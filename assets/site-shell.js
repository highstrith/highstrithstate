/* Shared, progressively enhanced navigation for the portfolio and project page. */
(() => {
  'use strict';
  const header = document.querySelector('.site-header');
  const nav = document.querySelector('.main-nav');
  const toggle = document.querySelector('#menuToggle');
  if (!header || !nav || !toggle) return;
  const collection = header.querySelector('.nav-collection');
  const collectionToggle = collection?.querySelector('summary');
  header.querySelectorAll('a').forEach(link => link.target = '_self');
  const compact = matchMedia('(max-width: 800px)');
  const english = () => document.documentElement.lang === 'en';
  function label() {
    const open = toggle.getAttribute('aria-expanded') === 'true';
    const value = english() ? (open ? 'Close menu' : 'Menu') : (open ? '收起' : '菜单');
    toggle.querySelector('[data-menu-label]').textContent = value;
    toggle.setAttribute('aria-label', value);
    collectionToggle?.setAttribute('aria-label', english()
      ? (collection.open ? 'Close work navigation' : 'Open work navigation')
      : (collection.open ? '收起作品导航' : '展开作品导航'));
  }
  function setOpen(open, returnFocus = false) {
    toggle.setAttribute('aria-expanded', String(open));
    header.classList.toggle('menu-open', open);
    if (!open && collection) collection.open = false;
    label();
    if (open && compact.matches) nav.querySelector('a')?.focus({ preventScroll: true });
    if (returnFocus) toggle.focus({ preventScroll: true });
  }
  toggle.hidden = false;
  document.documentElement.classList.add('shell-ready');
  toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));

  // Long one-page sites make native hash scrolling read as a flight instead of a
  // jump: Chrome spends ~1.5s crossing 8 000px and every section blurs past.
  // Cap the duration so the move reads as a deliberate cut, and keep the URL
  // hash in sync without letting the browser scroll a second time.
  const relaxed = matchMedia('(prefers-reduced-motion: reduce)');
  let scrollToken = 0;

  function sameDocumentTarget(link) {
    const destination = new URL(link.href, location.href);
    if (destination.origin !== location.origin) return null;
    if (destination.pathname !== location.pathname) return null;
    if (destination.search !== location.search) return null;
    if (!destination.hash) return null;
    return document.getElementById(decodeURIComponent(destination.hash.slice(1)));
  }

  function scrollPadding() {
    const value = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop);
    return Number.isFinite(value) ? value : header.getBoundingClientRect().height + 12;
  }

  function hardScroll(top) {
    // Inline 'auto' wins over the stylesheet's `scroll-behavior: smooth`, which
    // would otherwise smooth every animation frame.
    const previous = document.documentElement.style.scrollBehavior;
    document.documentElement.style.scrollBehavior = 'auto';
    window.scrollTo(0, top);
    document.documentElement.style.scrollBehavior = previous;
  }

  function scrollToAnchor(target, hash, instant) {
    const limit = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    const top = Math.round(Math.min(limit, Math.max(0, target.getBoundingClientRect().top + window.scrollY - scrollPadding())));
    const token = ++scrollToken;
    const from = window.scrollY;
    const distance = top - from;
    // Native anchor navigation moves focus; keep that for keyboard and screen readers.
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
    if (hash && location.hash !== hash) {
      try { history.pushState(null, '', hash); } catch { /* file:// denies history changes */ }
    }
    if (instant || relaxed.matches || Math.abs(distance) < 6) { hardScroll(top); return; }
    const duration = Math.min(460, 200 + Math.abs(distance) * 0.025);
    const start = performance.now();
    const ease = progress => 1 - Math.pow(1 - progress, 3);
    const step = now => {
      if (token !== scrollToken) return;
      const progress = Math.min(1, (now - start) / duration);
      hardScroll(Math.round(from + distance * ease(progress)));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // Any manual input takes over from a jump in progress, the way native smooth
  // scrolling yields to the wheel.
  ['wheel', 'touchstart', 'keydown'].forEach(type => {
    window.addEventListener(type, () => { scrollToken += 1; }, { passive: true });
  });

  document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a');
    if (!link || link.target === '_blank') return;
    // Skip links are a jump for assistive tech; they land at once and take focus.
    const skipLink = link.classList.contains('skip-link');
    const target = sameDocumentTarget(link);
    if (!target) return;
    event.preventDefault();
    scrollToAnchor(target, new URL(link.href, location.href).hash, skipLink);
  });

  // Keep ordinary site navigation in this document's browsing context,
  // including embedded browsers that otherwise intercept link clicks.
  header.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const destination = new URL(link.href, location.href);
    if (destination.origin !== location.origin) return;
    // Same-document anchors are handled by the scrolling above.
    if (sameDocumentTarget(link)) return;
    event.preventDefault();
    location.assign(destination.href);
  });
  document.addEventListener('click', event => {
    if (collection && !collection.contains(event.target)) collection.open = false;
    if (!header.contains(event.target)) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    if (collection?.open) {
      collection.open = false;
      collectionToggle.focus({ preventScroll: true });
      event.preventDefault();
    } else if (header.classList.contains('menu-open')) setOpen(false, true);
  });
  header.addEventListener('focusout', () => {
    requestAnimationFrame(() => { if (!header.contains(document.activeElement)) setOpen(false); });
  });
  nav.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link) return;
    const fromCollection = Boolean(collection?.open);
    if (collection) collection.open = false;
    if (compact.matches) setOpen(false);
    const href = link.getAttribute('href');
    if (href?.startsWith('#') && (compact.matches || fromCollection)) {
      const target = document.getElementById(href.slice(1));
      if (target) {
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
    }
  });
  compact.addEventListener('change', () => setOpen(false));
  collection?.addEventListener('toggle', label);
  new MutationObserver(label).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  label();
})();
