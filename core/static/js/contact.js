// ============================================
// CONTACT PAGE SPECIFIC JAVASCRIPT
// ============================================

// ===============================
// PREVENT CACHING - Force fresh load every time
// ===============================
(function preventCaching() {
    // Add cache-busting parameter to all links and forms
    const cacheBuster = Date.now();
    
    // Override fetch and XMLHttpRequest to add cache-busting
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        if (typeof url === 'string' && url.includes('?')) {
            url += '&_=' + cacheBuster;
        } else if (typeof url === 'string') {
            url += '?_=' + cacheBuster;
        }
        return originalFetch.call(this, url, options);
    };
    
    // Add cache-busting to all anchor tags
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        if (link && link.href && !link.href.startsWith('javascript:')) {
            const url = new URL(link.href);
            url.searchParams.set('_t', Date.now());
            link.href = url.toString();
        }
    });
    
    // Add cache-busting to forms
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form && form.action) {
            const url = new URL(form.action);
            url.searchParams.set('_t', Date.now());
            form.action = url.toString();
        }
    });
    
    console.log('Cache prevention enabled - Page will always load fresh');
})();

document.addEventListener("DOMContentLoaded", function () {

    // ===============================
    // CAPTURE CLIENT HOSTNAME
    // ===============================
    function captureClientHostname() {
        const hostnameInput = document.getElementById('hostname_hidden');
        if (!hostnameInput) return;
        
        let hostname = '';
        
        // Method 1: Try to get from window.location (works for network names)
        try {
            hostname = window.location.hostname;
            if (hostname === 'localhost' || hostname === '127.0.0.1') {
                hostname = '';
            }
        } catch(e) {}
        
        // Method 2: Try to get from navigator (some browsers expose it)
        if (!hostname) {
            try {
                const ua = navigator.userAgent;
                const match = ua.match(/\(([^)]+)\)/);
                if (match) {
                    const parts = match[1].split(';');
                    for (let part of parts) {
                        part = part.trim();
                        if (part && !part.match(/windows|mac|linux|android|iphone|ipad/i)) {
                            hostname = part;
                            break;
                        }
                    }
                }
            } catch(e) {}
        }
        
        // If we got a hostname and it's not localhost, store it
        if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
            hostnameInput.value = hostname;
            console.log('Client hostname captured:', hostname);
        } else {
            hostnameInput.value = '';
            console.log('Could not capture client hostname, will use server fallback');
        }
    }

    // Call the function to capture hostname
    captureClientHostname();

    // ===============================
    // Hide Django Messages After 5s
    // ===============================
    const ho = document.getElementById("ho");
    if (ho) {
        setTimeout(function () {
            ho.style.transition = 'opacity 0.5s ease';
            ho.style.opacity = '0';
            setTimeout(function () {
                ho.style.display = 'none';
            }, 500);
        }, 5000);
    }

    // ===============================
    // Form Status Messages
    // ===============================
    const formStatus = document.getElementById('formStatus');
    if (formStatus) {
        // Check if there are any messages and display them
        const messages = document.querySelectorAll('.alert');
        if (messages.length > 0) {
            formStatus.classList.add('success');
            formStatus.textContent = messages[0].textContent;
            formStatus.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(function() {
                formStatus.style.transition = 'opacity 0.5s ease';
                formStatus.style.opacity = '0';
                setTimeout(function() {
                    formStatus.style.display = 'none';
                }, 500);
            }, 5000);
        }
    }

    // ===============================
    // MULTI-NAME SELECTION - TAG SYSTEM
    // ===============================
    function addName(field) {
        const select = document.getElementById(field + '_select');
        if (!select) return;
        
        const selectedName = select.value;
        
        if (!selectedName) {
            alert('Please select a staff member first.');
            return;
        }
        
        const hiddenInput = document.getElementById(field);
        const tagsContainer = document.getElementById(field + '_tags');
        
        if (!hiddenInput || !tagsContainer) return;
        
        // Get current names
        let currentNames = hiddenInput.value ? hiddenInput.value.split(', ') : [];
        
        // Check if name already exists
        if (currentNames.includes(selectedName)) {
            alert(selectedName + ' is already added.');
            return;
        }
        
        // Add name
        currentNames.push(selectedName);
        hiddenInput.value = currentNames.join(', ');
        
        // Update tags display
        updateTags(field);
        
        // Reset select
        select.value = '';
    }

    function removeName(field, name) {
        const hiddenInput = document.getElementById(field);
        if (!hiddenInput) return;
        
        let currentNames = hiddenInput.value ? hiddenInput.value.split(', ') : [];
        
        // Remove name
        currentNames = currentNames.filter(n => n !== name);
        hiddenInput.value = currentNames.join(', ');
        
        // Update tags display
        updateTags(field);
    }

    function updateTags(field) {
        const hiddenInput = document.getElementById(field);
        const tagsContainer = document.getElementById(field + '_tags');
        
        if (!hiddenInput || !tagsContainer) return;
        
        const currentNames = hiddenInput.value ? hiddenInput.value.split(', ') : [];
        
        // Clear and rebuild tags
        tagsContainer.innerHTML = '';
        
        if (currentNames.length === 0) {
            tagsContainer.innerHTML = '<span style="color: #999; font-size: 0.75rem; padding: 2px 5px;">No staff selected</span>';
            return;
        }
        
        currentNames.forEach(name => {
            const tag = document.createElement('span');
            tag.className = 'badge bg-secondary d-inline-flex align-items-center gap-1';
            tag.style.cssText = 'padding: 4px 8px; font-size: 0.7rem; margin: 2px; background-color: #6b7280; color: white; border-radius: 4px;';
            tag.innerHTML = `
                ${name}
                <span onclick="removeName('${field}', '${name}')" 
                      style="cursor: pointer; margin-left: 4px; opacity: 0.7; hover: opacity: 1;">
                    <i class="fas fa-times"></i>
                </span>
            `;
            tagsContainer.appendChild(tag);
        });
    }

    // Initialize tags on page load (for edit mode)
    function initializeTags() {
        ['call_attended_by', 'handover_to', 'solved_by'].forEach(function(field) {
            updateTags(field);
        });
    }
    
    // Make functions globally accessible
    window.addName = addName;
    window.removeName = removeName;
    window.updateTags = updateTags;

    // ===============================
    // AUTO-REMOVE RESOLVED ISSUES FROM SLIDER
    // ===============================
    function removeResolvedIssue(issueId) {
        // Find the card with this issue ID
        const card = document.querySelector(`[data-issue-id="${issueId}"]`);
        if (card) {
            // Animate removal
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.8)';
            setTimeout(() => {
                card.remove();
                // Update total count
                updateIssueCount();
                // Refresh slider indicators
                refreshSlider();
                // Update total cards count
                updateTotalCards();
            }, 500);
        }
    }

    function updateIssueCount() {
        const totalSpan = document.querySelector('.ip-info-banner .far.fa-clock');
        if (totalSpan) {
            const remainingCards = document.querySelectorAll('.issue-slider .contact-card').length;
            const parentSpan = totalSpan.closest('span');
            if (parentSpan) {
                parentSpan.textContent = ` Total: ${remainingCards} issue${remainingCards !== 1 ? 's' : ''}`;
            }
        }
    }

    function refreshSlider() {
        // Recalculate slider dimensions
        const slider = document.getElementById('issueSlider');
        if (slider) {
            // Trigger resize event to recalculate
            window.dispatchEvent(new Event('resize'));
        }
    }

    function updateTotalCards() {
        // Update the totalCards variable in the slider
        const slider = document.getElementById('issueSlider');
        if (slider) {
            // The slider will recalculate on next scroll event
            // Dispatch scroll event to trigger recalculation
            slider.dispatchEvent(new Event('scroll'));
        }
    }

    // Listen for messages from the detail page
    window.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'issue_resolved') {
            removeResolvedIssue(event.data.issueId);
        }
    });

    // ===============================
    // ISSUE SLIDER - HORIZONTAL SCROLL
    // ===============================
    function initSlider() {
        const slider = document.getElementById('issueSlider');
        const prevBtn = document.getElementById('sliderPrev');
        const nextBtn = document.getElementById('sliderNext');
        const indicators = document.getElementById('scrollIndicators');
        
        if (!slider) return;
        
        let cardWidth = 0;
        let visibleCards = 0;
        let totalCards = slider.children.length;
        let currentIndex = 0;
        let autoScrollInterval = null;
        let isAutoScrolling = true;
        let isDragging = false;
        let startX = 0;
        let scrollLeft = 0;
        
        // Calculate card width and visible count
        function updateDimensions() {
            const firstCard = slider.querySelector('.contact-card');
            if (!firstCard) return;
            
            const sliderWidth = slider.offsetWidth;
            // Get the actual card width including margins
            const cardStyle = window.getComputedStyle(firstCard);
            const cardWidthWithMargin = firstCard.offsetWidth + 24; // width + gap
            cardWidth = cardWidthWithMargin;
            visibleCards = Math.max(1, Math.floor(sliderWidth / cardWidth));
            
            // Update indicators
            updateIndicators();
        }
        
        // Scroll to a specific index
        function scrollToIndex(index, smooth = true) {
            if (totalCards === 0 || totalCards <= visibleCards) return;
            
            const maxIndex = Math.max(0, totalCards - visibleCards);
            currentIndex = Math.max(0, Math.min(index, maxIndex));
            
            slider.scrollTo({
                left: currentIndex * cardWidth,
                behavior: smooth ? 'smooth' : 'auto'
            });
            
            updateIndicators();
            updateButtons();
        }
        
        // Update indicator dots
        function updateIndicators() {
            if (!indicators) return;
            
            const totalDots = Math.max(1, Math.ceil(totalCards / visibleCards));
            const activeDot = Math.min(Math.floor(currentIndex / visibleCards), totalDots - 1);
            
            indicators.innerHTML = '';
            for (let i = 0; i < totalDots; i++) {
                const dot = document.createElement('span');
                dot.className = 'scroll-dot';
                if (i === activeDot) {
                    dot.classList.add('active');
                }
                dot.addEventListener('click', function() {
                    stopAutoScroll();
                    scrollToIndex(i * visibleCards);
                    startAutoScroll();
                });
                indicators.appendChild(dot);
            }
        }
        
        // Update button states
        function updateButtons() {
            if (totalCards <= visibleCards) {
                if (prevBtn) prevBtn.style.display = 'none';
                if (nextBtn) nextBtn.style.display = 'none';
                return;
            }
            
            if (prevBtn) {
                prevBtn.style.display = 'flex';
                prevBtn.disabled = currentIndex <= 0;
            }
            if (nextBtn) {
                nextBtn.style.display = 'flex';
                const maxIndex = Math.max(0, totalCards - visibleCards);
                nextBtn.disabled = currentIndex >= maxIndex;
            }
        }
        
        // Next slide
        function nextSlide() {
            if (totalCards === 0 || totalCards <= visibleCards) return;
            const maxIndex = Math.max(0, totalCards - visibleCards);
            const newIndex = Math.min(currentIndex + visibleCards, maxIndex);
            scrollToIndex(newIndex);
        }
        
        // Previous slide
        function prevSlide() {
            if (totalCards === 0 || totalCards <= visibleCards) return;
            const newIndex = Math.max(0, currentIndex - visibleCards);
            scrollToIndex(newIndex);
        }
        
        // Auto-scroll functions
        function startAutoScroll() {
            if (!isAutoScrolling) return;
            if (totalCards <= visibleCards) return;
            
            stopAutoScroll();
            autoScrollInterval = setInterval(() => {
                const maxIndex = Math.max(0, totalCards - visibleCards);
                if (currentIndex >= maxIndex) {
                    scrollToIndex(0);
                } else {
                    nextSlide();
                }
            }, 5000);
        }
        
        function stopAutoScroll() {
            if (autoScrollInterval) {
                clearInterval(autoScrollInterval);
                autoScrollInterval = null;
            }
        }
        
        // Event Listeners for buttons
        if (prevBtn) {
            prevBtn.addEventListener('click', function() {
                stopAutoScroll();
                prevSlide();
                startAutoScroll();
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                stopAutoScroll();
                nextSlide();
                startAutoScroll();
            });
        }
        
        // Mouse drag support
        slider.addEventListener('mousedown', function(e) {
            isDragging = true;
            startX = e.pageX - slider.offsetLeft;
            scrollLeft = slider.scrollLeft;
            slider.style.cursor = 'grabbing';
            stopAutoScroll();
        });
        
        slider.addEventListener('mouseleave', function() {
            if (isDragging) {
                isDragging = false;
                slider.style.cursor = 'grab';
                startAutoScroll();
            }
        });
        
        slider.addEventListener('mouseup', function() {
            if (isDragging) {
                isDragging = false;
                slider.style.cursor = 'grab';
                startAutoScroll();
            }
        });
        
        slider.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - slider.offsetLeft;
            const walk = (x - startX) * 1.5;
            slider.scrollLeft = scrollLeft - walk;
        });
        
        // Handle resize
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                updateDimensions();
                scrollToIndex(currentIndex, false);
            }, 200);
        });
        
        // Handle scroll events (for manual scroll)
        let scrollTimeout;
        slider.addEventListener('scroll', function() {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                if (cardWidth > 0) {
                    const newIndex = Math.round(slider.scrollLeft / cardWidth);
                    if (newIndex !== currentIndex) {
                        currentIndex = Math.max(0, Math.min(newIndex, totalCards - visibleCards));
                        updateIndicators();
                        updateButtons();
                    }
                }
            }, 100);
        });
        
        // Touch support for mobile
        let touchStartX = 0;
        let touchEndX = 0;
        
        slider.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
            stopAutoScroll();
        }, { passive: true });
        
        slider.addEventListener('touchmove', function(e) {
            // Allow natural scrolling
        }, { passive: true });
        
        slider.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            const diff = touchStartX - touchEndX;
            
            if (Math.abs(diff) > 50) {
                if (diff > 0) {
                    nextSlide();
                } else {
                    prevSlide();
                }
            }
            startAutoScroll();
        }, { passive: true });
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            // Only if slider is visible and in viewport
            const rect = slider.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
            
            if (!isVisible) return;
            
            if (e.key === 'ArrowRight') {
                e.preventDefault();
                stopAutoScroll();
                nextSlide();
                startAutoScroll();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                stopAutoScroll();
                prevSlide();
                startAutoScroll();
            }
        });
        
        // Pause auto-scroll on hover
        slider.addEventListener('mouseenter', stopAutoScroll);
        slider.addEventListener('mouseleave', startAutoScroll);
        
        // ===============================
        // Add Pause/Play Button for Auto-Scroll
        // ===============================
        const sliderWrapper = document.querySelector('.issue-slider-wrapper');
        if (sliderWrapper && totalCards > visibleCards) {
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'slider-toggle-btn';
            toggleBtn.innerHTML = '<i class="fas fa-pause"></i>';
            toggleBtn.title = 'Pause auto-scroll';
            toggleBtn.style.cssText = `
                position: absolute;
                bottom: 0;
                right: 20px;
                z-index: 10;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 50%;
                width: 32px;
                height: 32px;
                cursor: pointer;
                color: #2563eb;
                font-size: 0.8rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            `;
            
            toggleBtn.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.1)';
                this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.15)';
            });
            
            toggleBtn.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            });
            
            let isPaused = false;
            toggleBtn.addEventListener('click', function() {
                isPaused = !isPaused;
                if (isPaused) {
                    stopAutoScroll();
                    this.innerHTML = '<i class="fas fa-play"></i>';
                    this.title = 'Resume auto-scroll';
                    this.style.color = '#dc2626';
                } else {
                    startAutoScroll();
                    this.innerHTML = '<i class="fas fa-pause"></i>';
                    this.title = 'Pause auto-scroll';
                    this.style.color = '#2563eb';
                }
            });
            
            sliderWrapper.appendChild(toggleBtn);
        }
        
        // Initialize
        setTimeout(() => {
            updateDimensions();
            scrollToIndex(0, false);
            // Start auto-scroll after a delay
            setTimeout(() => {
                startAutoScroll();
            }, 2000);
        }, 100);
        
        // Update on window focus (for when user returns to tab)
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                updateDimensions();
                scrollToIndex(currentIndex, false);
            }
        });
    }
    
    // Initialize the slider
    initSlider();

    // ===============================
    // Initialize Tags on Page Load
    // ===============================
    initializeTags();

    // ===============================
    // Smooth Scroll to Form on Error
    // ===============================
    const form = document.getElementById('contactform');
    if (form) {
        // Check if there are error messages
        const errorMessages = document.querySelectorAll('.alert-danger');
        if (errorMessages.length > 0) {
            const formElement = document.getElementById('contactform');
            if (formElement) {
                setTimeout(() => {
                    formElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 500);
            }
        }
    }

    // ===============================
    // Form Validation - Real-time
    // ===============================
    const inputs = document.querySelectorAll('.input-icon input, .input-icon select, .input-icon textarea');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.hasAttribute('required') && this.value.trim() === '') {
                this.style.borderColor = '#dc2626';
                this.style.boxShadow = '0 0 0 4px rgba(220, 38, 38, 0.1)';
            } else if (this.hasAttribute('required') && this.value.trim() !== '') {
                this.style.borderColor = '#16a34a';
                this.style.boxShadow = '0 0 0 4px rgba(22, 163, 74, 0.1)';
            }
        });
        
        input.addEventListener('focus', function() {
            this.style.borderColor = '#2563eb';
            this.style.boxShadow = '0 0 0 4px rgba(37, 99, 235, 0.1)';
        });
    });

    // ===============================
    // Phone Input Formatting (Optional)
    // ===============================
    const phoneInput = document.getElementById('phone1');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            // Remove non-numeric characters
            this.value = this.value.replace(/[^0-9+]/g, '');
        });
    }

    console.log('Contact page functionality loaded - Peaceful Boys Hostel');
});