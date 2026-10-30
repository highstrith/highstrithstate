/* A compact, rightward loop of the film's real production images. */
(() => {
  'use strict';
  const strip = document.getElementById('homeProgressStrip');
  const track = document.getElementById('homeProgressTrack');
  const group = strip?.querySelector('.home-progress-grid');
  if (!group || !track) return;
  const { gsap } = window;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const toggle = document.getElementById('productionStripToggle');
  const previous = document.getElementById('productionStripPrevious');
  const next = document.getElementById('productionStripNext');
  const links = [...group.querySelectorAll('a')];
  let loop, copy, width = 0, hovered = false, userPaused = false, nearViewport = false;
  let drag = null, suppressClickUntil = 0;
  let ready = !!document.querySelector('.work-card');

  function labels() {
    const en = document.documentElement.lang === 'en';
    strip.setAttribute('aria-label', en ? 'Production images' : '制作截图');
    previous.textContent = en ? 'Previous image' : '上一张';
    next.textContent = en ? 'Next image' : '下一张';
    toggle.textContent = en ? (userPaused ? 'Resume scrolling' : 'Pause scrolling') : (userPaused ? '继续滚动' : '暂停滚动');
    toggle.setAttribute('aria-pressed', String(userPaused));
    toggle.hidden = !loop;
  }
  function sync() {
    loop?.paused(userPaused || hovered || !!drag || strip.contains(document.activeElement)
      || document.hidden || !nearViewport || !!document.querySelector('dialog[open]'));
  }
  function loadThumbs() {
    if (!nearViewport || !ready) return;
    strip.querySelectorAll('img').forEach(image => { image.loading = 'eager'; });
  }
  function reveal(link) {
    if (!loop || !group.contains(link)) return;
    strip.scrollLeft = 0;
    const frame = strip.getBoundingClientRect();
    const rect = link.getBoundingClientRect();
    if (rect.left < frame.left || rect.right > frame.right) {
      const offset = link.offsetLeft - links[0].offsetLeft;
      loop.progress(1 - offset / width);
    }
  }
  function build() {
    const progress = loop?.progress() || 0;
    loop?.kill();
    loop = null;
    copy?.remove();
    strip.classList.remove('is-looping');
    gsap?.set(track, { clearProps: 'transform' });
    if (gsap && !reduce.matches) {
      copy = group.cloneNode(true);
      copy.className = 'production-strip-copy';
      copy.dataset.stripCopy = '';
      copy.setAttribute('aria-hidden', 'true');
      copy.querySelectorAll('a').forEach(link => { link.tabIndex = -1; });
      copy.querySelectorAll('noscript').forEach(node => node.remove());
      track.append(copy);
      width = group.getBoundingClientRect().width;
      strip.scrollLeft = 0;
      strip.classList.add('is-looping');
      // Each group includes its final gap, so the repeat joins identical frames.
      loop = gsap.fromTo(track, { x: -width }, {
        x: 0, duration: width / 34, repeat: -1, ease: 'none', paused: true,
      }).progress(progress);
      reveal(document.activeElement);
      loadThumbs();
    }
    if (!loop && group.contains(document.activeElement)) {
      strip.scrollLeft = document.activeElement.offsetLeft - links[0].offsetLeft;
    }
    labels();
    sync();
  }
  function seek(x) {
    const wrapped = ((x % width) + width) % width - width;
    loop.progress((wrapped + width) / width);
  }
  function step(direction) {
    if (!loop) {
      strip.scrollBy({ left: direction * (links[1].offsetLeft - links[0].offsetLeft), behavior: reduce.matches ? 'instant' : 'smooth' });
      return;
    }
    userPaused = true;
    const stride = links[1].offsetLeft - links[0].offsetLeft;
    const left = (-gsap.getProperty(track, 'x') % width + width) % width;
    const index = (Math.round(left / stride) + direction + links.length) % links.length;
    loop.progress(1 - (links[index].offsetLeft - links[0].offsetLeft) / width);
    labels();
    sync();
  }

  toggle.addEventListener('click', () => { userPaused = !userPaused; labels(); sync(); });
  previous.addEventListener('click', () => step(-1));
  next.addEventListener('click', () => step(1));
  strip.addEventListener('pointerenter', event => { if (event.pointerType !== 'touch') { hovered = true; sync(); } });
  strip.addEventListener('pointerleave', () => { hovered = false; sync(); });
  strip.addEventListener('focusin', event => { reveal(event.target); sync(); });
  strip.addEventListener('focusout', () => queueMicrotask(sync));
  strip.addEventListener('keydown', event => {
    if (event.target !== strip || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    step(event.key === 'ArrowRight' ? 1 : -1);
  });
  strip.addEventListener('wheel', event => {
    if (!loop || Math.abs(event.deltaX) <= Math.abs(event.deltaY)) return;
    event.preventDefault();
    userPaused = true;
    seek(gsap.getProperty(track, 'x') - event.deltaX);
    labels();
    sync();
  }, { passive: false });
  strip.addEventListener('pointerdown', event => {
    if (!loop || event.pointerType !== 'touch') return;
    drag = { start: event.clientX, x: gsap.getProperty(track, 'x'), moved: false };
    sync();
  });
  strip.addEventListener('pointermove', event => {
    if (!drag) return;
    const distance = event.clientX - drag.start;
    if (!drag.moved && Math.abs(distance) < 7) return;
    drag.moved = true;
    userPaused = true;
    strip.setPointerCapture(event.pointerId);
    if (event.cancelable) event.preventDefault();
    seek(drag.x + distance);
    labels();
  });
  const release = () => {
    if (drag?.moved) suppressClickUntil = performance.now() + 350;
    drag = null;
    sync();
  };
  strip.addEventListener('pointerup', release);
  strip.addEventListener('pointercancel', release);
  strip.addEventListener('click', event => {
    if (performance.now() < suppressClickUntil) { event.preventDefault(); event.stopImmediatePropagation(); }
  }, true);
  new IntersectionObserver(entries => {
    nearViewport = entries[0].isIntersecting;
    loadThumbs();
    sync();
  }, { rootMargin: '120px' }).observe(strip);
  new ResizeObserver(() => {
    if (loop && Math.abs(group.getBoundingClientRect().width - width) > 1) build();
  }).observe(group);
  const dialogs = new MutationObserver(sync);
  document.querySelectorAll('dialog').forEach(dialog => dialogs.observe(dialog, { attributes: true, attributeFilter: ['open'] }));
  new MutationObserver(labels).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  reduce.addEventListener('change', build);
  document.addEventListener('visibilitychange', sync);
  window.addEventListener('pagehide', () => loop?.pause());
  window.addEventListener('pageshow', sync);
  window.addEventListener('catalogue:ready', () => { ready = true; loadThumbs(); });
  strip.parentElement.querySelector('.production-strip-controls').hidden = false;
  build();
})();
