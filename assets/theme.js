/* Apply the saved palette before rendering; enhance controls after parsing. */
(() => {
  'use strict';
  const root = document.documentElement;
  const key = 'highstrith-theme';
  const read = () => {
    try { return localStorage.getItem(key) === 'dark' ? 'dark' : 'light'; }
    catch { return 'light'; }
  };
  function apply(theme) {
    root.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#111214' : '#f4f4f0');
  }
  apply(read());
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('#themeToggle');
    if (!button) return;
    function label() {
      const dark = root.dataset.theme === 'dark';
      const english = root.lang === 'en';
      const text = english ? (dark ? 'Switch to light mode' : 'Switch to dark mode')
        : (dark ? '切换到浅色模式' : '切换到深色模式');
      button.setAttribute('aria-label', text);
      button.title = text;
      button.setAttribute('aria-pressed', String(dark));
    }
    button.hidden = false;
    label();
    button.addEventListener('click', () => {
      const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(next);
      try { localStorage.setItem(key, next); } catch { /* Switching still works without storage. */ }
    });
    new MutationObserver(label).observe(root, { attributes: true, attributeFilter: ['lang', 'data-theme'] });
    window.addEventListener('storage', event => { if (event.key === key || event.key === null) apply(read()); });
    window.addEventListener('pageshow', event => { if (event.persisted) apply(read()); });
  });
})();
