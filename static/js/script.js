// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts
    const autoHideAlerts = document.querySelectorAll('.alert-auto-hide');
    autoHideAlerts.forEach(function(alert) {
        setTimeout(function() {
            new bootstrap.Alert(alert).close();
        }, 5000);
    });
    
    // Card animations
    const animatedCards = document.querySelectorAll('.card');
    if (window.IntersectionObserver) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        animatedCards.forEach(card => {
            observer.observe(card);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        animatedCards.forEach(card => {
            card.classList.add('animated');
        });
    }
    
    // Mobile detection
    const isMobile = window.matchMedia("only screen and (max-width: 768px)").matches;
    
    // Close sidebar on link click for mobile
    if (isMobile) {
        const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                sidebar.classList.add('active');
            });
        });
    }
    
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add fade-in animation to elements with fade-in class
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
    });

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-close alerts after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);

    // Add confirmation dialog for delete buttons
    document.querySelectorAll('.btn-delete').forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Enable data tables if available
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.datatable').DataTable({
            responsive: true,
            pageLength: 10,
            lengthMenu: [[5, 10, 25, 50, -1], [5, 10, 25, 50, "All"]]
        });
    }

    // Image preview before upload
    const photoInput = document.getElementById('photo');
    const photoPreview = document.getElementById('photoPreview');
    
    if (photoInput && photoPreview) {
        photoInput.addEventListener('change', function() {
            previewImage(this, 'photoPreview');
        });
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

// Function to handle image preview before upload
function previewImage(input, previewElementId) {
    const previewElement = document.getElementById(previewElementId);
    
    if (input.files && input.files[0] && previewElement) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            previewElement.src = e.target.result;
            previewElement.style.display = 'block';
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Function to print any section of the page
function printSection(elementId) {
    const element = document.getElementById(elementId);
    const originalContent = document.body.innerHTML;
    
    document.body.innerHTML = `
        <html>
            <head>
                <title>Print</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-4">
                    <div class="text-center mb-4">
                        <h2>Jarvin CMS</h2>
                        <p class="text-muted">Printed on ${new Date().toLocaleDateString()}</p>
                    </div>
                    ${element.innerHTML}
                </div>
                <script>
                    window.onload = function() { window.print(); }
                </script>
            </body>
        </html>
    `;
    
    setTimeout(function() {
        document.body.innerHTML = originalContent;
    }, 100);
}

// Function to show loading spinner
function showLoading(message = 'Loading...') {
    const loadingHtml = `
        <div id="loadingSpinner" class="position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-white bg-opacity-75" style="z-index: 9999;">
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">${message}</p>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

// Function to hide loading spinner
function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

/**
 * Display an English language notice if needed
 * @param {HTMLElement} containerElement - The message container to check
 */
function checkForLanguageNotice(containerElement) {
    // Look for common non-English language patterns
    const content = containerElement.textContent || "";
    const hasNonEnglishPatterns = 
        /[\u0600-\u06FF]/.test(content) || // Arabic
        /[\u0900-\u097F]/.test(content) || // Devanagari (Hindi)
        /[\u0400-\u04FF]/.test(content) || // Cyrillic (Russian)
        /[\u4E00-\u9FFF]/.test(content) || // Chinese
        /[\u3040-\u309F]/.test(content) || // Hiragana (Japanese)
        /[\u30A0-\u30FF]/.test(content);   // Katakana (Japanese)
    
    if (hasNonEnglishPatterns) {
        const notice = document.createElement('p');
        notice.className = 'mt-2 small text-muted';
        notice.innerHTML = 'Note: Jarvin AI responds only in English. If you see characters in another language, this might be an error.';
        containerElement.appendChild(notice);
    }
}

// You can call this function after adding a new message to the chat
// For example:
// const messageElement = document.createElement('div');
// messageElement.innerHTML = messageHtml;
// chatContainer.appendChild(messageElement);
// checkForLanguageNotice(messageElement);
