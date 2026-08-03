/**
 * Inicializacion del login de Delivery
 * - Toggle de visibilidad de contrasena
 * - Validacion + prevencion de doble envio en un solo handler
 * - Limpieza de Service Workers obsoletos
 */

// Limpiar Service Workers obsoletos al llegar al login
(function cleanupOldServiceWorkers() {
    if (!('serviceWorker' in navigator)) {
        return;
    }
    navigator.serviceWorker.getRegistrations().then(function(registrations) {
        registrations.forEach(function(registration) {
            registration.update().catch(function() {});
        });
    }).catch(function() {});
})();

// Toggle password visibility (accesible)
var togglePassword = document.getElementById('togglePassword');
var passwordInput = document.getElementById('password');

if (togglePassword && passwordInput) {
    togglePassword.addEventListener('click', function() {
        var type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        var icon = this.querySelector('i');
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
        this.setAttribute('aria-label', type === 'password' ? 'Mostrar contrasena' : 'Ocultar contrasena');
    });

    togglePassword.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.click();
        }
    });
}

// Validacion + prevencion de doble envio (un solo handler)
var loginForm = document.querySelector('form');
var isSubmitting = false;

if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
        if (isSubmitting) {
            e.preventDefault();
            return false;
        }

        var username = document.getElementById('username');
        var password = document.getElementById('password');

        if (username && !username.value.trim()) {
            e.preventDefault();
            if (window.showToast) {
                window.showToast('Por favor ingresa tu usuario', 'error');
            }
            username.focus();
            return false;
        }

        if (password && !password.value) {
            e.preventDefault();
            if (window.showToast) {
                window.showToast('Por favor ingresa tu contrasena', 'error');
            }
            password.focus();
            return false;
        }

        isSubmitting = true;
        var submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Iniciando sesion...';
        }
        setTimeout(function() { isSubmitting = false; }, 10000);
    });
}
