(() => {
  'use strict';
  const button = document.querySelector('#langSwitch');
  let language = new URLSearchParams(window.location.search).get('lang') === 'en' ? 'en' : 'cn';

  function setLanguage() {
    document.documentElement.lang = language === 'en' ? 'en' : 'zh-CN';
    document.title = language === 'en' ? 'Projects & apps · Highstrith' : '项目与应用 · Highstrith 橘小桔';
    document.querySelectorAll('[data-cn][data-en]').forEach(element => {
      element.textContent = element.dataset[language];
    });
    document.querySelectorAll('[data-cn-label][data-en-label]').forEach(element => {
      element.setAttribute(element.tagName === 'IMG' ? 'alt' : 'aria-label', element.dataset[`${language}Label`]);
    });
    document.querySelectorAll('[data-home-link]').forEach(link => {
      const url = new URL(link.getAttribute('href'), window.location.href);
      url.search = language === 'en' ? '?lang=en' : '';
      link.setAttribute('href', `index.html${url.search}${url.hash}`);
    });
    document.querySelectorAll('[data-resume-link]').forEach(link => {
      link.setAttribute('href', language === 'en' ? 'resume.html?lang=en' : 'resume.html');
    });
    document.querySelectorAll('[data-films-link]').forEach(link => {
      link.setAttribute('href', language === 'en' ? 'films.html?lang=en' : 'films.html');
    });
    document.querySelector('[aria-current="page"]').setAttribute('href', language === 'en' ? 'projects.html?lang=en' : 'projects.html');
    button.textContent = language === 'en' ? '中文' : 'EN';
    button.setAttribute('aria-label', language === 'en' ? '切换到中文' : 'Switch to English');
    button.setAttribute('aria-pressed', String(language === 'en'));
    const url = new URL(window.location.href);
    if (language === 'en') url.searchParams.set('lang', 'en');
    else url.searchParams.delete('lang');
    // file:// links still work when a browser disallows history replacement.
    try { window.history.replaceState(null, '', url); } catch {}
  }

  button.addEventListener('click', () => {
    language = language === 'cn' ? 'en' : 'cn';
    setLanguage();
  });
  document.querySelector('#copyrightYear').textContent = String(new Date().getFullYear());
  setLanguage();
})();
