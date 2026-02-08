// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Update current time
    function updateTime() {
        const timeEl = document.getElementById('currentTime');
        if (timeEl) {
            const now = new Date();
            const options = { 
                weekday: 'short', 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            timeEl.textContent = now.toLocaleDateString('en-US', options);
        }
    }
    
    updateTime();
    setInterval(updateTime, 60000); // Update every minute

    // Animate cards on load
    const cards = document.querySelectorAll('.card, .search-card, .forecast-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Search form enhancement
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('.search-btn');
            const originalText = submitBtn.querySelector('span').textContent;
            
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.7';
            submitBtn.querySelector('span').textContent = 'Searching...';
            
            // Animation will continue as form submits
        });
    }

    // Alert action buttons
    const alertActionBtns = document.querySelectorAll('.alert-action-btn');
    alertActionBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            // Create a simple dropdown menu
            alert('Alert actions coming soon!');
        });
    });

    // Smooth scroll for navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
        });
    });

    // Auto-hide alerts/messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'all 0.3s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Weather icon animation
    const weatherIcon = document.querySelector('.weather-icon-large img');
    if (weatherIcon) {
        weatherIcon.style.animation = 'float 3s ease-in-out infinite';
    }

    // Add hover effect to search items
    const searchItems = document.querySelectorAll('.search-item');
    searchItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 8px 16px rgba(59, 130, 246, 0.2)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.boxShadow = 'none';
        });
    });

    // Mobile sidebar toggle (for responsive)
    const createMobileToggle = () => {
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.sidebar');
            const mainContent = document.querySelector('.main-content');
            
            if (!document.querySelector('.mobile-toggle')) {
                const toggleBtn = document.createElement('button');
                toggleBtn.className = 'mobile-toggle';
                toggleBtn.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <line x1="3" y1="12" x2="21" y2="12"/>
                        <line x1="3" y1="6" x2="21" y2="6"/>
                        <line x1="3" y1="18" x2="21" y2="18"/>
                    </svg>
                `;
                toggleBtn.style.cssText = `
                    position: fixed;
                    top: 1rem;
                    left: 1rem;
                    z-index: 1001;
                    padding: 0.75rem;
                    background: var(--bg-card);
                    border: 1px solid var(--border);
                    border-radius: 10px;
                    cursor: pointer;
                    width: 48px;
                    height: 48px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                `;
                toggleBtn.querySelector('svg').style.cssText = `
                    width: 24px;
                    height: 24px;
                    stroke-width: 2px;
                    color: var(--text-primary);
                `;
                
                document.body.appendChild(toggleBtn);
                
                toggleBtn.addEventListener('click', () => {
                    sidebar.style.transition = 'transform 0.3s ease';
                    if (sidebar.style.transform === 'translateX(0%)') {
                        sidebar.style.transform = 'translateX(-100%)';
                    } else {
                        sidebar.style.transform = 'translateX(0%)';
                    }
                });

                // Close sidebar when clicking outside
                mainContent.addEventListener('click', () => {
                    if (sidebar.style.transform === 'translateX(0%)') {
                        sidebar.style.transform = 'translateX(-100%)';
                    }
                });
            }
        }
    };

    createMobileToggle();
    window.addEventListener('resize', createMobileToggle);
});

// Add floating animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);