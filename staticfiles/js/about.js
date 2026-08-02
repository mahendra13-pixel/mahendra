// About Hostel Section - PAN badge & highlights animation
const hostelSection = document.querySelector('.about-hostel-section');

if (hostelSection) {
    const panBadge = hostelSection.querySelector('.pan-badge');
    const highlights = hostelSection.querySelectorAll('.hostel-highlights li');
    const hostelImg = hostelSection.querySelector('.hostel-img');

    // Set initial states
    if (panBadge) {
        panBadge.style.opacity = '0';
        panBadge.style.transform = 'scale(0.9)';
        panBadge.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    }
    if (hostelImg) {
        hostelImg.style.opacity = '0';
        hostelImg.style.transform = 'translateX(-30px)';
        hostelImg.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    }
    highlights.forEach(li => {
        li.style.opacity = '0';
        li.style.transform = 'translateX(-15px)';
        li.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    });

    const hostelObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                if (hostelImg) {
                    hostelImg.style.opacity = '1';
                    hostelImg.style.transform = 'translateX(0)';
                }
                if (panBadge) {
                    setTimeout(() => {
                        panBadge.style.opacity = '1';
                        panBadge.style.transform = 'scale(1)';
                    }, 200);
                }
                highlights.forEach((li, index) => {
                    setTimeout(() => {
                        li.style.opacity = '1';
                        li.style.transform = 'translateX(0)';
                    }, 400 + index * 100);
                });
                hostelObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    hostelObserver.observe(hostelSection);
}