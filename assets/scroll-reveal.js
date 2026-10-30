/*
 * scroll-reveal.js — 滚动驱动的沉浸式展开动画（零依赖）。
 *
 * 与 artocea 类似的观感：滚动时区块内容「展开」进视口，大标题逐行浮现，
 * 图片与海报轻微缩放/上移，营造一屏一节的叙事节奏。
 *
 * 实现要点：
 *  - IntersectionObserver 触发 CSS 过渡（不用 rAF 轮询，省电且支持 reduced-motion）。
 *  - 所有动效都走 CSS class 切换，天然支持 prefers-reduced-motion 降级。
 *  - 标题按「行」拆分为 .rv-line（逐行错峰上移+淡入）。
 *  - 图片/卡片/区块用 .rv（单元素淡入上移）或 .rv-scale（额外缩放）。
 */
(() => {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const noMotion = () => reducedMotion.matches;
  document.documentElement.classList.add('reveal-ready');

  // 标题按换行拆成「行」，每行包一层 .rv-line，做错峰浮现。
  // 换行既可能是文本里的 \n（copy 文案），也可能是 <br> 标签（初始 HTML）。
  function splitLines(root) {
    if (noMotion()) return;
    const headings = root.querySelectorAll('[data-lines]');
    headings.forEach((heading) => {
      // 已拆分过且文本未变则跳过（幂等，避免语言切换等重复调用时嵌套）。
      if (heading.dataset.lines === 'done') return;
      heading.dataset.lines = 'done';
      // 确保标题自身会进入观察器并触发 rv-in（否则 .rv-line 一直隐藏）。
      if (!heading.hasAttribute('data-reveal')) heading.setAttribute('data-reveal', '');
      // 先把 <br> 归一成 \n 文本，再统一按 \n 拆行。
      const raw = heading.innerHTML.replace(/<br\s*\/?>/gi, '\n');
      const text = raw.replace(/<[^>]+>/g, '').replace(/\n+/g, '\n').trim();
      heading.textContent = '';
      const lines = text.split('\n').map((line) => line.trim()).filter(Boolean);
      lines.forEach((line, index) => {
        const span = document.createElement('span');
        span.className = 'rv-line';
        span.style.setProperty('--i', String(index));
        span.textContent = line;
        heading.append(span);
        // Each rv-line is already a block. A BR here adds an empty line box.
        if (index < lines.length - 1) heading.append(document.createTextNode('\n'));
      });
    });
  }

  // 语言切换后标题文本已由 studio.js 重写为「文本 + <br>」，
  // 这里清掉 done 标记让 splitLines 重新按新语言拆分逐行动画。
  // 注意：只清 done 值、保留 data-lines 属性本身（否则 [data-lines] 选择器匹配不到）。
  function resetLines(root) {
    root.querySelectorAll('[data-lines]').forEach((heading) => {
      heading.dataset.lines = '';
    });
    splitLines(root);
  }

  // 把所有待动画元素按「进入视口即展开」注册进观察器。
  function observe(root) {
    const targets = root.querySelectorAll('[data-reveal]');
    if (!('IntersectionObserver' in window) || noMotion() || !targets.length) {
      targets.forEach((el) => el.classList.add('rv-in'));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('rv-in');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    targets.forEach((el) => observer.observe(el));
  }

  // 对 hero 海报等元素做轻量视差：随滚动平移，制造「空间后退」感。
  function attachParallax(root) {
    if (noMotion() || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    const layers = root.querySelectorAll('[data-parallax]');
    if (!layers.length) return;
    let ticking = false;
    const update = () => {
      ticking = false;
      layers.forEach((el) => {
        const speed = parseFloat(el.dataset.parallax) || 0.08;
        const rect = el.getBoundingClientRect();
        const viewport = window.innerHeight;
        // 仅当元素在视口附近时计算，避免离屏无谓布局。
        if (rect.bottom < -viewport || rect.top > viewport * 2) return;
        const offset = (rect.top + rect.height / 2 - viewport / 2) * speed;
        el.style.transform = `translate3d(0, ${(-offset).toFixed(1)}px, 0)`;
      });
    };
    const request = () => {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(update);
      }
    };
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request, { passive: true });
    update();
  }

  // 公开给 studio.js 在动态渲染（作品卡片 / 截图 / 语言切换）后调用。
  window.StudioReveal = {
    refresh(root) {
      const scope = root || document;
      splitLines(scope);
      observe(scope);
    },
    // 语言切换后重排标题逐行动画。
    relang(root) {
      resetLines(root || document);
    },
  };

  // 页面加载完成后统一初始化。
  function init() {
    splitLines(document);
    observe(document);
    attachParallax(document);
  }

  reducedMotion.addEventListener('change', () => {
    if (!noMotion()) return;
    document.querySelectorAll('[data-reveal]').forEach(element => element.classList.add('rv-in'));
    document.querySelectorAll('[data-parallax]').forEach(element => element.style.removeProperty('transform'));
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
