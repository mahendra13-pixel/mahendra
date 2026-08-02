// ============================================
// INDEX PAGE SPECIFIC JAVASCRIPT
// ============================================

// Animated Counter for Stats Section
const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const counters = entry.target.querySelectorAll('.stat-number');
            counters.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-target'));
                if (isNaN(target)) return;
                
                let current = 0;
                const increment = target / 60; // Smoother increment
                const duration = 2000; // 2 seconds
                const stepTime = duration / 60; // ~33ms per step
                
                const updateCounter = () => {
                    if (current < target) {
                        current += increment;
                        counter.innerText = Math.floor(current);
                        setTimeout(updateCounter, stepTime);
                    } else {
                        counter.innerText = target;
                    }
                };
                updateCounter();
            });
            counterObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.3 }); // Changed to 0.3 for earlier trigger

const statsSection = document.querySelector('.stats-section');
if (statsSection) {
    counterObserver.observe(statsSection);
}

// Testimonial Slider
const slider = document.getElementById('testimonialSlider');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');

if (slider && prevBtn && nextBtn) {
    let scrollAmount = 0;
    const scrollStep = 380; // Width of testimonial card + gap

    nextBtn.addEventListener('click', () => {
        scrollAmount += scrollStep;
        const maxScroll = slider.scrollWidth - slider.clientWidth;
        if (scrollAmount >= maxScroll) {
            scrollAmount = 0; // Loop back to start
        }
        slider.scrollTo({
            left: scrollAmount,
            behavior: 'smooth'
        });
    });

    prevBtn.addEventListener('click', () => {
        scrollAmount -= scrollStep;
        if (scrollAmount <= 0) {
            scrollAmount = slider.scrollWidth - slider.clientWidth; // Loop to end
        }
        slider.scrollTo({
            left: scrollAmount,
            behavior: 'smooth'
        });
    });
}

// Optional: Add smooth scroll for anchor links (e.g. "See Gallery" -> #gallery)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Optional: Add loading animation for cards + gallery photos
window.addEventListener('load', () => {
    console.log('Index page fully loaded - Peaceful Boys Hostel');

    const fadeElements = document.querySelectorAll('.category-card, .blog-card, .gallery-item');
    fadeElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = `opacity 0.5s ease ${index * 0.1}s, transform 0.5s ease ${index * 0.1}s`;
        
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 100);
    });
});