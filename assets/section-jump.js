/* Reuse site-shell's bounded anchor scrolling; keep this index independent. */
(() => {
  'use strict';
  const jump = document.getElementById('sectionJump');
  if (!jump) return;
  const toggle = jump.querySelector('summary');
  const nav = jump.querySelector('nav');
  const links = [...jump.querySelectorAll('[data-jump-section]')];
  const sections = links.map(link => document.getElementById(link.hash.slice(1)));
  let frame = 0;

  function labels() {
    const en = document.documentElement.lang === 'en';
    jump.querySelectorAll('[data-jump-cn]').forEach(node => {
      node.textContent = en ? node.dataset.jumpEn : node.dataset.jumpCn;
    });
    const label = en ? 'Chapter navigation' : '区块导航';
    nav.setAttribute('aria-label', label);
    toggle.setAttribute('aria-label', en
      ? (jump.open ? 'Close chapter navigation' : 'Open chapter navigation')
      : (jump.open ? '收起区块导航' : '展开区块导航'));
    toggle.setAttribute('aria-expanded', String(jump.open));
  }

  function close(returnFocus = false) {
    jump.open = false;
    if (returnFocus) toggle.focus({ preventScroll: true });
  }

  jump.addEventListener('toggle', labels);
  jump.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (link && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) close();
    // The click bubbles to site-shell, which moves focus and updates the hash.
  });
  document.addEventListener('click', event => { if (!jump.contains(event.target)) close(); });
  jump.addEventListener('keydown', event => {
    if (event.key === 'Escape' && jump.open) {
      event.preventDefault();
      close(true);
    }
  });
  jump.addEventListener('focusout', () => {
    requestAnimationFrame(() => { if (!jump.contains(document.activeElement)) close(); });
  });

  function current() {
    frame = 0;
    const guide = Math.min(200, innerHeight * .3);
    let active = -1;
    sections.forEach((section, index) => {
      if (section && section.getBoundingClientRect().top <= guide) active = index;
    });
    links.forEach((link, index) => {
      if (index === active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }
  function schedule() { if (!frame) frame = requestAnimationFrame(current); }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  window.addEventListener('catalogue:ready', schedule);
  new MutationObserver(labels).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  labels();
  schedule();
})();
