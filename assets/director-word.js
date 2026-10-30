/* A local, original adaptation of proximity-responsive elastic typography. */
(() => {
  'use strict';
  const heading = document.getElementById('toolsTitle');
  if (!heading) return;
  const surface = heading.closest('.tools-preview-copy');
  const media = matchMedia('(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)');
  const ns = 'http://www.w3.org/2000/svg';
  const filters = document.createElementNS(ns, 'svg');
  filters.id = 'directorWordFilters';
  filters.setAttribute('width', '0');
  filters.setAttribute('height', '0');
  filters.style.position = 'absolute';
  filters.setAttribute('aria-hidden', 'true');
  filters.setAttribute('focusable', 'false');
  heading.after(filters);
  let letters = [], frame = 0, lastTime = 0, energy = 0, previous = null;
  const observer = new MutationObserver(build);

  function reset() {
    cancelAnimationFrame(frame); frame = 0; lastTime = 0; energy = 0; previous = null;
    letters.forEach(letter => {
      letter.current = letter.target = 0;
      letter.node.removeAttribute('style');
      letter.map.setAttribute('scale', '0');
    });
  }

  function build() {
    observer.disconnect();
    reset();
    const text = heading.textContent;
    heading.setAttribute('aria-label', text);
    const content = document.createDocumentFragment();
    filters.replaceChildren();
    letters = [];
    text.split(/(\s+)/).forEach(word => {
      if (!word.trim()) { content.append(document.createTextNode(word)); return; }
      const chunk = document.createElement('span');
      chunk.className = 'director-word-chunk';
      chunk.setAttribute('aria-hidden', 'true');
      [...word].forEach(character => {
        const node = document.createElement('span');
        node.className = 'director-letter';
        node.textContent = character;
        const filter = document.createElementNS(ns, 'filter');
        filter.id = `director-word-warp-${letters.length}`;
        for (const [key, value] of Object.entries({x:'-20%',y:'-20%',width:'140%',height:'140%'})) filter.setAttribute(key, value);
        const noise = document.createElementNS(ns, 'feTurbulence');
        noise.setAttribute('type', 'fractalNoise');
        noise.setAttribute('baseFrequency', '.04 .08');
        noise.setAttribute('numOctaves', '1');
        noise.setAttribute('seed', String(letters.length + 1));
        noise.setAttribute('result', 'grain');
        const map = document.createElementNS(ns, 'feDisplacementMap');
        map.setAttribute('in', 'SourceGraphic'); map.setAttribute('in2', 'grain');
        map.setAttribute('scale', '0'); map.setAttribute('xChannelSelector', 'R'); map.setAttribute('yChannelSelector', 'G');
        filter.append(noise, map); filters.append(filter); chunk.append(node);
        letters.push({node, chunk, filter, map, current: 0, target: 0, side: 0});
      });
      content.append(chunk);
    });
    heading.replaceChildren(content);
    observer.observe(heading, {childList: true, subtree: true});
  }

  function schedule() { if (!frame && media.matches && !document.hidden) frame = requestAnimationFrame(render); }
  function render(now) {
    frame = 0;
    const dt = Math.min(50, lastTime ? now - lastTime : 16.7);
    lastTime = now;
    energy *= Math.exp(-dt / 100);
    let moving = energy > .002;
    letters.forEach(letter => {
      letter.current += (letter.target - letter.current) * (1 - Math.exp(-dt / 55));
      if (Math.abs(letter.current - letter.target) < .001) letter.current = letter.target;
      else moving = true;
      const value = letter.current;
      if (value < .001) { letter.node.removeAttribute('style'); letter.map.setAttribute('scale', '0'); return; }
      letter.node.style.transform = `translateY(${(-2 * value).toFixed(2)}px) scale(${(1 - .06 * value).toFixed(3)}, ${(1 + .18 * value).toFixed(3)}) skewX(${(-letter.side * 6 * value).toFixed(2)}deg)`;
      letter.node.style.setProperty('--director-accent', (value * 65).toFixed(1) + '%');
      const ripple = value * energy * 2.2;
      letter.map.setAttribute('scale', ripple.toFixed(2));
      if (ripple > .04) letter.node.style.filter = `url(#${letter.filter.id})`;
      else letter.node.style.removeProperty('filter');
    });
    if (moving) schedule(); else lastTime = 0;
  }

  surface.addEventListener('pointermove', event => {
    if (event.pointerType !== 'mouse' || !media.matches) return;
    const radius = 68;
    if (previous) energy = Math.min(1, energy + Math.hypot(event.clientX - previous.x, event.clientY - previous.y) / 70);
    else energy = .6;
    previous = {x: event.clientX, y: event.clientY};
    // Layout offsets ignore the letter transforms, keeping the field stable.
    const boxes = new Map();
    letters.forEach(letter => {
      if (!boxes.has(letter.chunk)) boxes.set(letter.chunk, letter.chunk.getBoundingClientRect());
      const box = boxes.get(letter.chunk);
      const dx = box.left + letter.node.offsetLeft + letter.node.offsetWidth / 2 - event.clientX;
      const dy = box.top + letter.node.offsetTop + letter.node.offsetHeight / 2 - event.clientY;
      letter.target = Math.exp(-(dx * dx + dy * dy) / (radius * radius));
      letter.side = Math.max(-1, Math.min(1, dx / radius));
    });
    schedule();
  }, {passive: true});
  surface.addEventListener('pointerleave', () => {
    letters.forEach(letter => { letter.target = 0; }); previous = null; schedule();
  });
  surface.addEventListener('pointercancel', reset);
  media.addEventListener('change', reset);
  addEventListener('blur', reset);
  addEventListener('resize', reset, {passive: true});
  addEventListener('scroll', reset, {passive: true});
  document.addEventListener('visibilitychange', reset);
  build();
})();
