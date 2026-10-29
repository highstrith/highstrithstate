/* Shared, progressively enhanced navigation for the portfolio and project page. */
(() => {
  'use strict';
  const header = document.querySelector('.site-header');
  const nav = document.querySelector('.main-nav');
  const toggle = document.querySelector('#menuToggle');
  if (!header || !nav || !toggle) return;
  const collection = header.querySelector('.nav-collection');
  const collectionToggle = collection?.querySelector('summary');
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
