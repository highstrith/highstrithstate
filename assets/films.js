/* films.js — 片单页的语言切换与年份。内容本身写在 HTML 里，脚本只做增强。 */
(() => {
  'use strict';
  const button = document.querySelector('#langSwitch');
  const current = document.querySelector('[aria-current="page"]');
  let language = new URLSearchParams(window.location.search).get('lang') === 'en' ? 'en' : 'cn';

  function withLanguage(href, english) {
    const url = new URL(href, window.location.href);
    url.search = english ? '?lang=en' : '';
    return `${url.pathname.split('/').pop()}${url.search}${url.hash}`;
  }

  // 观看按钮的文案跟着链接走：拿到作品页直链时显示「观看第 01 集」，
  // 只有平台搜索页时如实写成「在抖音搜索」，换链接不用再改一次文案。
  const isSearchLink = link => /\/search\//.test(link.getAttribute('href') || '');
  function labelWatch() {
    const english = language === 'en';
    document.querySelectorAll('[data-watch]').forEach(link => {
      const text = link.querySelector('span[data-cn]');
      if (!text) return;
      const key = isSearchLink(link) ? (english ? 'enSearch' : 'cnSearch') : (english ? 'en' : 'cn');
      text.textContent = text.dataset[key];
    });
  }

  function setLanguage() {
    const english = language === 'en';
    document.documentElement.lang = english ? 'en' : 'zh-CN';
    document.title = english ? 'AI Film Index · Highstrith' : 'AI 影像片单 · Highstrith 橘小桔';
    document.querySelectorAll('[data-cn][data-en]').forEach(element => {
      element.textContent = element.dataset[language];
    });
    labelWatch();
    document.querySelectorAll('[data-cn-label][data-en-label]').forEach(element => {
      element.setAttribute(element.tagName === 'IMG' ? 'alt' : 'aria-label', element.dataset[`${language}Label`]);
    });
    document.querySelectorAll('[data-home-link]').forEach(link => {
      const url = new URL(link.getAttribute('href'), window.location.href);
      link.setAttribute('href', `index.html${english ? '?lang=en' : ''}${url.hash}`);
    });
    document.querySelectorAll('[data-projects-link]').forEach(link => {
      link.setAttribute('href', withLanguage('projects.html', english));
    });
    document.querySelectorAll('[data-resume-link]').forEach(link => {
      link.setAttribute('href', withLanguage('resume.html', english));
    });
    current.setAttribute('href', withLanguage('films.html', english));
    button.textContent = english ? '中文' : 'EN';
    button.setAttribute('aria-label', english ? '切换到中文' : 'Switch to English');
    button.setAttribute('aria-pressed', String(english));
    const url = new URL(window.location.href);
    if (english) url.searchParams.set('lang', 'en');
    else url.searchParams.delete('lang');
    // file:// 下浏览器可能拒绝改写地址，本地预览不受影响。
    try { window.history.replaceState(null, '', url); } catch { /* ignore */ }
  }

  button.addEventListener('click', () => {
    language = language === 'cn' ? 'en' : 'cn';
    setLanguage();
  });
  const year = document.querySelector('#copyrightYear');
  if (year) year.textContent = String(new Date().getFullYear());
  setLanguage();
})();
