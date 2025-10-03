// HAVEN - Mental Health Platform JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add floating animation to cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    // Observe all haven cards
    document.querySelectorAll('.haven-card').forEach(card => {
        observer.observe(card);
    });

    // Add click animations to buttons
    document.querySelectorAll('.btn-haven').forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Add typing animation to text elements
    function typeWriter(element, text, speed = 50) {
        let i = 0;
        element.innerHTML = '';
        
        function type() {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        
        type();
    }

    // Initialize typing animation for motivation text
    const motivationText = document.querySelector('.motivation-text');
    if (motivationText) {
        const originalText = motivationText.textContent;
        typeWriter(motivationText, originalText, 30);
    }

    // Add parallax effect to background
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const parallax = document.querySelector('.auth-container');
        if (parallax) {
            const speed = scrolled * 0.5;
            parallax.style.transform = `translateY(${speed}px)`;
        }
    });

    // Add floating animation to decorative elements
    function addFloatingAnimation() {
        const floatingElements = document.querySelectorAll('.decorative-icons i');
        floatingElements.forEach((element, index) => {
            element.style.animationDelay = `${index * 0.2}s`;
            element.style.animationDuration = `${3 + index * 0.5}s`;
        });
    }

    addFloatingAnimation();

    // Add hover effects to feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });

    // Add mood rating stars interaction
    document.querySelectorAll('.mood-rating').forEach(rating => {
        const stars = rating.querySelectorAll('.star');
        stars.forEach((star, index) => {
            star.addEventListener('click', function() {
                // Update visual state
                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.add('active');
                    } else {
                        s.classList.remove('active');
                    }
                });
                
                // Update hidden input
                const hiddenInput = rating.querySelector('input[type="hidden"]');
                if (hiddenInput) {
                    hiddenInput.value = index + 1;
                }
            });
            
            star.addEventListener('mouseenter', function() {
                stars.forEach((s, i) => {
                    if (i <= index) {
                        s.classList.add('hover');
                    } else {
                        s.classList.remove('hover');
                    }
                });
            });
        });
        
        rating.addEventListener('mouseleave', function() {
            const stars = this.querySelectorAll('.star');
            stars.forEach(star => star.classList.remove('hover'));
        });
    });

    // Add progress bar animation
    function animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const width = bar.getAttribute('aria-valuenow');
            bar.style.width = '0%';
            setTimeout(() => {
                bar.style.width = width + '%';
            }, 500);
        });
    }

    // Initialize progress bars when they come into view
    const progressObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateProgressBars();
                progressObserver.unobserve(entry.target);
            }
        });
    });

    document.querySelectorAll('.progress').forEach(progress => {
        progressObserver.observe(progress);
    });

    // Add notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
    });

    // Add theme toggle functionality
    function toggleTheme() {
        const body = document.body;
        const currentTheme = body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('haven-theme', newTheme);
        
        showNotification(`Switched to ${newTheme} theme`, 'success');
    }

    // Load saved theme
    const savedTheme = localStorage.getItem('haven-theme');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
    }

    // Add accessibility improvements
    function improveAccessibility() {
        // Add skip link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link position-absolute';
        skipLink.style.cssText = 'top: -40px; left: 6px; z-index: 10000; padding: 8px; background: var(--haven-primary); color: var(--haven-dark); text-decoration: none; border-radius: 4px;';
        
        skipLink.addEventListener('focus', function() {
            this.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', function() {
            this.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Add main content ID
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.id = 'main-content';
        }
    }

    improveAccessibility();

    // Add performance monitoring
    function monitorPerformance() {
        if ('performance' in window) {
            window.addEventListener('load', function() {
                setTimeout(function() {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                    
                    if (loadTime > 3000) {
                        console.warn('Page load time is slow:', loadTime + 'ms');
                    }
                }, 0);
            });
        }
    }

    monitorPerformance();

    // Add error handling for AJAX requests
    function handleAjaxError(xhr, status, error) {
        console.error('AJAX Error:', status, error);
        showNotification('Something went wrong. Please try again.', 'danger');
    }

    // Global error handler
    window.addEventListener('error', function(e) {
        console.error('Global Error:', e.error);
        showNotification('An unexpected error occurred. Please refresh the page.', 'danger');
    });

    // Add offline detection
    window.addEventListener('online', function() {
        showNotification('You are back online!', 'success');
    });

    window.addEventListener('offline', function() {
        showNotification('You are offline. Some features may not work.', 'warning');
    });

    // Initialize all components
    console.log('HAVEN platform initialized successfully! 🌟');
});

// Utility functions
const HavenUtils = {
    // Format date
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    // Format time
    formatTime: function(time) {
        return new Date(time).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // Generate random cheerful username
    generateCheerfulUsername: function() {
        const positiveWords = ['Calm', 'Joyful', 'Bright', 'Happy', 'Peaceful', 'Serene'];
        const natureWords = ['Star', 'Moon', 'Flower', 'Tree', 'River', 'Ocean'];
        const firstWord = positiveWords[Math.floor(Math.random() * positiveWords.length)];
        const secondWord = natureWords[Math.floor(Math.random() * natureWords.length)];
        const number = Math.floor(Math.random() * 999) + 1;
        return `${firstWord}${secondWord}${number}`;
    }
};

// Export for use in other scripts
window.HavenUtils = HavenUtils;
