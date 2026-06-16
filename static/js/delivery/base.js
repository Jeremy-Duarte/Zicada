// ==================== BASE PWA - VERSIÓN OPTIMIZADA ====================

// Estado de conexión
let isOnline = navigator.onLine;
const offlineIndicator = document.getElementById('offlineIndicator');

/**
 * Actualiza la interfaz según el estado de conexión
 * @function updateOnlineStatus
 * @description Muestra/oculta el indicador offline y actualiza su valor
 */
function updateOnlineStatus() {
    isOnline = navigator.onLine;
    
    if (!offlineIndicator) {
        return;
    }
    
    if (isOnline) {
        // Está conectado - ocultar indicador
        offlineIndicator.classList.add('hidden');
        offlineIndicator.setAttribute('aria-hidden', 'true');
        offlineIndicator.value = 'Conectado';
    } else {
        // Está desconectado - mostrar indicador
        offlineIndicator.classList.remove('hidden');
        offlineIndicator.setAttribute('aria-hidden', 'false');
        offlineIndicator.value = 'Desconectado';
    }
}

// Eventos de conexión
globalThis.addEventListener('online', updateOnlineStatus);
globalThis.addEventListener('offline', updateOnlineStatus);
updateOnlineStatus();

// Botón para cerrar la notificación offline
const dismissBtn = document.getElementById('dismissOfflineBtn');

if (dismissBtn) {
    dismissBtn.addEventListener('click', function() {
        if (offlineIndicator) {
            offlineIndicator.classList.add('hidden');
        }
    });
    
    // Soporte para teclado (accesibilidad)
    dismissBtn.addEventListener('keydown', function(event) {
        const isEnterOrSpace = event.key === 'Enter' || event.key === ' ';
        
        if (isEnterOrSpace) {
            event.preventDefault();
            if (offlineIndicator) {
                offlineIndicator.classList.add('hidden');
            }
        }
    });
}

/**
 * Obtiene el color de fondo según el tipo de toast
 * @param {string} type - Tipo de toast ('success', 'error', 'info')
 * @returns {string} Clase CSS de color
 */
function getToastBgColor(type) {
    if (type === 'success') {
        return 'bg-green-500';
    }
    
    if (type === 'error') {
        return 'bg-red-500';
    }
    
    return 'bg-gray-800';
}

/**
 * Obtiene el ícono según el tipo de toast
 * @param {string} type - Tipo de toast ('success', 'error', 'info')
 * @returns {string} Nombre del ícono Font Awesome
 */
function getToastIcon(type) {
    if (type === 'success') {
        return 'check-circle';
    }
    
    if (type === 'error') {
        return 'exclamation-circle';
    }
    
    return 'info-circle';
}

/**
 * Muestra un mensaje temporal tipo toast
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de mensaje ('success', 'error', 'info')
 */
globalThis.showToast = function(message, type = 'info') {
    // Limpiar toasts existentes
    const existingToasts = document.querySelectorAll('.toast-message');
    existingToasts.forEach(function(toast) {
        toast.remove();
    });
    
    // Crear nuevo toast
    const toast = document.createElement('div');
    const bgColor = getToastBgColor(type);
    const icon = getToastIcon(type);
    
    toast.className = `toast-message fixed bottom-20 left-4 right-4 ${bgColor} text-white px-4 py-2 rounded-lg shadow-lg z-50 text-center transition-opacity duration-300`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML = `<i class="fas fa-${icon} mr-2" aria-hidden="true"></i>${escapeHtml(message)}`;
    
    document.body.appendChild(toast);
    
    // Auto-eliminar después de 3 segundos
    setTimeout(function() {
        toast.style.opacity = '0';
        setTimeout(function() {
            toast.remove();
        }, 300);
    }, 3000);
};

/**
 * Escapa caracteres HTML para prevenir XSS
 * @param {string} text - Texto a escapar
 * @returns {string} Texto escapado
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Registrar Service Worker
if ('serviceWorker' in navigator) {
    globalThis.addEventListener('load', function() {
        const swUrl = "{% url 'delivery:service_worker' %}";
        navigator.serviceWorker.register(swUrl)
            .then(function(registration) {
                console.log('Service Worker registrado:', registration.scope);
            })
            .catch(function(error) {
                console.error('Error al registrar Service Worker:', error);
            });
    });
}

/**
 * Maneja el envío de formularios para prevenir doble submit
 * @param {HTMLFormElement} form - Elemento formulario
 */
function setupFormSubmitProtection(form) {
    let isSubmitting = false;
    
    form.addEventListener('submit', function(event) {
        if (isSubmitting) {
            event.preventDefault();
            return;
        }
        
        isSubmitting = true;
        const submitBtn = this.querySelector('button[type="submit"]');
        
        if (submitBtn && !submitBtn.disabled) {
            submitBtn.disabled = true;
            submitBtn.dataset.originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Procesando...';
            
            setTimeout(function() {
                if (submitBtn.disabled) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalText || 'Enviar';
                    isSubmitting = false;
                }
            }, 10000);
        }
    });
}

const forms = document.querySelectorAll('form');
forms.forEach(setupFormSubmitProtection);

const isInPwaMode = globalThis.matchMedia('(display-mode: standalone)').matches || 
                    globalThis.navigator.standalone === true;

if (isInPwaMode) {
    document.body.classList.add('pwa-mode');
    console.log('App ejecutándose como PWA instalada');
}

document.addEventListener('visibilitychange', function() {
    const isVisible = document.visibilityState === 'visible';
    
    if (isVisible && !isOnline) {
        updateOnlineStatus();
    }
});