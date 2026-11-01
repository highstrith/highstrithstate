/* Keep the eight original viewer buttons; repeat only visual copies for the loop. */
(() => {
  'use strict';
  const grid = document.getElementById('stillsGrid');
  const controls = document.getElementById('stillsTickerControls');
  const toggle = document.getElementById('stillsTickerToggle');
  const hint = document.getElementById('stillsTickerHint');
  if (!grid || !controls || !toggle || !window.gsap) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  let order = [], rows = [], paused = false, hovered = false, visible = false, builtWidth = 0;

  function labels() {
    const en = document.documentElement.lang === 'en';
    toggle.textContent = en ? (paused ? 'Resume motion' : 'Pause motion') : (paused ? '继续动效' : '暂停动效');
    toggle.setAttribute('aria-pressed', String(paused));
    hint.textContent = en ? '8 stills · Hover to pause, select to view in full' : '8 张画面 · 悬停暂停，点击查看完整画面';
  }
  function sync() {
    const hold = paused || hovered || grid.contains(document.activeElement) || document.hidden
      || !visible || !!document.querySelector('dialog[open]');
    rows.forEach(row => row.loop.paused(hold));
  }
  function echo(figure) {
    const copy = figure.cloneNode(true);
    copy.className = 'ticker-echo';
    copy.removeAttribute('data-reveal');
    copy.removeAttribute('style');
    copy.setAttribute('aria-hidden', 'true');
    const button = copy.querySelector('button');
    const id = button.dataset.still ?? button.dataset.tickerEcho;
    button.removeAttribute('data-still');
    button.dataset.tickerEcho = id;
    button.className = 'ticker-echo-media';
    button.tabIndex = -1;
    button.addEventListener('pointerdown', event => { if (event.pointerType === 'mouse') event.preventDefault(); });
    button.addEventListener('click', () => grid.querySelector(`[data-still="${id}"]`)?.click());
    return copy;
  }
  function build() {
    const figures = [...grid.querySelectorAll('.still-card')];
    if (!figures.length) return;
    const focused = grid.contains(document.activeElement) ? document.activeElement : null;
    rows.forEach(row => row.loop.kill());
    rows = [];
    figures.sort((a, b) => Number(a.querySelector('[data-still]').dataset.still) - Number(b.querySelector('[data-still]').dataset.still));
    grid.classList.remove('ticker-ready');
    grid.replaceChildren(...figures);
    controls.hidden = reduce.matches;
    if (reduce.matches) {
      builtWidth = grid.clientWidth;
      focused?.focus({ preventScroll: true });
      focused?.scrollIntoView({ behavior: 'instant', block: 'nearest', inline: 'nearest' });
      return;
    }
    if (order.length !== figures.length) {
      order = figures.map((_, index) => index);
      for (let i = order.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [order[i], order[j]] = [order[j], order[i]];
      }
    }
    const plane = document.createElement('div');
    plane.className = 'still-ticker-plane';
    grid.replaceChildren(plane);
    grid.classList.add('ticker-ready');
    const size = Math.ceil(figures.length / 3);
    for (let index = 0; index < 3; index++) {
      const originals = order.slice(index * size, (index + 1) * size).map(i => figures[i]);
      if (!originals.length) continue;
      const row = document.createElement('div');
      row.className = 'still-ticker-row';
      const track = document.createElement('div');
      track.className = 'still-ticker-track';
      const set = document.createElement('div');
      set.className = 'still-ticker-set';
      originals.forEach(figure => {
        figure.removeAttribute('data-reveal');
        set.append(figure);
      });
      track.append(set); row.append(track); plane.append(row);
      // A period is wider than the viewport, even for the two-image last row.
      const minimum = grid.clientWidth + 2 * originals[0].offsetWidth;
      while (set.offsetWidth < minimum) originals.forEach(figure => set.append(echo(figure)));
      const repeat = document.createElement('div');
      repeat.className = 'still-ticker-set';
      [...set.children].forEach(figure => repeat.append(echo(figure)));
      track.append(repeat);
      const width = set.offsetWidth;
      const reverse = index === 1;
      const loop = gsap.fromTo(track, { x: reverse ? -width : 0 }, {
        x: reverse ? 0 : -width, duration: width / (index === 1 ? 28 : 34),
        repeat: -1, ease: 'none', paused: true,
      });
      rows.push({ row, loop, width, reverse });
    }
    builtWidth = grid.clientWidth;
    focused?.focus({ preventScroll: true });
    labels(); sync();
  }
  function reveal(target) {
    const button = target.closest?.('[data-still]');
    if (!button) return;
    const state = rows.find(item => item.row.contains(button));
    if (!state) return;
    const figure = button.closest('.still-card');
    const padding = parseFloat(getComputedStyle(grid.querySelector('.still-ticker-plane')).paddingLeft);
    const shift = Math.min(state.width, Math.max(0, figure.offsetLeft + padding - (grid.clientWidth - figure.offsetWidth) / 2));
    state.loop.progress(state.reverse ? 1 - shift / state.width : shift / state.width);
  }
  toggle.addEventListener('click', () => { paused = !paused; labels(); sync(); });
  grid.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') { hovered = true; sync(); } });
  grid.addEventListener('pointerleave', () => { hovered = false; sync(); });
  grid.addEventListener('focusin', event => {
    // Mouse/touch focus must not move a card between pointerdown and click.
    if (event.target.matches(':focus-visible')) reveal(event.target);
    sync();
  });
  grid.addEventListener('focusout', () => queueMicrotask(sync));
  document.addEventListener('visibilitychange', sync);
  new IntersectionObserver(entries => { visible = entries[0].isIntersecting; sync(); }).observe(grid);
  const modal = new MutationObserver(sync);
  document.querySelectorAll('dialog').forEach(dialog => modal.observe(dialog, { attributes: true, attributeFilter: ['open'] }));
  new ResizeObserver(() => { if (Math.abs(grid.clientWidth - builtWidth) > 1) build(); }).observe(grid);
  new MutationObserver(labels).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  reduce.addEventListener('change', build);
  window.addEventListener('stills:ready', build);
  labels(); build();
})();
