(() => {
  'use strict';
  const root = document.querySelector('#rankings');
  if (!root) return;
  const $ = (selector) => root.querySelector(selector);
  let films = [];
  let latestSummary = null;
  let latestOutbound = null;
  const dayMs = 86400000;
  const futureSkewMs = 60000; // Permit small server/browser clock differences.
  const chinaDay = () => new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10);
  const shortDay = (day) => day.slice(5).replace('-', '.');
  const validDay = (day) => typeof day === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(day) && Number.isFinite(Date.parse(day)) && new Date(day).toISOString().slice(0, 10) === day;

  function renderList(board, entries) {
    const list = $(board + ' .ranking-list');
    const focusedId = list.contains(document.activeElement) ? document.activeElement.dataset.rankingFilm : null;
    const existing = new Map([...list.children].map((item) => [item.querySelector('[data-ranking-film]').dataset.rankingFilm, item]));
    list.replaceChildren(...entries.slice(0, 5).map(({ film, label }, index) => {
      const previous = existing.get(film.id);
      if (previous) {
        previous.querySelector('.ranking-position').textContent = String(index + 1).padStart(2, '0');
        previous.querySelector('.ranking-film-info > span').textContent = label;
        return previous;
      }
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = film.link;
      link.dataset.rankingFilm = film.id;
      link.className = 'ranking-film';
      const rank = document.createElement('span');
      rank.className = 'ranking-position';
      rank.textContent = String(index + 1).padStart(2, '0');
      rank.setAttribute('aria-hidden', 'true');
      const image = document.createElement('img');
      image.src = film.image;
      image.alt = '';
      image.width = 64;
      image.height = 50;
      image.loading = 'lazy';
      const info = document.createElement('span');
      info.className = 'ranking-film-info';
      const title = document.createElement('strong');
      title.textContent = film.title;
      const meta = document.createElement('span');
      meta.textContent = label;
      info.append(title, meta);
      link.append(rank, image, info);
      item.append(link);
      return item;
    }));
    if (focusedId) {
      const next = [...list.querySelectorAll('[data-ranking-film]')].find((link) => link.dataset.rankingFilm === focusedId);
      (next || $('#rankingsTitle')).focus({ preventScroll: true });
    }
  }

  function renderDaily() {
    const today = chinaDay();
    const entries = films.filter((film) => validDay(film.date) && film.date <= today).sort((a, b) => b.date.localeCompare(a.date) || a.index - b.index);
    const count = entries.filter((film) => film.date === today).length;
    $('#dailyRankingStatus').textContent = count ? '今日新收录 ' + count + ' 部' : entries.length ? '今日暂无新收录 · 最近收录 ' + shortDay(entries[0].date) : '作品核实后会出现在这里。';
    renderList('#rankingDaily', entries.map((film) => ({ film, label: shortDay(film.date) + ' 收录 · ' + film.runtime })));
  }

  function renderPopular(data) {
    if (!data?.available) {
      $('#popularRankingStatus').textContent = data?.configured ? '共享跳转统计暂不可用，连接后恢复榜单。' : '共享跳转统计尚未配置，暂不能显示热门排名。';
      renderList('#rankingPopular', []);
      return;
    }
    const today = chinaDay();
    const start = new Date(Date.parse(today) - 9 * dayMs).toISOString().slice(0, 10);
    const seen = new Set();
    const updated = Date.parse(data.updatedAt);
    const valid = data.metric === 'outbound-clicks' && data.windowStart === start && data.windowEnd === today && Number.isFinite(updated) && updated <= Date.now() + futureSkewMs && Date.now() - updated < dayMs && Array.isArray(data.films) && data.films.every((entry) => {
      if (!entry || typeof entry.filmId !== 'string' || seen.has(entry.filmId) || !Number.isSafeInteger(entry.outboundClicks) || entry.outboundClicks < 0) return false;
      seen.add(entry.filmId);
      return true;
    });
    if (!valid) {
      $('#popularRankingStatus').textContent = '当前统计数据暂不可用，更新后恢复榜单。';
      renderList('#rankingPopular', []);
      return;
    }
    const counts = new Map(data.films.map((entry) => [entry.filmId, entry.outboundClicks]));
    const entries = films.filter((film) => (counts.get(film.id) || 0) > 0).sort((a, b) => counts.get(b.id) - counts.get(a.id) || a.index - b.index);
    $('#popularRankingStatus').textContent = shortDay(start) + '–' + shortDay(today) + (entries.length ? ' · 本站原作跳转' : ' · 暂无原作跳转，观看后更新');
    renderList('#rankingPopular', entries.map((film) => ({ film, label: counts.get(film.id).toLocaleString('zh-CN') + ' 次原作跳转' })));
  }

  window.addEventListener('framepick:catalogue-ready', () => {
    films = [...document.querySelectorAll('#filmGrid [data-film]')].map((card, index) => ({
      id: card.dataset.film, date: card.dataset.date, index,
      title: card.querySelector('h3').textContent.trim(), image: card.querySelector('img').src,
      link: card.querySelector('.watch').href, runtime: card.querySelector('.card-runtime')?.textContent.trim() || '时长待核实'
    }));
    renderDaily();
    renderPopular(latestOutbound);
    if (latestSummary) renderAcclaimed(latestSummary);
  });

  function renderAcclaimed(detail) {
    const summaries = new Map((detail.films || []).map((entry) => [entry.filmId, entry]));
    const entries = detail.available ? films.map((film) => ({ film, summary: summaries.get(film.id) })).filter(({ summary }) => Number.isFinite(summary?.averageRating) && summary.averageRating >= 8 && summary.averageRating <= 10 && Number.isInteger(summary.ratingCount) && summary.ratingCount >= 5) : [];
    const weighted = ({ summary }) => (summary.averageRating * summary.ratingCount + 7 * 20) / (summary.ratingCount + 20);
    entries.sort((a, b) => weighted(b) - weighted(a) || b.summary.ratingCount - a.summary.ratingCount || a.film.index - b.film.index);
    $('#acclaimedRankingStatus').textContent = !detail.available ? '共享评价暂不可用，连接后更新口碑榜。' : entries.length ? '站内口碑 · 随评价更新' : '暂未有作品达到入榜门槛，评分积累后自动更新。';
    renderList('#rankingAcclaimed', entries.map(({ film, summary }) => ({ film, label: summary.averageRating.toFixed(1) + ' / 10 · ' + summary.ratingCount + ' 人评分' })));
  }
  window.addEventListener('framepick:review-summary', ({ detail }) => {
    latestSummary = detail;
    renderAcclaimed(detail);
  });
  window.addEventListener('framepick:outbound-summary', ({ detail }) => {
    latestOutbound = detail;
    renderPopular(detail);
  });

  root.addEventListener('click', (event) => {
    const link = event.target.closest('[data-ranking-film]');
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button > 0) return;
    event.preventDefault();
    window.dispatchEvent(new CustomEvent('framepick:request-film', { detail: { id: link.dataset.rankingFilm, trigger: link } }));
  });
  // Refresh calendar-bound lists after a background tab passes midnight.
  document.addEventListener('visibilitychange', () => { if (!document.hidden && films.length) { renderDaily(); renderPopular(latestOutbound); } });
})();
