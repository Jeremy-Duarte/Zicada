(function() {
    'use strict';
    
    // Variables de estado
    let touchStartY = 0;
    let isRefreshing = false;
    let mainElement = null;
    
    /**
     * Crea un indicador de carga para la lista de pedidos
     * @param {string} message - Mensaje a mostrar
     * @returns {HTMLElement} Elemento del indicador
     */
    function createLoadingIndicator(message) {
        const indicator = document.createElement('div');
        indicator.className = 'fixed top-32 left-0 right-0 bg-black text-white text-center py-2 text-sm z-50';
        indicator.setAttribute('role', 'status');
        indicator.setAttribute('aria-live', 'polite');
        indicator.innerHTML = `<i class="fas fa-spinner fa-spin mr-2" aria-hidden="true"></i>${escapeHtml(message)}`;
        return indicator;
    }
    
    /**
     * Actualiza los datos de pedidos
     * @async
     * @function refreshData
     */
    async function refreshData() {
        // Evitar refreshes concurrentes
        if (isRefreshing) {
            return;
        }
        
        isRefreshing = true;
        const indicator = createLoadingIndicator('Actualizando pedidos...');
        document.body.appendChild(indicator);
        
        try {
            const response = await fetch('/delivery/api/orders/');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                globalThis.showToast('Pedidos actualizados', 'success');
                setTimeout(function() {
                    globalThis.location.reload();
                }, 1000);
            } else {
                throw new Error('Error en la respuesta del servidor');
            }
        } catch (error) {
            console.error('Error al actualizar pedidos:', error);
            globalThis.showToast('Error al actualizar. Verifica tu conexión.', 'error');
        } finally {
            indicator.remove();
            isRefreshing = false;
        }
    }
    
    /**
     * Configura el evento de pull-to-refresh
     * @function setupPullToRefresh
     */
    function setupPullToRefresh() {
        mainElement = document.querySelector('main');
        
        if (!mainElement) {
            console.warn('No se encontró el elemento main para pull-to-refresh');
            return;
        }
        
        // Touch start - registrar posición inicial
        mainElement.addEventListener('touchstart', function(event) {
            touchStartY = event.touches[0].clientY;
        });
        
        // Touch move - detectar pull hacia abajo
        mainElement.addEventListener('touchmove', function(event) {
            const scrollTop = mainElement.scrollTop;
            const isAtTop = scrollTop === 0;
            const currentTouchY = event.touches[0].clientY;
            const hasPulledDown = currentTouchY > touchStartY + 50;
            const shouldRefresh = isAtTop && hasPulledDown && !isRefreshing;
            
            if (shouldRefresh) {
                event.preventDefault();
                refreshData();
            }
        });
        
        // Prevenir comportamientos por defecto en iOS
        mainElement.addEventListener('touchcancel', function() {
            touchStartY = 0;
        });
    }
    
    /**
     * Configura los botones de refresh manual
     * @function setupRefreshButtons
     */
    function setupRefreshButtons() {
        const refreshBtn = document.getElementById('refreshBtn');
        const emptyRefreshBtn = document.getElementById('emptyRefreshBtn');
        
        // Botón de refresh en el header
        if (refreshBtn) {
            refreshBtn.addEventListener('click', refreshData);
            
            // Soporte para teclado (accesibilidad)
            refreshBtn.addEventListener('keydown', function(event) {
                const isEnterOrSpace = event.key === 'Enter' || event.key === ' ';
                
                if (isEnterOrSpace) {
                    event.preventDefault();
                    refreshData();
                }
            });
        }
        
        // Botón de refresh cuando no hay pedidos
        if (emptyRefreshBtn) {
            emptyRefreshBtn.addEventListener('click', refreshData);
            
            emptyRefreshBtn.addEventListener('keydown', function(event) {
                const isEnterOrSpace = event.key === 'Enter' || event.key === ' ';
                
                if (isEnterOrSpace) {
                    event.preventDefault();
                    refreshData();
                }
            });
        }
    }
    
    /**
     * Configura la navegación por teclado entre pedidos
     * @function setupKeyboardNavigation
     */
    function setupKeyboardNavigation() {
        const orderCards = document.querySelectorAll('.order-card');
        
        if (orderCards.length === 0) {
            return;
        }
        
        orderCards.forEach(function(card, index) {
            card.setAttribute('tabindex', '0');
            
            card.addEventListener('keydown', function(event) {
                const isEnter = event.key === 'Enter';
                const isSpace = event.key === ' ';
                
                if (isEnter || isSpace) {
                    event.preventDefault();
                    this.click();
                }
                
                // Navegación con flechas
                if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    const nextCard = orderCards[index + 1];
                    if (nextCard) {
                        nextCard.focus();
                    }
                }
                
                if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    const prevCard = orderCards[index - 1];
                    if (prevCard) {
                        prevCard.focus();
                    }
                }
            });
        });
    }
    
    /**
     * Filtra pedidos sin recargar la página (mejora UX)
     * @function setupFilterButtons
     */
    function setupFilterButtons() {
        const filterBtns = document.querySelectorAll('.filter-btn');
        
        if (filterBtns.length === 0) {
            return;
        }
        
        filterBtns.forEach(function(btn) {
            btn.addEventListener('click', function(event) {
                // Los filtros ya son enlaces, solo añadimos indicador visual
                const currentUrl = new URL(globalThis.location.href);
                const filterValue = this.getAttribute('href').split('=')[1];
                
                if (currentUrl.searchParams.get('filter') === filterValue) {
                    event.preventDefault();
                } else {
                    globalThis.showToast('Filtrando pedidos...', 'info');
                }
            });
        });
    }
    
    /**
     * Inicializa la página de pedidos
     * @function initOrdersPage
     */
    function initOrdersPage() {
        setupPullToRefresh();
        setupRefreshButtons();
        setupKeyboardNavigation();
        setupFilterButtons();
        
        // Registrar analytics opcional
        console.log('Página de pedidos inicializada');
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOrdersPage);
    } else {
        initOrdersPage();
    }
})();