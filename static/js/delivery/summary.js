(function() {
    'use strict';
    
    /**
     * Manejador para el cierre de jornada
     */
    function setupCloseJourneyHandler() {
        const closeForm = document.getElementById('closeJourneyForm');
        
        if (!closeForm) {
            return;
        }
        
        closeForm.addEventListener('submit', function(event) {
            const confirmMessage = '¿Confirmas que deseas cerrar tu jornada laboral?\n\nDespués de cerrar no podrás modificar los pedidos de hoy.';
            const isConfirmed = confirm(confirmMessage);
            
            if (!isConfirmed) {
                event.preventDefault();
            }
        });
    }
    
    /**
     * Crea un indicador de carga
     */
    function createLoadingIndicator(message) {
        const indicator = document.createElement('div');
        indicator.className = 'fixed top-16 left-0 right-0 bg-black text-white text-center py-2 text-sm z-50';
        indicator.setAttribute('role', 'status');
        indicator.setAttribute('aria-live', 'polite');
        indicator.innerHTML = `<i class="fas fa-spinner fa-spin mr-2" aria-hidden="true"></i>${escapeHtml(message)}`;
        return indicator;
    }
    
    /**
     * Actualiza el resumen
     */
    async function refreshSummary() {
        const indicator = createLoadingIndicator('Actualizando resumen...');
        document.body.appendChild(indicator);
        
        try {
            const response = await fetch('/delivery/api/orders/');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                globalThis.showToast('Resumen actualizado', 'success');
                setTimeout(function() {
                    globalThis.location.reload();
                }, 1000);
            } else {
                throw new Error('Error en respuesta');
            }
        } catch (error) {
            console.error('Refresh error:', error);
            globalThis.showToast('Error al actualizar', 'error');
        } finally {
            indicator.remove();
        }
    }
    
    /**
     * Configura botón de refresh
     */
    function setupRefreshButton() {
        const refreshBtn = document.getElementById('refreshBtn');
        
        if (!refreshBtn) {
            return;
        }
        
        refreshBtn.addEventListener('click', refreshSummary);
        
        refreshBtn.addEventListener('keydown', function(event) {
            const isEnterOrSpace = event.key === 'Enter' || event.key === ' ';
            
            if (isEnterOrSpace) {
                event.preventDefault();
                refreshSummary();
            }
        });
    }
    
    /**
     * Configura pull-to-refresh
     */
    function setupPullToRefresh() {
        let touchStartY = 0;
        let isRefreshing = false;
        const mainElement = document.querySelector('main');
        
        if (!mainElement) {
            return;
        }
        
        mainElement.addEventListener('touchstart', function(event) {
            touchStartY = event.touches[0].clientY;
        });
        
        mainElement.addEventListener('touchmove', function(event) {
            const scrollTop = mainElement.scrollTop;
            const isAtTop = scrollTop === 0;
            const hasPulledDown = event.touches[0].clientY > touchStartY + 50;
            
            if (isAtTop && hasPulledDown && !isRefreshing) {
                event.preventDefault();
                refreshSummary();
                isRefreshing = true;
                
                setTimeout(function() {
                    isRefreshing = false;
                }, 5000);
            }
        });
    }
    
    /**
     * Inicializa la página
     */
    function initSummaryPage(isClosed) {
        setupCloseJourneyHandler();
        
        if (!isClosed) {
            setupRefreshButton();
            setupPullToRefresh();
        }
    }
    
    // Inicializar cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        const metaClosed = document.querySelector('meta[name="journey-closed"]');
        const isClosed = metaClosed ? metaClosed.getAttribute('content') === 'true' : false;
        
        initSummaryPage(isClosed);
    });
})();