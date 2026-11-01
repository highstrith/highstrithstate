(() => {
  'use strict';

  // Language State
  let currentLang = new URLSearchParams(window.location.search).get('lang') === 'en' ? 'en' : 'cn';

  // DOM Elements
  const langSwitchBtn = document.querySelector('#langSwitch');
  const toast = document.querySelector('#toast');
  const qrDialog = document.querySelector('#qrDialog');
  const qrDialogClose = document.querySelector('#qrDialogClose');
  const qrDialogImg = document.querySelector('#qrDialogImg');
  const qrDialogTitle = document.querySelector('#qrDialogTitle');
  const qrDialogDesc = document.querySelector('#qrDialogDesc');

  // Toast Functionality
  let toastTimer = null;
  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, 2400);
  }

  // Language Toggle
  function setLanguage(lang) {
    currentLang = lang;
    document.documentElement.lang = currentLang === 'en' ? 'en' : 'zh-CN';
    document.title = currentLang === 'en' 
      ? 'Junjie Lin (Highstrith) · Creator Profile & Resume' 
      : '林俊杰 · 创作者档案与个人简历 — Highstrith';

    document.querySelectorAll('[data-cn][data-en]').forEach(el => {
      el.textContent = el.dataset[currentLang];
    });
    document.querySelectorAll('[data-cn-label][data-en-label]').forEach(el => {
      el.setAttribute(el.tagName === 'IMG' ? 'alt' : 'aria-label', el.dataset[`${currentLang}Label`]);
    });

    // Update cross-page links with language query parameter
    document.querySelectorAll('a[href^="index.html"], a[href^="projects.html"]').forEach(el => {
      const url = new URL(el.getAttribute('href'), window.location.href);
      if (currentLang === 'en') url.searchParams.set('lang', 'en');
      else url.searchParams.delete('lang');
      el.setAttribute('href', url.pathname.split('/').pop() + url.search + url.hash);
    });

    if (langSwitchBtn) {
      langSwitchBtn.textContent = currentLang === 'en' ? '中文' : 'EN';
      langSwitchBtn.setAttribute('aria-label', currentLang === 'en' ? '切换到中文' : 'Switch to English');
      langSwitchBtn.setAttribute('aria-pressed', String(currentLang === 'en'));
    }

    // Keep lang query param in URL if supported
    try {
      const url = new URL(window.location.href);
      if (currentLang === 'en') {
        url.searchParams.set('lang', 'en');
      } else {
        url.searchParams.delete('lang');
      }
      window.history.replaceState(null, '', url);
    } catch {}
  }

  // QR Code Popups
  document.querySelectorAll('[data-open-qr]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!qrDialog) return;
      const qrType = btn.getAttribute('data-open-qr');
      if (qrType === 'wechat') {
        if (qrDialogImg) qrDialogImg.src = 'assets/social/wechat-qr.png';
        if (qrDialogTitle) qrDialogTitle.textContent = currentLang === 'en' ? 'WeChat Contact' : '微信扫码联系';
        if (qrDialogDesc) qrDialogDesc.textContent = currentLang === 'en' ? 'ID: Gw1sgdsj_787' : '微信号：Gw1sgdsj_787（点击即可复制）';
      } else {
        if (qrDialogImg) qrDialogImg.src = 'assets/site-qr.svg';
        if (qrDialogTitle) qrDialogTitle.textContent = currentLang === 'en' ? 'Scan to View Works' : '手机扫码浏览作品集';
        if (qrDialogDesc) qrDialogDesc.textContent = 'highstrith.github.io/highstrithstate';
      }
      if (typeof qrDialog.showModal === 'function') {
        qrDialog.showModal();
      } else {
        qrDialog.setAttribute('open', '');
      }
    });
  });

  if (qrDialogClose && qrDialog) {
    qrDialogClose.addEventListener('click', () => {
      if (typeof qrDialog.close === 'function') {
        qrDialog.close();
      } else {
        qrDialog.removeAttribute('open');
      }
    });
  }

  // Copy to clipboard
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const textToCopy = btn.getAttribute('data-copy');
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          showToast(currentLang === 'en' ? `Copied: ${textToCopy}` : `已复制：${textToCopy}`);
        }).catch(() => {
          showToast(`微信号：${textToCopy}`);
        });
      } else {
        showToast(`微信号：${textToCopy}`);
      }
    });
  });

  if (langSwitchBtn) {
    langSwitchBtn.addEventListener('click', () => {
      setLanguage(currentLang === 'cn' ? 'en' : 'cn');
    });
  }

  // Initialize
  setLanguage(currentLang);
})();
