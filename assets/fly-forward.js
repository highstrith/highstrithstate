/* Scroll-driven helix of the site's own posters. Native CSS perspective. */
(() => {
  'use strict';
  const section = document.getElementById('flyWorks');
  const field = document.getElementById('flyField');
  const stage = document.getElementById('flyStage');
  if (!section || !field || !stage) return;
  const motion = matchMedia('(min-width: 801px) and (prefers-reduced-motion: no-preference)');
  const clamp = value => Math.max(0, Math.min(1, value));
  const smooth = (start, end, value) => {
    const t = clamp((value - start) / (end - start));
    return t * t * (3 - 2 * t);
  };
  let cards = [], sources = [], frame = 0, current = null, previousTime = 0;
  let visible = false, imagesLoaded = false;

  function translate() {
    const english = document.documentElement.lang === 'en';
    document.getElementById('flyTitle').textContent = english ? 'Selected films' : '精选放映';
    section.querySelector('.fly-hint').textContent = english
      ? 'Stories, characters and imagination meet.' : '故事、角色与想象，在此交汇。';
    section.querySelector('.fly-more').textContent = english ? 'Browse all works' : '查看全部作品';
    section.querySelector('.fly-scroll-note').textContent = english ? 'Scroll to explore' : '滚动探索';
    cards.forEach((card, index) => {
      card.querySelector('.fly-title').textContent = sources[index].querySelector('.work-title').textContent;
    });
  }

  function loadImages() {
    if (imagesLoaded || !cards.length) return;
    imagesLoaded = true;
    cards.forEach((card, index) => {
      const source = sources[index].querySelector('img');
      const small = (source.srcset || '').split(',').map(part => part.trim().split(/\s+/))
        .find(([, width]) => parseInt(width, 10) >= 480);
      card.querySelector('img').src = small?.[0] || source.src;
    });
  }

  function build() {
    if (cards.length) return;
    // The normalized catalogue owns the images, order and translations.
    sources = [...document.querySelectorAll('#worksGrid .work-card')].slice(0, 20);
    if (!sources.length) return;
    cards = sources.map(() => {
      const card = document.createElement('a');
      card.className = 'fly-card';
      card.href = '#works';
      const image = document.createElement('img');
      image.alt = '';
      image.width = 480;
      image.height = 270;
      image.decoding = 'async';
      image.loading = 'lazy';
      const title = document.createElement('span');
      title.className = 'fly-title';
      card.append(image, title);
      return card;
    });
    field.replaceChildren(...cards);
    translate();
    configure();
    if (visible) loadImages();
  }

  function schedule() {
    if (!frame && motion.matches && visible && !document.hidden && cards.length) {
      frame = requestAnimationFrame(render);
    }
  }

  function render(time) {
    frame = 0;
    if (!motion.matches || !visible || document.hidden) return;
    const rect = section.getBoundingClientRect();
    const target = clamp(-rect.top / Math.max(1, rect.height - stage.clientHeight));
    const delta = previousTime ? Math.min(64, time - previousTime) : 16.7;
    previousTime = time;
    current = current === null ? target : current + (target - current) * (1 - Math.exp(-delta / 75));
    if (Math.abs(target - current) < .00002) current = target;
    const turn = current * 1.9;
    const travel = current * cards.length * 320;
    const radiusX = Math.min(stage.clientWidth * .65, 1100);
    const radiusY = Math.max(stage.clientHeight * .72, 480);
    cards.forEach((card, index) => {
      const baseAngle = index * .83 - .6;
      const angle = baseAngle + turn;
      const depth = -800 - index * 320 + travel;
      const opacity = smooth(-4800, -2800, depth) * (1 - smooth(60, 420, depth));
      card.style.visibility = opacity > .003 ? 'visible' : 'hidden';
      card.style.opacity = opacity.toFixed(3);
      // Rotate both XY position and plane orientation: a spiral, not a zoom.
      card.style.transform = `translate3d(${(Math.cos(angle) * radiusX).toFixed(2)}px, ${(Math.sin(angle) * radiusY).toFixed(2)}px, ${depth.toFixed(2)}px) rotateZ(${(Math.sin(baseAngle * 1.7) * 12 + turn * 180 / Math.PI).toFixed(2)}deg) rotateY(${(-Math.cos(angle) * 16).toFixed(2)}deg) rotateX(${(Math.sin(angle) * 10).toFixed(2)}deg)`;
      card.style.zIndex = String(cards.length - index);
    });
    document.getElementById('flyBar').style.transform = `scaleX(${current})`;
    if (current !== target) schedule();
  }

  function configure() {
    cancelAnimationFrame(frame);
    frame = 0;
    current = null;
    previousTime = 0;
    const active = motion.matches && cards.length > 0;
    section.classList.toggle('fly-motion', active);
    if (active) field.setAttribute('aria-hidden', 'true');
    else field.removeAttribute('aria-hidden');
    cards.forEach(card => {
      card.removeAttribute('style');
      card.tabIndex = active ? -1 : 0;
    });
    // Do not inherit either mobile scrolling or a transformed scroll anchor.
    field.scrollTo({ left: 0, top: 0, behavior: 'instant' });
    schedule();
  }

  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (visible) { loadImages(); schedule(); }
    else { cancelAnimationFrame(frame); frame = 0; current = null; previousTime = 0; }
  }, { rootMargin: '60% 0px' }).observe(section);
  new ResizeObserver(() => { current = null; schedule(); }).observe(stage);
  new MutationObserver(translate).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  motion.addEventListener('change', configure);
  addEventListener('scroll', schedule, { passive: true });
  addEventListener('catalogue:ready', build);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { cancelAnimationFrame(frame); frame = 0; previousTime = 0; }
    else schedule();
  });
  build();
})();
