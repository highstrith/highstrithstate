/* Grouped image entrances, tactile hover and full-image transitions. */
(() => {
  'use strict';
  if (!window.gsap || !window.ScrollTrigger) return;
  const { gsap, ScrollTrigger } = window;
  gsap.registerPlugin(ScrollTrigger);
  gsap.matchMedia().add('(prefers-reduced-motion: no-preference)', () => {
    document.documentElement.classList.add('production-motion');
    const cleanups = [];
    const groups = document.querySelectorAll('.progress-gallery, .home-progress-grid');
    const targets = [...groups].flatMap(group => [...group.children]);
    const surfaces = [];
    const intro = document.querySelectorAll('.progress-return, .progress-heading, .progress-project-heading, .progress-index');
    if (intro.length) gsap.from(intro, { autoAlpha: 0, y: 24, duration: .75, stagger: .1, ease: 'power3.out', clearProps: 'transform,opacity,visibility' });
    groups.forEach(group => gsap.from(group.children, {
      autoAlpha: 0, y: 42, scale: .95, duration: .85,
      stagger: .085, ease: 'power3.out', immediateRender: false,
      clearProps: 'transform,opacity,visibility',
      scrollTrigger: { trigger: group, start: 'top 94%', once: true },
    }));
    const listen = (node, event, callback) => {
      node.addEventListener(event, callback);
      cleanups.push(() => node.removeEventListener(event, callback));
    };
    listen(window, 'catalogue:ready', () => ScrollTrigger.refresh());
    listen(window, 'catalogue:layout', () => ScrollTrigger.refresh());
    if (matchMedia('(hover: hover) and (pointer: fine)').matches) {
      document.querySelectorAll('.progress-gallery a, .home-progress-card').forEach(link => {
        const surface = link.matches('.home-progress-card') ? link.querySelector('img') : link;
        surfaces.push(surface);
        listen(link, 'pointermove', event => {
          const rect = link.getBoundingClientRect();
          const x = (event.clientX - rect.left) / rect.width - .5;
          const y = (event.clientY - rect.top) / rect.height - .5;
          gsap.to(surface, { rotationY: x * 7, rotationX: -y * 6, y: -5, scale: 1.018, duration: .4, ease: 'power2.out', overwrite: true, transformPerspective: 900 });
        });
        listen(link, 'pointerleave', () => gsap.to(surface, { rotationY: 0, rotationX: 0, y: 0, scale: 1, duration: .7, ease: 'elastic.out(1, .6)', overwrite: true, clearProps: 'transform' }));
      });
    }
    const dialogs = document.querySelectorAll('#progressViewer, #stillViewer');
    const images = document.querySelectorAll('#progressViewerImage, #stillViewerImage');
    dialogs.forEach(dialog => listen(dialog, 'gallery:open', () => gsap.fromTo(dialog,
      { autoAlpha: 0, scale: .96, y: 20 },
      { autoAlpha: 1, scale: 1, y: 0, duration: .45, ease: 'back.out(1.1)', overwrite: true, clearProps: 'transform,opacity,visibility' }
    )));
    images.forEach(image => listen(image, 'gallery:image', () => gsap.fromTo(image,
      { autoAlpha: 0, scale: .95, x: 18 },
      { autoAlpha: 1, scale: 1, x: 0, duration: .5, ease: 'power3.out', overwrite: true, clearProps: 'transform,opacity,visibility' }
    )));
    return () => {
      cleanups.forEach(cleanup => cleanup());
      const animated = [...intro, ...targets, ...surfaces, ...dialogs, ...images];
      gsap.killTweensOf(animated);
      gsap.set(animated, { clearProps: 'transform,opacity,visibility' });
      document.documentElement.classList.remove('production-motion');
    };
  });
})();
