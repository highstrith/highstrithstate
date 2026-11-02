(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const grid = $('#filmGrid');
  if (!grid) return;
  const filmDialog = $('#filmDialog');
  const membershipDialog = $('#membershipDialog');
  const cards = [...grid.querySelectorAll('[data-film]')];
  const films = cards.map((card, index) => {
    const raw = card.dataset.score.trim();
    const number = Number(raw);
    const score = raw !== '' && Number.isFinite(number) && number >= 0 && number <= 10 ? number : null;
    const text = (selector) => card.querySelector(selector)?.textContent.trim() || '';
    return {
      id: card.dataset.film, card, index, score,
      category: card.dataset.category, genres: card.dataset.genres.split(' '),
      source: card.dataset.source, access: card.dataset.access, date: card.dataset.date,
      title: text('h3'), author: text('.author-name'), kind: text('.kind'),
      description: text('.desc'), reason: text('.recommendation'), episode: text('.episode'),
      image: card.querySelector('img'), link: card.querySelector('.watch').href,
      search: card.textContent.toLocaleLowerCase()
    };
  });
  const byId = new Map(films.map((film) => [film.id, film]));
  const controls = {
    q: $('#filmSearch'), genre: $('#genreFilter'), source: $('#sourceFilter'),
    rating: $('#scoreFilter'), access: $('#accessFilter'), sort: $('#sortFilter')
  };
  const defaults = { q: '', category: 'all', genre: 'all', source: 'all', rating: 'all', access: 'all', sort: 'curated', saved: false };
  const categories = [...document.querySelectorAll('[data-category]')].filter((node) => node.tagName === 'BUTTON');
  const storageKey = 'framepick:saved:v1';
  let storageAvailable = true;
  let saved = new Set();
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey) || '[]');
    if (Array.isArray(parsed)) saved = new Set(parsed.filter((id) => typeof id === 'string' && byId.has(id)));
  } catch { storageAvailable = false; }
  let state = { ...defaults };
  let currentFilm = null;
  let opener = null;
  let noticeTimer;
  const defaultTitle = document.title;

  function notify(message) {
    $('#notice').textContent = message;
    $('#notice').classList.add('is-visible');
    clearTimeout(noticeTimer);
    noticeTimer = setTimeout(() => $('#notice').classList.remove('is-visible'), 2800);
  }

  function readState() {
    const params = new URL(location.href).searchParams;
    state = { ...defaults, q: (params.get('q') || '').slice(0, 100), saved: params.get('saved') === '1' };
    const category = params.get('category');
    if (categories.some((button) => button.dataset.category === category)) state.category = category;
    for (const key of ['genre', 'source', 'rating', 'access', 'sort']) {
      const value = params.get(key);
      if ([...controls[key].options].some((option) => option.value === value)) state[key] = value;
    }
  }

  function writeState() {
    const url = new URL(location.href);
    for (const key of Object.keys(defaults)) {
      const value = state[key];
      if (value === defaults[key]) url.searchParams.delete(key);
      else url.searchParams.set(key, key === 'saved' ? '1' : value);
    }
    try { history.replaceState(history.state, '', url); } catch { /* file viewers may restrict history */ }
  }

  function syncControls() {
    for (const [key, control] of Object.entries(controls)) control.value = state[key];
    for (const button of categories) button.setAttribute('aria-pressed', String(button.dataset.category === state.category));
    $('#savedToggle').setAttribute('aria-pressed', String(state.saved));
  }

  function syncSaved() {
    $('#savedCount').textContent = String(saved.size);
    for (const button of document.querySelectorAll('[data-save-film]')) {
      const film = byId.get(button.dataset.saveFilm);
      const active = saved.has(film.id);
      button.setAttribute('aria-pressed', String(active));
      button.setAttribute('aria-label', (active ? '取消收藏《' : '收藏《') + film.title + '》');
    }
    if (currentFilm) {
      const active = saved.has(currentFilm.id);
      $('#detailSave').setAttribute('aria-pressed', String(active));
      $('#detailSave').textContent = active ? '已收藏 · 取消' : '收藏作品';
    }
  }

  function render() {
    const query = state.q.trim().toLocaleLowerCase();
    const visible = films.filter((film) =>
      (!query || film.search.includes(query)) &&
      (state.category === 'all' || film.category === state.category) &&
      (state.genre === 'all' || film.genres.includes(state.genre)) &&
      (state.source === 'all' || film.source === state.source) &&
      (state.access === 'all' || film.access === state.access) &&
      (state.rating === 'all' || (film.score !== null && film.score >= Number(state.rating))) &&
      (!state.saved || saved.has(film.id))
    );
    if (state.sort === 'score') visible.sort((a, b) => (b.score ?? -1) - (a.score ?? -1) || a.index - b.index);
    if (state.sort === 'newest') visible.sort((a, b) => b.date.localeCompare(a.date) || a.index - b.index);
    const ids = new Set(visible.map((film) => film.id));
    for (const film of films) film.card.hidden = !ids.has(film.id);
    const ordered = [...visible, ...films.filter((film) => !ids.has(film.id))];
    ordered.forEach((film, index) => {
      if (grid.children[index] !== film.card) grid.insertBefore(film.card, grid.children[index] || null);
    });
    $('#resultCount').textContent = visible.length + ' 部' + (state.saved ? '已收藏作品' : '精选作品');
    $('#emptyState').hidden = visible.length !== 0;
    $('#emptyMembership').hidden = state.access !== 'vip';
    let title = '暂时没有匹配的作品';
    let copy = '试试其他题材，或清除筛选条件。';
    if (state.access === 'vip') {
      title = 'VIP 片库正在筹备';
      copy = '订阅尚未开放，先从免费精选里发现好作品。';
    } else if (state.saved && saved.size === 0) {
      title = '还没有收藏的作品';
      copy = '点击作品上的收藏按钮，把想看的好片留在这台设备。';
    } else if (state.rating !== 'all' && films.every((film) => film.score === null)) {
      title = '正式评分还在补充';
      copy = '当前作品均为待评，完成审核后才会进入评分筛选。';
    } else if (state.source !== 'all' && !films.some((film) => film.source === state.source)) {
      title = '这个来源还没有公开收录';
      copy = '作品核实后会补充到片库，也可以先看看其他来源。';
    }
    $('#emptyTitle').textContent = title;
    $('#emptyCopy').textContent = copy;
    syncSaved();
  }

  function applyFilters() { syncControls(); render(); writeState(); }

  function resetFilters(access = 'all') {
    state = { ...defaults, access };
    applyFilters();
  }

  function toggleSave(id) {
    const focusedCard = document.activeElement?.closest('#filmGrid [data-film]');
    if (saved.has(id)) saved.delete(id); else saved.add(id);
    if (storageAvailable) {
      try { localStorage.setItem(storageKey, JSON.stringify([...saved])); }
      catch { storageAvailable = false; }
    }
    render();
    if (focusedCard?.hidden) {
      const next = grid.querySelector('[data-film]:not([hidden]) [data-save-film]') || $('#resetFilters');
      next.focus({ preventScroll: true });
    }
    notify(storageAvailable ? (saved.has(id) ? '已收藏，保存在此浏览器' : '已取消收藏') : '收藏仅在本次浏览中保留');
  }

  function syncDialogBody() {
    document.body.classList.toggle('has-dialog', filmDialog.open || membershipDialog.open);
  }

  function closeFilmUI() {
    if (!filmDialog.open) return;
    currentFilm = null;
    filmDialog.close();
    document.title = defaultTitle;
    syncDialogBody();
    const target = opener?.isConnected && !opener.closest('[hidden]') ? opener : $('#entriesTitle');
    target.focus({ preventScroll: true });
  }

  function openFilm(id, push = false, trigger = null) {
    const film = byId.get(id);
    if (!film) return;
    currentFilm = film;
    if (trigger) opener = trigger;
    $('#detailTitle').textContent = film.title;
    $('#detailKind').textContent = film.kind + ' / 系列短剧';
    $('#detailAuthor').textContent = film.author + ' / 抖音';
    $('#detailEpisode').textContent = film.episode;
    $('#detailDescription').textContent = film.description;
    $('#detailReason').textContent = film.reason;
    $('#detailImage').src = film.image.src;
    $('#detailImage').alt = film.image.alt;
    $('#detailWatch').href = film.link;
    $('#detailScore').textContent = film.score === null ? '编辑评分：待评。完成审核后公开，不计入评分榜单。' : '编辑评分：' + film.score.toFixed(1) + ' / 10';
    syncSaved();
    if (push) {
      const url = new URL(location.href);
      url.searchParams.set('film', id);
      try { history.pushState({ framepickFilm: true }, '', url); } catch { /* details still work without URL history */ }
    }
    if (!filmDialog.open) filmDialog.showModal();
    document.title = film.title + ' — ' + defaultTitle;
    syncDialogBody();
  }

  function requestCloseFilm() {
    if (history.state?.framepickFilm && new URL(location.href).searchParams.has('film')) {
      history.back();
    } else {
      const url = new URL(location.href);
      url.searchParams.delete('film');
      try { history.replaceState({}, '', url); } catch { /* file viewers may restrict history */ }
      closeFilmUI();
    }
  }

  function syncFromURL() {
    readState();
    syncControls();
    render();
    const id = new URL(location.href).searchParams.get('film');
    if (byId.has(id)) openFilm(id); else closeFilmUI();
  }

  for (const [key, control] of Object.entries(controls)) {
    control.addEventListener(key === 'q' ? 'input' : 'change', () => {
      state[key] = control.value;
      applyFilters();
    });
  }
  for (const button of categories) button.addEventListener('click', () => {
    state.category = button.dataset.category;
    applyFilters();
  });
  $('#savedToggle').addEventListener('click', () => {
    state.saved = !state.saved;
    applyFilters();
    $('#entries').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  });
  $('#resetFilters').addEventListener('click', () => {
    resetFilters();
    $('#filmSearch').focus({ preventScroll: true });
  });
  for (const trigger of document.querySelectorAll('[data-open-film]')) {
    trigger.addEventListener('click', (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button > 0) return;
      event.preventDefault();
      openFilm(trigger.dataset.openFilm, true, trigger);
    });
  }
  for (const button of document.querySelectorAll('[data-save-film]')) button.addEventListener('click', () => toggleSave(button.dataset.saveFilm));
  $('#detailSave').addEventListener('click', () => { if (currentFilm) toggleSave(currentFilm.id); });
  $('[data-close-film]').addEventListener('click', requestCloseFilm);
  filmDialog.addEventListener('cancel', (event) => { event.preventDefault(); requestCloseFilm(); });
  filmDialog.addEventListener('click', (event) => { if (event.target === filmDialog) {
    const rect = filmDialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) requestCloseFilm();
  } });
  for (const button of document.querySelectorAll('[data-membership]')) button.addEventListener('click', () => { membershipDialog.showModal(); syncDialogBody(); });
  $('[data-close-membership]').addEventListener('click', () => membershipDialog.close());
  membershipDialog.addEventListener('close', syncDialogBody);
  membershipDialog.addEventListener('click', (event) => { if (event.target === membershipDialog) {
    const rect = membershipDialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) membershipDialog.close();
  } });
  $('#browseFree').addEventListener('click', () => resetFilters('free'));
  $('#memberBrowse').addEventListener('click', () => { membershipDialog.close(); resetFilters('free'); });
  window.addEventListener('popstate', syncFromURL);
  for (const film of films) if (film.score !== null) {
    film.card.querySelector('.score').textContent = film.score.toFixed(1);
    film.card.querySelector('.score').setAttribute('aria-label', '编辑评分：' + film.score.toFixed(1) + '分');
  }
  document.documentElement.classList.add('js');
  syncFromURL();
})();
