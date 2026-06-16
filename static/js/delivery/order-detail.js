(function() {
    'use strict';
    
    // Elementos del DOM
    let paymentModal = null;
    let incidenceModal = null;
    
    /**
     * Obtiene un elemento del DOM con validación
     * @param {string} id - ID del elemento
     * @returns {HTMLElement|null}
     */
    function getElement(id) {
        return document.getElementById(id);
    }
    
    /**
     * Abre un modal específico
     * @param {HTMLElement} modal - Elemento del modal
     * @param {string} modalId - ID del modal (para logging)
     */
    function openModal(modal, modalId) {
        if (!modal) {
            console.warn(`Modal ${modalId} no encontrado`);
            return;
        }
        
        modal.classList.add('active');
        
        // Prevenir scroll del body cuando el modal está abierto
        document.body.style.overflow = 'hidden';
        
        // Enfocar el primer elemento interactivo dentro del modal
        const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            setTimeout(function() {
                firstFocusable.focus();
            }, 100);
        }
        
        // Disparar evento personalizado
        const event = new CustomEvent('modal:opened', { detail: { modalId: modalId } });
        document.dispatchEvent(event);
    }
    
    /**
     * Cierra un modal específico
     * @param {HTMLElement} modal - Elemento del modal
     * @param {string} modalId - ID del modal (para logging)
     */
    function closeModal(modal, modalId) {
        if (!modal) {
            console.warn(`Modal ${modalId} no encontrado`);
            return;
        }
        
        modal.classList.remove('active');
        
        // Restaurar scroll del body
        document.body.style.overflow = '';
        
        // Disparar evento personalizado
        const event = new CustomEvent('modal:closed', { detail: { modalId: modalId } });
        document.dispatchEvent(event);
    }
    
    /**
     * Muestra el modal de confirmación de pago
     * @function showPaymentModal
     */
    function showPaymentModal() {
        if (!paymentModal) {
            paymentModal = getElement('paymentModal');
        }
        openModal(paymentModal, 'paymentModal');
    }
    
    /**
     * Cierra el modal de confirmación de pago
     * @function closePaymentModal
     */
    function closePaymentModal() {
        if (!paymentModal) {
            paymentModal = getElement('paymentModal');
        }
        closeModal(paymentModal, 'paymentModal');
    }
    
    /**
     * Muestra el modal de reporte de incidencia
     * @function showIncidenceModal
     */
    function showIncidenceModal() {
        if (!incidenceModal) {
            incidenceModal = getElement('incidenceModal');
        }
        openModal(incidenceModal, 'incidenceModal');
    }
    
    /**
     * Cierra el modal de reporte de incidencia
     * @function closeIncidenceModal
     */
    function closeIncidenceModal() {
        if (!incidenceModal) {
            incidenceModal = getElement('incidenceModal');
        }
        closeModal(incidenceModal, 'incidenceModal');
    }
    
    /**
     * Configura el cierre de modales al hacer clic fuera
     * @function setupModalClickOutside
     */
    function setupModalClickOutside() {
        paymentModal = getElement('paymentModal');
        incidenceModal = getElement('incidenceModal');
        
        // Modal de pago
        if (paymentModal) {
            paymentModal.addEventListener('click', function(event) {
                const isClickOnOverlay = event.target === event.currentTarget;
                
                if (isClickOnOverlay) {
                    closePaymentModal();
                }
            });
        }
        
        // Modal de incidencia
        if (incidenceModal) {
            incidenceModal.addEventListener('click', function(event) {
                const isClickOnOverlay = event.target === event.currentTarget;
                
                if (isClickOnOverlay) {
                    closeIncidenceModal();
                }
            });
        }
    }
    
    /**
     * Configura el cierre de modales con tecla Escape
     * @function setupModalEscapeKey
     */
    function setupModalEscapeKey() {
        document.addEventListener('keydown', function(event) {
            const isEscapeKey = event.key === 'Escape';
            
            if (!isEscapeKey) {
                return;
            }
            
            // Usar optional chaining para verificar modales activos
            if (paymentModal?.classList.contains('active')) {
                closePaymentModal();
            }
            
            if (incidenceModal?.classList.contains('active')) {
                closeIncidenceModal();
            }
        });
    }
    
    /**
     * Abre Google Maps con la dirección proporcionada
     * @param {string} address - Dirección a buscar
     */
    function openMaps(address) {
        if (!address || typeof address !== 'string') {
            console.error('Dirección inválida para abrir en Google Maps');
            if (globalThis.showToast) {
                globalThis.showToast('Dirección no válida', 'error');
            }
            return;
        }
        
        const encodedAddress = encodeURIComponent(address.trim());
        const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodedAddress}`;
        
        // Abrir en nueva pestaña/ventana
        globalThis.open(mapsUrl, '_blank', 'noopener,noreferrer');
    }
    
    /**
     * Configura el botón de Google Maps usando dataset
     * @function setupMapsButton
     */
    function setupMapsButton() {
        // Buscar cualquier botón que tenga data-address (usando dataset)
        const mapButtons = document.querySelectorAll('[data-address]');
        
        mapButtons.forEach(function(button) {
            // Usar dataset en lugar de getAttribute (S7761)
            const address = button.dataset.address;
            
            // Remover onclick inline si existe
            if (button.hasAttribute('onclick')) {
                button.removeAttribute('onclick');
            }
            
            button.addEventListener('click', function(event) {
                event.preventDefault();
                openMaps(address);
            });
            
            // Soporte para teclado
            button.addEventListener('keydown', function(event) {
                const isEnterOrSpace = event.key === 'Enter' || event.key === ' ';
                
                if (isEnterOrSpace) {
                    event.preventDefault();
                    openMaps(address);
                }
            });
        });
    }
    
    /**
     * Configura el botón de marcar como pagado
     * @function setupMarkAsPaidButton
     */
    function setupMarkAsPaidButton() {
        const markPaidForm = document.querySelector('form[action*="mark-paid"]');
        
        if (markPaidForm) {
            markPaidForm.addEventListener('submit', function(event) {
                const confirmMessage = '¿Confirmas que deseas marcar este pedido como pagado?';
                const isConfirmed = confirm(confirmMessage);
                
                if (!isConfirmed) {
                    event.preventDefault();
                }
            });
        }
    }
    
    /**
     * Configura el formulario de incidencia
     * @function setupIncidenceForm
     */
    function setupIncidenceForm() {
        const incidenceForm = document.querySelector('#incidenceModal form');
        
        if (!incidenceForm) {
            return;
        }
        
        incidenceForm.addEventListener('submit', function(event) {
            const selectedType = document.querySelector('select[name="incidence_type"]');
            const hasSelectedType = selectedType && selectedType.value !== '';
            
            if (!hasSelectedType) {
                event.preventDefault();
                if (globalThis.showToast) {
                    globalThis.showToast('Por favor selecciona un tipo de incidencia', 'error');
                }
                return;
            }
            
            const confirmMessage = '¿Confirmas que deseas reportar esta incidencia?\n\nEl pedido será cancelado y el administrador será notificado.';
            const isConfirmed = confirm(confirmMessage);
            
            if (!isConfirmed) {
                event.preventDefault();
            }
        });
    }
    
    /**
     * Configura el botón de llamada telefónica
     * @function setupPhoneCallButton
     */
    function setupPhoneCallButton() {
        const phoneLink = document.querySelector('a[href^="tel:"]');
        
        if (phoneLink) {
            phoneLink.addEventListener('click', function(event) {
                const phoneNumber = this.getAttribute('href').replace('tel:', '');
                const confirmMessage = `¿Deseas llamar al ${phoneNumber}?`;
                const isConfirmed = confirm(confirmMessage);
                
                if (!isConfirmed) {
                    event.preventDefault();
                }
            });
        }
    }
    
    /**
     * Exporta funciones globales necesarias
     * @function exposeGlobalFunctions
     */
    function exposeGlobalFunctions() {
        // Solo exponer lo necesario para el HTML inline (si existe)
        globalThis.showPaymentModal = showPaymentModal;
        globalThis.closePaymentModal = closePaymentModal;
        globalThis.showIncidenceModal = showIncidenceModal;
        globalThis.closeIncidenceModal = closeIncidenceModal;
        globalThis.openMaps = openMaps;
    }
    
    /**
     * Inicializa la página de detalle de pedido
     * @function initOrderDetailPage
     */
    function initOrderDetailPage() {
        // Obtener referencias a modales
        paymentModal = getElement('paymentModal');
        incidenceModal = getElement('incidenceModal');
        
        // Configurar modales
        setupModalClickOutside();
        setupModalEscapeKey();
        
        // Configurar botones y formularios
        setupMapsButton();
        setupMarkAsPaidButton();
        setupIncidenceForm();
        setupPhoneCallButton();
        
        // Exponer funciones globales
        exposeGlobalFunctions();
        
        // Registrar analytics (opcional)
        const orderNumberElement = document.querySelector('h1');
        const orderNumber = orderNumberElement?.textContent || 'unknown';
        console.log(`Página de detalle inicializada para pedido: ${orderNumber}`);
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOrderDetailPage);
    } else {
        initOrderDetailPage();
    }
})();