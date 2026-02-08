// Auth page enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Add floating animation to form inputs
    const inputs = document.querySelectorAll('.form-input');
    
    inputs.forEach(input => {
        // Add focus effect
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });

    // Password strength indicator (for register page)
    const passwordInput = document.querySelector('#password1');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const requirementsEl = document.querySelector('.password-requirements small');
            
            if (password.length === 0) {
                requirementsEl.textContent = 'Password must contain at least 8 characters';
                requirementsEl.style.color = 'var(--text-muted)';
            } else if (password.length < 8) {
                requirementsEl.textContent = 'Password too short';
                requirementsEl.style.color = 'var(--danger)';
            } else {
                requirementsEl.textContent = 'Password strength: Good';
                requirementsEl.style.color = 'var(--success)';
            }
        });
    }

    // Animate feature items on scroll (for info card)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateX(0)';
            }
        });
    }, observerOptions);

    const featureItems = document.querySelectorAll('.feature-item');
    featureItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        item.style.transition = `all 0.5s ease ${index * 0.1}s`;
        observer.observe(item);
    });

    // Form submission loading state
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('.btn-primary');
            const originalText = submitBtn.querySelector('span').textContent;
            
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.7';
            submitBtn.querySelector('span').textContent = 'Processing...';
            
            // Re-enable after 3 seconds if form doesn't submit
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
                submitBtn.querySelector('span').textContent = originalText;
            }, 3000);
        });
    });
});