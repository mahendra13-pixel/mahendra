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

// ===============================
// VIDEO UPLOAD - Edit page
// ===============================
function updateVideoLabelEdit(input) {
    const fileNameSpan = document.getElementById('videoFileNameEdit');
    if (input.files && input.files.length > 0) {
        fileNameSpan.textContent = '🎬 ' + input.files[0].name;
    } else {
        fileNameSpan.textContent = '';
    }
}

// ===============================
// MEDIA UPLOAD - Contact form
// ===============================
function updateMediaLabel(input) {
    const fileNameSpan = document.getElementById('mediaFileName');
    if (input.files && input.files.length > 0) {
        const file = input.files[0];
        const fileType = file.type.startsWith('video/') ? '🎬' : '🖼️';
        fileNameSpan.textContent = fileType + ' ' + file.name;
    } else {
        fileNameSpan.textContent = '';
    }
}

// ===============================
// MEDIA UPLOAD - Edit page (All file types)
// ===============================
function updateMediaLabelEdit(input) {
    const fileNameSpan = document.getElementById('mediaFileNameEdit');
    if (input.files && input.files.length > 0) {
        const file = input.files[0];
        const fileType = file.type.startsWith('video/') ? '🎬' : 
                        file.type.startsWith('image/') ? '🖼️' :
                        file.type.startsWith('application/pdf') ? '📄' :
                        '📎';
        fileNameSpan.textContent = fileType + ' ' + file.name;
    } else {
        fileNameSpan.textContent = '';
    }
}

// ===============================
// MULTIPLE FILE ATTACHMENT - Compact Version
// ===============================

let selectedFiles = [];
let totalFileSize = 0;
const MAX_SIZE = 100 * 1024 * 1024; // 100 MB

function handleMultipleFiles(input) {
    const files = input.files;
    const fileListContainer = document.getElementById('fileListContainer');
    const fileCountDisplay = document.getElementById('fileCountDisplay');
    const fileCountText = document.getElementById('fileCountText');
    
    if (!files || files.length === 0) return;
    
    // Calculate total size
    let newTotalSize = totalFileSize;
    for (let i = 0; i < files.length; i++) {
        newTotalSize += files[i].size;
    }
    
    // Check if exceeds 100 MB limit
    if (newTotalSize > MAX_SIZE) {
        alert(`Total file size (${formatFileSize(newTotalSize)}) exceeds the 100 MB limit!`);
        input.value = '';
        return;
    }
    
    // Add files to selected list (avoid duplicates)
    for (let i = 0; i < files.length; i++) {
        const exists = selectedFiles.some(f => f.name === files[i].name && f.size === files[i].size);
        if (!exists) {
            selectedFiles.push(files[i]);
            totalFileSize += files[i].size;
        }
    }
    
    // Update UI
    updateFileListUI();
    
    // Show file count
    fileCountDisplay.style.display = 'inline-block';
    const count = selectedFiles.length;
    fileCountText.textContent = count === 1 ? '1 file selected' : `${count} files selected`;
    
    // Show file list
    if (selectedFiles.length > 0) {
        fileListContainer.style.display = 'block';
        renderFileList();
    }
    
    // Reset input
    input.value = '';
}

function renderFileList() {
    const container = document.getElementById('fileListContainer');
    container.innerHTML = '';
    
    if (selectedFiles.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    // Show first 5 files
    const maxShow = 5;
    const showFiles = selectedFiles.slice(0, maxShow);
    
    showFiles.forEach((file, index) => {
        const div = document.createElement('div');
        div.style.cssText = 'display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px solid #f3f4f6; font-size: 0.65rem;';
        const icon = getFileIcon(file.name);
        div.innerHTML = `
            <span><i class="${icon}" style="color: #6b7280; width: 14px;"></i> ${file.name}</span>
            <span style="color: #6b7280;">${formatFileSize(file.size)}</span>
        `;
        container.appendChild(div);
    });
    
    if (selectedFiles.length > maxShow) {
        const more = document.createElement('div');
        more.style.cssText = 'padding: 2px 0; font-size: 0.65rem; color: #6b7280;';
        more.textContent = `+ ${selectedFiles.length - maxShow} more file(s)`;
        container.appendChild(more);
    }
}

function updateFileListUI() {
    const fileCountDisplay = document.getElementById('fileCountDisplay');
    const fileCountText = document.getElementById('fileCountText');
    const fileListContainer = document.getElementById('fileListContainer');
    
    if (selectedFiles.length === 0) {
        fileCountDisplay.style.display = 'none';
        fileListContainer.style.display = 'none';
        fileListContainer.innerHTML = '';
        return;
    }
    
    fileCountDisplay.style.display = 'inline-block';
    const count = selectedFiles.length;
    fileCountText.textContent = count === 1 ? '1 file selected' : `${count} files selected`;
    
    renderFileList();
}

function removeFile(index) {
    if (index >= 0 && index < selectedFiles.length) {
        totalFileSize -= selectedFiles[index].size;
        selectedFiles.splice(index, 1);
        updateFileListUI();
    }
}

function clearAllFiles() {
    if (selectedFiles.length === 0) return;
    if (!confirm(`Remove all ${selectedFiles.length} files?`)) return;
    
    selectedFiles = [];
    totalFileSize = 0;
    updateFileListUI();
    
    document.getElementById('fileCountDisplay').style.display = 'none';
    document.getElementById('fileListContainer').style.display = 'none';
    document.getElementById('fileListContainer').innerHTML = '';
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': 'fas fa-file-pdf',
        'doc': 'fas fa-file-word',
        'docx': 'fas fa-file-word',
        'xls': 'fas fa-file-excel',
        'xlsx': 'fas fa-file-excel',
        'ppt': 'fas fa-file-powerpoint',
        'pptx': 'fas fa-file-powerpoint',
        'jpg': 'fas fa-file-image',
        'jpeg': 'fas fa-file-image',
        'png': 'fas fa-file-image',
        'gif': 'fas fa-file-image',
        'mp4': 'fas fa-file-video',
        'avi': 'fas fa-file-video',
        'mkv': 'fas fa-file-video',
        'mp3': 'fas fa-file-audio',
        'wav': 'fas fa-file-audio',
        'zip': 'fas fa-file-archive',
        'rar': 'fas fa-file-archive',
        'txt': 'fas fa-file-alt',
        'py': 'fas fa-file-code',
        'html': 'fas fa-file-code',
        'css': 'fas fa-file-code',
        'js': 'fas fa-file-code',
        'json': 'fas fa-file-code',
    };
    return icons[ext] || 'fas fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}







// ============================================
// AUTOCOMPLETE - Message & Remarks Fields
// Only shows top 3 suggestions
// With RIGHT SIDE positioning & KEYBOARD navigation
// ============================================

let suggestionTimeout;
let currentSuggestionIndex = -1;
let currentSuggestionsList = [];
let currentFieldName = '';

function showAutoSuggest(input, suggestionId, fieldName) {
    const value = input.value.trim();
    const suggestionsDiv = document.getElementById(suggestionId);
    
    if (!suggestionsDiv) return;
    
    // Reset keyboard index
    currentSuggestionIndex = -1;
    currentFieldName = fieldName;
    
    clearTimeout(suggestionTimeout);
    
    if (value.length < 1) {
        suggestionsDiv.style.display = 'none';
        suggestionsDiv.innerHTML = '';
        currentSuggestionsList = [];
        return;
    }
    
    suggestionTimeout = setTimeout(function() {
        fetchAutoSuggestions(value, suggestionsDiv, fieldName);
    }, 300);
}

function fetchAutoSuggestions(query, suggestionsDiv, fieldName) {
    fetch(`/autocomplete/?field=${fieldName}&q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.suggestions.length > 0) {
                const suggestions = data.suggestions.slice(0, 3);
                currentSuggestionsList = suggestions;
                
                let html = '';
                suggestions.forEach(function(item, index) {
                    const safeItem = item.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    html += `<div class="suggestion-item" data-index="${index}" onclick="selectSuggestion('${fieldName}', '${safeItem}', ${index})">
                                <i class="fas fa-history"></i>
                                <span class="suggestion-text">${highlightMatch(item, query)}</span>
                            </div>`;
                });
                suggestionsDiv.innerHTML = html;
                suggestionsDiv.style.display = 'block';
                currentSuggestionIndex = -1;
                currentFieldName = fieldName;
            } else {
                suggestionsDiv.style.display = 'none';
                suggestionsDiv.innerHTML = '';
                currentSuggestionsList = [];
                currentSuggestionIndex = -1;
            }
        })
        .catch(() => {
            suggestionsDiv.style.display = 'none';
            suggestionsDiv.innerHTML = '';
            currentSuggestionsList = [];
            currentSuggestionIndex = -1;
        });
}

function selectSuggestion(fieldName, value, index) {
    const textarea = document.getElementById(fieldName);
    if (textarea) {
        textarea.value = value;
        textarea.dispatchEvent(new Event('input'));
        textarea.dispatchEvent(new Event('change'));
        
        const suggestionsDiv = document.getElementById(fieldName + '-suggestions');
        if (suggestionsDiv) {
            suggestionsDiv.style.display = 'none';
            suggestionsDiv.innerHTML = '';
        }
        currentSuggestionsList = [];
        currentSuggestionIndex = -1;
        currentFieldName = '';
        
        textarea.dispatchEvent(new Event('change'));
    }
}

function highlightMatch(text, query) {
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<strong>$1</strong>');
}

// ============================================
// KEYBOARD NAVIGATION - Up/Down/Left/Right + Enter
// ============================================

// ✅ Use a separate event listener with capture phase
document.addEventListener('keydown', function(e) {
    // Get the active element (textarea that triggered suggestions)
    const activeElement = document.activeElement;
    
    // Check if the active element is the message or remarks textarea
    const isMessageField = activeElement && activeElement.id === 'message';
    const isRemarksField = activeElement && activeElement.id === 'remarks';
    
    // Only proceed if we're in the message or remarks field
    if (!isMessageField && !isRemarksField) {
        // Still handle Escape to close any open suggestions
        if (e.key === 'Escape') {
            document.querySelectorAll('.autocomplete-suggestions').forEach(function(div) {
                div.style.display = 'none';
                div.innerHTML = '';
            });
            currentSuggestionsList = [];
            currentSuggestionIndex = -1;
        }
        return;
    }
    
    // Determine which field we're in
    const fieldName = isMessageField ? 'message' : 'remarks';
    const suggestionsDiv = document.getElementById(fieldName + '-suggestions');
    
    // If suggestions not visible, only handle Escape
    if (!suggestionsDiv || suggestionsDiv.style.display !== 'block') {
        if (e.key === 'Escape') {
            suggestionsDiv.style.display = 'none';
            suggestionsDiv.innerHTML = '';
            currentSuggestionsList = [];
            currentSuggestionIndex = -1;
        }
        return;
    }
    
    const items = suggestionsDiv.querySelectorAll('.suggestion-item');
    if (items.length === 0) return;
    
    // ✅ UP Arrow
    if (e.key === 'ArrowUp') {
        e.preventDefault();
        e.stopPropagation();
        currentSuggestionIndex = (currentSuggestionIndex - 1 + items.length) % items.length;
        updateActiveItem(items, suggestionsDiv);
        return;
    }
    
    // ✅ DOWN Arrow
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        e.stopPropagation();
        currentSuggestionIndex = (currentSuggestionIndex + 1) % items.length;
        updateActiveItem(items, suggestionsDiv);
        return;
    }
    
    // ✅ LEFT Arrow - Cycle to previous (same as Up)
    if (e.key === 'ArrowLeft') {
        e.preventDefault();
        e.stopPropagation();
        currentSuggestionIndex = (currentSuggestionIndex - 1 + items.length) % items.length;
        updateActiveItem(items, suggestionsDiv);
        return;
    }
    
    // ✅ RIGHT Arrow - Cycle to next (same as Down)
    if (e.key === 'ArrowRight') {
        e.preventDefault();
        e.stopPropagation();
        currentSuggestionIndex = (currentSuggestionIndex + 1) % items.length;
        updateActiveItem(items, suggestionsDiv);
        return;
    }
    
    // ✅ ENTER key - select current item
    if (e.key === 'Enter' && currentSuggestionIndex >= 0 && currentSuggestionIndex < items.length) {
        e.preventDefault();
        e.stopPropagation();
        const activeItem = items[currentSuggestionIndex];
        if (activeItem) {
            activeItem.click();
        }
        return;
    }
    
    // ✅ ESCAPE key - close suggestions
    if (e.key === 'Escape') {
        e.preventDefault();
        suggestionsDiv.style.display = 'none';
        suggestionsDiv.innerHTML = '';
        currentSuggestionsList = [];
        currentSuggestionIndex = -1;
        return;
    }
});

function updateActiveItem(items, suggestionsDiv) {
    // Remove active class from all items
    items.forEach(item => item.classList.remove('active'));
    
    // Add active class to current item
    if (currentSuggestionIndex >= 0 && currentSuggestionIndex < items.length) {
        items[currentSuggestionIndex].classList.add('active');
        
        // Scroll to make sure the active item is visible
        items[currentSuggestionIndex].scrollIntoView({
            block: 'nearest',
            behavior: 'smooth'
        });
    }
    // ✅ NO TIMER - Blue stays permanently until user selects or closes
}

// Close suggestions when clicking outside
document.addEventListener('click', function(e) {
    const isClickInside = e.target.closest('.autocomplete-wrapper') || 
                          e.target.closest('.autocomplete-suggestions');
    if (!isClickInside) {
        document.querySelectorAll('.autocomplete-suggestions').forEach(function(div) {
            div.style.display = 'none';
            div.innerHTML = '';
        });
        currentSuggestionsList = [];
        currentSuggestionIndex = -1;
        currentFieldName = '';
    }
});

// Close suggestions on form submission
document.addEventListener('submit', function(e) {
    document.querySelectorAll('.autocomplete-suggestions').forEach(function(div) {
        div.style.display = 'none';
        div.innerHTML = '';
    });
    currentSuggestionsList = [];
    currentSuggestionIndex = -1;
    currentFieldName = '';
});