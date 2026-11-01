/* One small CSS loop, with eight semantic originals and one hidden visual repeat. */
(() => {
  'use strict';
  const ribbon = document.getElementById('softwareRibbon');
  const viewport = document.getElementById('softwareLogoWindow');
  const track = document.getElementById('softwareLogoTrack');
  const group = document.getElementById('softwareLogoSet');
  const toggle = document.getElementById('softwareRibbonToggle');
  if (!ribbon || !viewport || !track || !group || !toggle) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  let copy = null, visible = false, hovered = false, paused = false;

  function labels() {
    const en = document.documentElement.lang === 'en';
    toggle.setAttribute('aria-label', en
      ? (paused ? 'Resume software logo scrolling' : 'Pause software logo scrolling')
      : (paused ? '继续软件图标滚动' : '暂停软件图标滚动'));
    toggle.setAttribute('aria-pressed', String(paused));
  }
  function sync() {
    ribbon.dataset.running = String(!reduce.matches && visible && !paused && !hovered
      && !viewport.contains(document.activeElement) && !document.hidden && !document.querySelector('dialog[open]'));
  }
  function repeat() {
    copy?.remove();
    copy = null;
    if (reduce.matches) return;
    copy = group.cloneNode(true);
    copy.removeAttribute('id');
    copy.dataset.softwareCopy = '';
    copy.setAttribute('aria-hidden', 'true');
    copy.querySelectorAll('[data-software]').forEach(item => item.removeAttribute('data-software'));
    track.append(copy);
  }
  function measure() {
    ribbon.style.setProperty('--software-window-width', `${viewport.clientWidth}px`);
    ribbon.style.setProperty('--software-period', `${group.offsetWidth}px`);
    ribbon.style.setProperty('--software-duration', `${group.offsetWidth / 16}s`);
  }
  function configure() {
    viewport.classList.toggle('is-looping', !reduce.matches);
    viewport.scrollLeft = 0;
    toggle.hidden = reduce.matches;
    repeat(); measure(); labels(); sync();
  }
  toggle.addEventListener('click', () => { paused = !paused; labels(); sync(); });
  viewport.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') { hovered = true; sync(); } });
  viewport.addEventListener('pointerleave', () => { hovered = false; sync(); });
  viewport.addEventListener('focusin', sync);
  viewport.addEventListener('focusout', () => queueMicrotask(sync));
  document.addEventListener('visibilitychange', sync);
  new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); }).observe(ribbon);
  new ResizeObserver(measure).observe(viewport);
  const modal = new MutationObserver(sync);
  document.querySelectorAll('dialog').forEach(dialog => modal.observe(dialog, { attributes: true, attributeFilter: ['open'] }));
  new MutationObserver(() => { repeat(); labels(); measure(); sync(); }).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  reduce.addEventListener('change', configure);
  configure();
})();
