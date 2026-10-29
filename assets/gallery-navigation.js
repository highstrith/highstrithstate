/* Keep image viewing inside the page's normal Back / Forward history. */
(() => {
  'use strict';
  window.createGalleryNavigation = dialog => {
    const entries = new Map();
    let current = '';
    let waiting = false;
    const state = () => history.state && typeof history.state === 'object' ? history.state : {};
    const show = callback => {
      callback();
      dialog.dispatchEvent(new Event('gallery:open'));
    };
    const open = callback => {
      if (waiting || dialog.open) return;
      current = `gallery-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      entries.set(current, callback);
      try { history.pushState({ ...state(), portfolioGallery: current }, '', location.href); }
      catch { current = ''; }
      show(callback);
    };
    const close = () => {
      if (!dialog.open || waiting) return;
      if (current && state().portfolioGallery === current) {
        waiting = true;
        history.back();
      } else dialog.close();
    };
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
    window.addEventListener('popstate', () => {
      const key = state().portfolioGallery;
      waiting = false;
      if (entries.has(key)) {
        current = key;
        if (!dialog.open) show(entries.get(key));
      } else {
        current = '';
        if (dialog.open) dialog.close();
      }
    });
    return { open, close };
  };
})();
