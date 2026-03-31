// HAVEN — Main JS

document.addEventListener('DOMContentLoaded', function () {

  // ── Active nav link ──
  // Match current path to nav links; use startsWith so /journal/ matches /journal
  const path = window.location.pathname;
  document.querySelectorAll('.haven-navbar .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    // Exact match for root dashboard, startsWith for everything else
    const isActive = href === path || (href !== '/' && path.startsWith(href));
    if (isActive) link.classList.add('active');
  });

  // ── Staggered card animations ──
  document.querySelectorAll('.feature-card').forEach((card, i) => {
    card.style.animationDelay = `${i * 0.06}s`;
    card.classList.add('fade-in');
  });

  // ── Auto-dismiss alerts after 5s ──
  document.querySelectorAll('.alert-haven').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

});
