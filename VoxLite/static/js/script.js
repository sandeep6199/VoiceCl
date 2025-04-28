// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize page loader
    initPageLoader();
    
    // Initialize header scroll effects
    initHeaderScroll();
    
    // Initialize mobile nav
    initMobileNav();
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize modals
    initModals();
    
    // Initialize FAQ accordions
    initFaqAccordion();
    
    // Initialize form validation
    initFormValidation();
    
    // Hero animation
    animateHero();
    
    // Initialize stats animation
    initStatsAnimation();
    
    // Initialize scroll to top button
    initScrollToTop();
});

// Page loader with elegant fade
function initPageLoader() {
    const pageLoader = document.querySelector('.page-loader');
    if (pageLoader) {
        setTimeout(() => {
            pageLoader.style.opacity = '0';
            setTimeout(() => {
                pageLoader.style.display = 'none';
            }, 500);
        }, 800);
    }
}

// Header scroll effects
function initHeaderScroll() {
    const header = document.querySelector('.header');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        // Add active class to nav links based on section visibility
        const sections = document.querySelectorAll('section[id]');
        const scrollPosition = window.scrollY + 100;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                document.querySelector(`.nav-list a[href="#${sectionId}"]`)?.classList.add('active');
            } else {
                document.querySelector(`.nav-list a[href="#${sectionId}"]`)?.classList.remove('active');
            }
        });
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('.nav-list a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (this.getAttribute('href') === '#') return;
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                // Close mobile menu if open
                document.querySelector('.nav-list').classList.remove('active');
                document.querySelector('.header-actions')?.classList.remove('active');
                document.querySelector('.menu-toggle')?.classList.remove('active');
                document.body.classList.remove('menu-open');
                
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Mobile Navigation
function initMobileNav() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navList = document.querySelector('.nav-list');
    const headerActions = document.querySelector('.header-actions');
    
    if (menuToggle && navList) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            navList.classList.toggle('active');
            headerActions?.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (navList.classList.contains('active') && 
                !navList.contains(e.target) && 
                !menuToggle.contains(e.target)) {
                
                menuToggle.classList.remove('active');
                navList.classList.remove('active');
                headerActions?.classList.remove('active');
                document.body.classList.remove('menu-open');
            }
        });
    }
}

// Intersection Observer for scroll animations
function initScrollAnimations() {
    // Initialize animations for various elements
    const animatedElements = document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .scale-in, .stagger-children, .section-header, .stats, .stats-wrapper');
    
    const options = {
        root: null,
        threshold: 0.15,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                
                // If it's a stagger container, animate children with delays
                if (entry.target.classList.contains('stagger-children')) {
                    const children = entry.target.children;
                    Array.from(children).forEach((child, index) => {
                        setTimeout(() => {
                            child.style.opacity = '1';
                            child.style.transform = 'translateY(0)';
                        }, 100 * index);
                    });
                }
                
                observer.unobserve(entry.target);
            }
        });
    }, options);
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
    
    // Add section header animations for all section headers
    const sectionHeaders = document.querySelectorAll('.section-header');
    sectionHeaders.forEach(header => {
        if (!Array.from(animatedElements).includes(header)) {
            observer.observe(header);
        }
    });
    
    // Enhanced animations for individual cards
    const cards = document.querySelectorAll('.industry-card, .feature-block, .pricing-card');
    const cardsObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100 * (index % 4)); // Stagger based on position within row
                cardsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
        cardsObserver.observe(card);
    });
}

// Modern minimal hero animation
function animateHero() {
    const heroElements = [
        document.querySelector('.hero-badge'),
        document.querySelector('.hero-title'),
        document.querySelector('.hero-description'),
        document.querySelector('.hero-cta')
    ];
    
    const heroVisual = document.querySelector('.hero-visualization');
    
    // Initial state
    heroElements.forEach(el => {
        if (el) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
        }
    });
    
    if (heroVisual) {
        heroVisual.style.opacity = '0';
        heroVisual.style.transform = 'translateY(30px)';
    }
    
    // Animate in sequence
    let delay = 200;
    heroElements.forEach((el, index) => {
        if (el) {
            setTimeout(() => {
                el.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, delay + (index * 150));
        }
    });
    
    if (heroVisual) {
        setTimeout(() => {
            heroVisual.style.transition = 'opacity 1s ease, transform 1s ease';
            heroVisual.style.opacity = '1';
            heroVisual.style.transform = 'translateY(0)';
        }, delay + 800);
    }
}

// FAQ Accordion
function initFaqAccordion() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        if (question) {
            question.addEventListener('click', () => {
                // Close other items
                faqItems.forEach(otherItem => {
                    if (otherItem !== item && otherItem.classList.contains('active')) {
                        otherItem.classList.remove('active');
                    }
                });
                
                // Toggle current item
                item.classList.toggle('active');
            });
        }
    });
}

// Modal functionality
function initModals() {
    // Modal triggers
    const modalTriggers = {
        'login-btn': '.login-modal',
        'register-btn': '.register-modal',
        'try-demo-btn': '.demo-modal'
    };
    
    // Open modals
    for (const triggerId in modalTriggers) {
        const trigger = document.getElementById(triggerId);
        const modalSelector = modalTriggers[triggerId];
        const modal = document.querySelector(modalSelector);
        
        if (trigger && modal) {
            trigger.addEventListener('click', () => {
                openModal(modal);
            });
        }
    }
    
    // Switch between login and register
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    const loginModal = document.querySelector('.login-modal');
    const registerModal = document.querySelector('.register-modal');
    
    if (showRegisterLink && registerModal) {
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            closeModal(loginModal);
            setTimeout(() => {
                openModal(registerModal);
            }, 300);
        });
    }
    
    if (showLoginLink && loginModal) {
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            closeModal(registerModal);
            setTimeout(() => {
                openModal(loginModal);
            }, 300);
        });
    }
    
    // Close modals via close button
    document.querySelectorAll('.close-modal').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            const modal = closeBtn.closest('.modal');
            if (modal) {
                closeModal(modal);
            }
        });
    });
    
    // Close modals via outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });
    
    // Password toggle visibility
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const passwordField = toggle.previousElementSibling;
            const icon = toggle.querySelector('i');
            
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordField.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
    
    // Helper functions for modal management
    function openModal(modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        setTimeout(() => {
            modal.classList.add('active');
        }, 10);
    }
    
    function closeModal(modal) {
        modal.classList.remove('active');
        
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }, 300);
    }
}

// Form validation
function initFormValidation() {
    const contactForm = document.querySelector('.contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            let valid = true;
            const requiredFields = contactForm.querySelectorAll('[required]');
            
            // Validate required fields
            requiredFields.forEach(field => {
                removeError(field);
                
                if (!field.value.trim()) {
                    showError(field, 'This field is required');
                    valid = false;
                } else if (field.type === 'email' && !isValidEmail(field.value)) {
                    showError(field, 'Please enter a valid email address');
                    valid = false;
                }
            });
            
            if (valid) {
                // Show success message
                const formContent = contactForm.innerHTML;
                
                contactForm.innerHTML = `
                    <div class="success-message">
                        <div class="success-icon">
                            <i class="fas fa-check"></i>
                        </div>
                        <h3>Message Sent!</h3>
                        <p>Thank you for contacting us. We'll get back to you soon.</p>
                    </div>
                `;
                
                // Reset form after delay
                setTimeout(() => {
                    contactForm.innerHTML = formContent;
                    contactForm.reset();
                    initFormValidation();
                }, 5000);
            }
        });
    }
    
    // Password strength meter
    const passwordInput = document.getElementById('register-password');
    const strengthIndicator = document.querySelector('.password-strength');
    
    if (passwordInput && strengthIndicator) {
        passwordInput.addEventListener('input', () => {
            const password = passwordInput.value;
            let strength = 0;
            
            if (password.length >= 8) strength += 1;
            if (/[A-Z]/.test(password)) strength += 1;
            if (/[0-9]/.test(password)) strength += 1;
            if (/[^A-Za-z0-9]/.test(password)) strength += 1;
            
            strengthIndicator.className = 'password-strength';
            
            if (password.length === 0) {
                strengthIndicator.style.width = '0%';
            } else if (strength <= 1) {
                strengthIndicator.classList.add('weak');
                strengthIndicator.style.width = '25%';
            } else if (strength === 2) {
                strengthIndicator.classList.add('medium');
                strengthIndicator.style.width = '50%';
            } else if (strength === 3) {
                strengthIndicator.classList.add('medium');
                strengthIndicator.style.width = '75%';
            } else {
                strengthIndicator.classList.add('strong');
                strengthIndicator.style.width = '100%';
            }
        });
    }
    
    // Helper functions
    function showError(field, message) {
        const parent = field.parentElement;
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        
        field.classList.add('error');
        parent.appendChild(errorElement);
    }
    
    function removeError(field) {
        const parent = field.parentElement;
        const errorElement = parent.querySelector('.error-message');
        
        if (errorElement) {
            errorElement.remove();
        }
        
        field.classList.remove('error');
    }
    
    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
}

// Play button click
document.addEventListener('click', (e) => {
    if (e.target.closest('.play-btn')) {
        e.preventDefault();
        alert('Video demo feature would play here');
    }
});

// Learn more button
document.getElementById('learn-more-btn')?.addEventListener('click', () => {
    const featuresSection = document.getElementById('features');
    if (featuresSection) {
        window.scrollTo({
            top: featuresSection.offsetTop - 80,
            behavior: 'smooth'
        });
    }
});

// Stats Animation with enhanced transitions
function initStatsAnimation() {
    const statItems = document.querySelectorAll('.stat-item');
    
    // Define percentages for circle animations
    // Some values (like 3min or 15ms) need custom percentages to look good visually
    const circlePercentages = {
        '98%': 98,  // 98% accuracy = 98% of circle
        '3min': 60, // 3min = 60% of circle
        '15ms': 75, // 15ms = 75% of circle
        '60%': 60   // 60% less power = 60% of circle
    };
    
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                const item = entry.target;
                // Make sure the parent stats sections are visible
                document.querySelector('.stats').classList.add('visible');
                document.querySelector('.stats-wrapper').classList.add('visible');
                
                const valueDisplay = item.querySelector('.stat-value');
                const circle = item.querySelector('.stat-circle-progress');
                
                // Get data from attributes
                const value = item.getAttribute('data-value');
                const unit = item.getAttribute('data-unit');
                const finalText = value + unit;
                
                // Set starting values
                let currentValue = 0;
                valueDisplay.textContent = '0' + unit;
                
                // Calculate the circle animation percentage
                let circlePercentage;
                if (unit === '%') {
                    circlePercentage = parseInt(value);
                } else if (unit === 'min') {
                    circlePercentage = 60; // 3min = 60% filled
                } else if (unit === 'ms') {
                    circlePercentage = 75; // 15ms = 75% filled
                }
                
                // Calculate the strokeDashoffset
                const circumference = 2 * Math.PI * 60; // 2πr where r=60
                const offsetStart = circumference;
                const offsetEnd = circumference - (circumference * circlePercentage / 100);
                
                // Add animated class with staggered delay and enhanced easing
                const index = Array.from(statItems).indexOf(item);
                setTimeout(() => {
                    item.classList.add('animated');
                    
                    // Animate the circle
                    // Use requestAnimationFrame for smoother animation
                    const startTime = performance.now();
                    const duration = 1500; // ms
                    
                    function animateCircle(timestamp) {
                        const elapsed = timestamp - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        
                        // Cubic bezier easing
                        const easedProgress = 1 - Math.pow(1 - progress, 3);
                        
                        // Calculate current offset
                        const currentOffset = offsetStart - (offsetStart - offsetEnd) * easedProgress;
                        circle.style.strokeDashoffset = currentOffset;
                        
                        if (progress < 1) {
                            requestAnimationFrame(animateCircle);
                        }
                    }
                    
                    requestAnimationFrame(animateCircle);
                    
                    // Animate the counter with cubic easing
                    const counterStartTime = performance.now();
                    const counterDuration = 2000; // ms
                    const targetValue = parseInt(value);
                    
                    function updateCounter(timestamp) {
                        const elapsed = timestamp - counterStartTime;
                        const progress = Math.min(elapsed / counterDuration, 1);
                        
                        // Use cubic easing for smoother animation
                        const easedProgress = 1 - Math.pow(1 - progress, 3);
                        
                        currentValue = Math.floor(targetValue * easedProgress);
                        valueDisplay.textContent = currentValue + unit;
                        
                        if (progress < 1) {
                            requestAnimationFrame(updateCounter);
                        } else {
                            valueDisplay.textContent = finalText;
                            
                            // Add subtle bounce effect at the end
                            if (circle) {
                                circle.animate([
                                    { transform: 'scale(1.05)' },
                                    { transform: 'scale(1)' }
                                ], {
                                    duration: 300,
                                    easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)'
                                });
                            }
                        }
                    }
                    
                    requestAnimationFrame(updateCounter);
                }, index * 200);
                
                statsObserver.unobserve(item);
            }
        });
    }, { threshold: 0.2 });
    
    statItems.forEach(item => {
        statsObserver.observe(item);
    });
}

// Scroll to top button functionality
const scrollToTopButton = document.getElementById('scroll-to-top');

function toggleScrollToTopButton() {
    if (window.scrollY > 500) {
        scrollToTopButton.classList.add('visible');
    } else {
        scrollToTopButton.classList.remove('visible');
    }
}

// Check button visibility on page load
document.addEventListener('DOMContentLoaded', toggleScrollToTopButton);

// Check button visibility on scroll
window.addEventListener('scroll', toggleScrollToTopButton);

// Scroll to top when button is clicked
scrollToTopButton.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}); 