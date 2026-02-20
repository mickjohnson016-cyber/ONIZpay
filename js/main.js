document.addEventListener('DOMContentLoaded', () => {

    // ── Navbar scroll effect ──
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 60);
        }, { passive: true });
    }

    // ── Smooth anchor scrolling ──
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const id = link.getAttribute('href');
            if (!id || id === '#') return;
            const target = document.querySelector(id);
            if (target) {
                e.preventDefault();
                window.scrollTo({
                    top: target.offsetTop - 70,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ── "Watch Overview" scrolls to video section ──
    const watchBtn = document.getElementById('watchOverviewBtn');
    if (watchBtn) {
        watchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const videoSection = document.getElementById('video');
            if (videoSection) {
                window.scrollTo({
                    top: videoSection.offsetTop - 70,
                    behavior: 'smooth'
                });
            }
        });
    }
    // ── Read More / Read Less toggle ──
    const readMoreBtn = document.getElementById('readMoreToggle');
    const expandBlock = document.getElementById('heroDescExpand');
    if (readMoreBtn && expandBlock) {
        readMoreBtn.addEventListener('click', () => {
            const isOpen = expandBlock.classList.toggle('open');
            readMoreBtn.textContent = isOpen ? 'Read Less' : 'Read More';
        });
    }

});
