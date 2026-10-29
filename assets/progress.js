(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  let english = new URLSearchParams(location.search).get('lang') === 'en';
  const gallery = [...document.querySelectorAll('[data-progress-image]')];
  const viewer = $('#progressViewer');
  const image = $('#progressViewerImage');
  const status = $('#progressViewerStatus');
  let selected = 0;
  let returnFocus = null;
  let imageState = '';

  function updateViewerText() {
    const frame = gallery[selected].closest('figure');
    const title = frame.querySelector('h4').textContent;
    $('#progressViewerTitle').textContent = title;
    $('#progressViewerDescription').textContent = frame.querySelector('figcaption p').textContent;
    $('#progressViewerPosition').textContent = `${String(selected + 1).padStart(2, '0')} / ${String(gallery.length).padStart(2, '0')}`;
    image.alt = title;
    status.textContent = imageState === 'error'
      ? (english ? 'Image unavailable. Try opening the full image.' : '图片暂时无法加载，可以试试打开原图。')
      : (english ? 'Loading image…' : '正在加载图片…');
  }

  function setLanguage() {
    const language = english ? 'en' : 'cn';
    document.documentElement.lang = english ? 'en' : 'zh-CN';
    document.title = english ? 'In progress · Highstrith' : '正在制作 · Highstrith 橘小桔';
    document.querySelectorAll('[data-cn][data-en]').forEach(element => { element.textContent = element.dataset[language]; });
    document.querySelectorAll('[data-cn-label][data-en-label]').forEach(element => {
      element.setAttribute(element.tagName === 'IMG' ? 'alt' : 'aria-label', element.dataset[`${language}Label`]);
    });
    document.querySelectorAll('[data-home-link], [data-projects-link], [data-progress-link]').forEach(link => {
      const url = new URL(link.getAttribute('href'), location.href);
      url.search = english ? '?lang=en' : '';
      link.setAttribute('href', `${url.pathname.split('/').at(-1)}${url.search}${url.hash}`);
    });
    $('#langSwitch').textContent = english ? '中文' : 'EN';
    $('#langSwitch').setAttribute('aria-label', english ? '切换到中文' : 'Switch to English');
    $('#langSwitch').setAttribute('aria-pressed', String(english));
    gallery.forEach(link => link.setAttribute('aria-label', `${english ? 'View image' : '查看大图'}: ${link.closest('figure').querySelector('h4').textContent}`));
    if (viewer.open) updateViewerText();
    const url = new URL(location.href);
    if (english) url.searchParams.set('lang', 'en');
    else url.searchParams.delete('lang');
    try { history.replaceState(null, '', url); } catch { /* file mode may deny history changes */ }
  }

  function showImage(index) {
    selected = (index + gallery.length) % gallery.length;
    imageState = 'loading';
    status.hidden = false;
    image.hidden = true;
    updateViewerText();
    $('#progressOriginal').href = gallery[selected].href;
    image.onload = () => { imageState = ''; status.hidden = true; image.hidden = false; };
    image.onerror = () => { imageState = 'error'; updateViewerText(); };
    image.src = gallery[selected].href;
  }

  gallery.forEach((link, index) => link.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    returnFocus = link;
    showImage(index);
    viewer.showModal();
    document.body.classList.add('modal-open');
    $('#progressViewerClose').focus({ preventScroll: true });
  }));
  $('#progressPrevious').addEventListener('click', () => showImage(selected - 1));
  $('#progressNext').addEventListener('click', () => showImage(selected + 1));
  $('#progressViewerClose').addEventListener('click', () => viewer.close());
  viewer.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    showImage(selected + (event.key === 'ArrowRight' ? 1 : -1));
  });
  viewer.addEventListener('close', () => {
    if (viewer.open) return;
    image.onload = image.onerror = null;
    image.removeAttribute('src');
    document.body.classList.remove('modal-open');
    returnFocus?.focus({ preventScroll: true });
    returnFocus = null;
  });
  viewer.addEventListener('click', event => {
    if (event.target !== viewer) return;
    const rect = viewer.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) viewer.close();
  });
  $('#langSwitch').addEventListener('click', () => { english = !english; setLanguage(); });
  $('#copyrightYear').textContent = String(new Date().getFullYear());
  setLanguage();
})();
