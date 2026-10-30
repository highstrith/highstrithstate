(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var hero = document.querySelector('.hero-feature');
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var y = window.scrollY;
      if (hero && y < window.innerHeight) {
        hero.style.transform = 'translateY(' + Math.min(40, y * 0.08).toFixed(1) + 'px)';
      }
      document.querySelectorAll('[data-brighten]').forEach(function (el) {
        var r = el.getBoundingClientRect();
        var p = 1 - Math.max(0, Math.min(1, (r.top - window.innerHeight * 0.3) / (window.innerHeight * 0.5)));
        el.style.opacity = (0.35 + 0.65 * p).toFixed(2);
      });
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (window.matchMedia('(pointer: fine)').matches) {
    document.querySelectorAll('.button, .fly-more').forEach(function (btn) {
      btn.addEventListener('pointermove', function (e) {
        var r = btn.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) / r.width * 12;
        var dy = (e.clientY - (r.top + r.height / 2)) / r.height * 8;
        btn.style.transform = 'translate(' + dx.toFixed(1) + 'px, ' + dy.toFixed(1) + 'px)';
      });
      btn.addEventListener('pointerleave', function () { btn.style.transform = ''; });
    });
  }
})();
