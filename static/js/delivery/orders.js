// ==================== ORDERS.JS - LISTA DE PEDIDOS ====================

(function() {
    'use strict';
    
    // ============================================================
    // CONFIGURACIÓN
    // ============================================================
    
    const CONFIG = globalThis.DELIVERY_CONFIG || {
        apiBase: '/delivery/api',
        csrfToken: '',
        userId: null,
        initialFilter: 'all',
        refreshInterval: 30000
    };
    
    // ============================================================
    // ESTADO
    // ============================================================
    
    let state = {
        orders: [],
        filter: CONFIG.initialFilter || 'all',
        isLoading: false,
        isRefreshing: false,
        touchStartY: 0
    };
    
    // ============================================================
    // DOM REFERENCIAS
    // ============================================================
    
    const elements = {
        ordersList: document.getElementById('ordersList'),
        loadingState: document.getElementById('loadingState'),
        emptyState: document.getElementById('emptyState'),
        totalCount: document.getElementById('totalCount'),
        pendingCount: document.getElementById('pendingCount'),
        filterBtns: document.querySelectorAll('.filter-btn'),
        refreshBtn: document.getElementById('refreshBtn'),
        emptyRefreshBtn: document.getElementById('emptyRefreshBtn'),
        mainElement: document.querySelector('main')
    };
    
    // ============================================================
    // FUNCIONES DE RENDERIZADO
    // ============================================================
    
    /**
     * Renderiza un pedido individual como tarjeta HTML
     */
    function renderOrderCard(order) {
        const statusColors = {
            'listo': 'bg-yellow-100 text-yellow-800',
            'en_camino': 'bg-blue-100 text-blue-800',
            'entregado': 'bg-green-100 text-green-800',
            'cancelado': 'bg-red-100 text-red-800'
        };
        
        const statusIcon = order.status === 'en_camino' ? 'fa-truck' : 'fa-clock';
        
        return `
            <a href="/delivery/orders/${order.id}/" class="order-card block bg-white rounded-xl shadow-sm hover:shadow-md transition overflow-hidden mb-3">
                <!-- Estado y número -->
                <div class="px-4 py-3 border-b border-gray-100">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColors[order.status] || 'bg-gray-100 text-gray-800'}">
                                <i class="fas ${statusIcon} text-xs mr-1"></i>
                                ${order.status_display || order.status}
                            </span>
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                                <i class="fas fa-shield-alt mr-1"></i> Pago en línea
                            </span>
                        </div>
                        <span class="text-xs text-gray-500">${order.order_number}</span>
                    </div>
                </div>
                
                <!-- Cliente -->
                <div class="px-4 py-3">
                    <div class="flex items-start space-x-3">
                        <div class="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-user text-gray-500 text-lg"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="font-medium text-gray-900">${escapeHtml(order.customer_name)}</p>
                            <p class="text-sm text-gray-500 mt-1 truncate">${escapeHtml(order.customer_phone || '')}</p>
                        </div>
                        <div class="text-right">
                            <p class="font-semibold text-gray-900">$${formatCurrency(order.total_amount)}</p>
                        </div>
                    </div>
                </div>
                
                <!-- Dirección -->
                <div class="px-4 py-3 bg-gray-50 border-t border-gray-100">
                    <div class="flex items-start space-x-2">
                        <i class="fas fa-map-marker-alt text-gray-400 mt-0.5 text-sm"></i>
                        <p class="text-sm text-gray-600 line-clamp-2">${escapeHtml(order.shipping_address)}</p>
                    </div>
                    ${order.delivery_notes ? `
                        <div class="flex items-start space-x-2 mt-2">
                            <i class="fas fa-sticky-note text-gray-400 mt-0.5 text-sm"></i>
                            <p class="text-xs text-gray-500">${escapeHtml(order.delivery_notes.substring(0, 60))}${order.delivery_notes.length > 60 ? '...' : ''}</p>
                        </div>
                    ` : ''}
                </div>
            </a>
        `;
    }
    
    /**
     * Renderiza la lista completa de pedidos
     */
    function renderOrders(orders) {
        const container = elements.ordersList;
        
        if (!container) return;
        
        // Actualizar contadores
        if (elements.totalCount) {
            elements.totalCount.textContent = orders.length;
        }
        
        if (elements.pendingCount) {
            const pending = orders.filter(o => o.status === 'listo' || o.status === 'en_camino');
            elements.pendingCount.textContent = pending.length;
        }
        
        // Mostrar/ocultar estados
        if (orders.length === 0) {
            container.innerHTML = '';
            showEmptyState(true);
            showLoadingState(false);
            return;
        }
        
        showEmptyState(false);
        showLoadingState(false);
        
        // Renderizar pedidos
        container.innerHTML = orders.map(renderOrderCard).join('');
    }
    
    /**
     * Muestra/oculta el estado de carga
     */
    function showLoadingState(show) {
        if (elements.loadingState) {
            elements.loadingState.classList.toggle('hidden', !show);
        }
    }
    
    /**
     * Muestra/oculta el estado vacío
     */
    function showEmptyState(show) {
        if (elements.emptyState) {
            elements.emptyState.classList.toggle('hidden', !show);
        }
    }
    
    /**
     * Formatea un número como moneda
     */
    function formatCurrency(amount) {
        return new Intl.NumberFormat('es-CO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }
    
    /**
     * Escapa HTML para prevenir XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ============================================================
    // FUNCIONES DE API
    // ============================================================
    
    /**
     * Obtiene los pedidos desde la API
     */
    async function fetchOrders(filter = state.filter) {
        if (state.isLoading) return;
        
        state.isLoading = true;
        showLoadingState(true);
        
        try {
            const url = `${CONFIG.apiBase}/orders/?filter=${filter}`;
            const response = await fetch(url, {
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                state.orders = data.orders || [];
                renderOrders(state.orders);
                return data;
            } else {
                throw new Error(data.message || 'Error al cargar pedidos');
            }
        } catch (error) {
            console.error('Error fetching orders:', error);
            globalThis.showToast('Error al cargar pedidos. Verifica tu conexión.', 'error');
            
            // Mostrar mensaje de error en la UI
            if (elements.ordersList) {
                elements.ordersList.innerHTML = `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                        <i class="fas fa-exclamation-circle text-red-500 text-2xl mb-2"></i>
                        <p class="text-red-700">Error al cargar los pedidos</p>
                        <button onclick="globalThis.location.reload()" class="mt-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm">
                            Reintentar
                        </button>
                    </div>
                `;
            }
            
            showLoadingState(false);
        } finally {
            state.isLoading = false;
        }
    }
    
    /**
     * Actualiza los pedidos (pull-to-refresh)
     */
    async function refreshOrders() {
        if (state.isRefreshing) return;
        
        state.isRefreshing = true;
        
        // Mostrar indicador de refresh
        const indicator = document.createElement('div');
        indicator.className = 'fixed top-16 left-0 right-0 bg-black text-white text-center py-2 text-sm z-50';
        indicator.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Actualizando pedidos...';
        document.body.appendChild(indicator);
        
        try {
            await fetchOrders(state.filter);
            globalThis.showToast('Pedidos actualizados', 'success');
        } catch (error) {
            // Error ya manejado en fetchOrders
        } finally {
            indicator.remove();
            state.isRefreshing = false;
        }
    }
    
    // ============================================================
    // CONFIGURACIÓN DE EVENTOS
    // ============================================================
    
    /**
     * Configura los botones de filtro
     */
    function setupFilters() {
        elements.filterBtns.forEach(btn => {
            btn.addEventListener('click', function(event) {
                event.preventDefault();
                
                const filter = this.dataset.filter;
                if (!filter || filter === state.filter) return;
                
                // Actualizar UI de filtros
                elements.filterBtns.forEach(b => {
                    b.classList.remove('bg-black', 'text-white');
                    b.classList.add('bg-gray-100', 'text-gray-700');
                });
                this.classList.remove('bg-gray-100', 'text-gray-700');
                this.classList.add('bg-black', 'text-white');
                
                state.filter = filter;
                fetchOrders(filter);
            });
            
            // Soporte para teclado
            btn.addEventListener('keydown', function(event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    this.click();
                }
            });
        });
    }
    
    /**
     * Configura los botones de refresh
     */
    function setupRefreshButtons() {
        if (elements.refreshBtn) {
            elements.refreshBtn.addEventListener('click', refreshOrders);
        }
        
        if (elements.emptyRefreshBtn) {
            elements.emptyRefreshBtn.addEventListener('click', refreshOrders);
        }
    }
    
    /**
     * Configura el pull-to-refresh
     */
    function setupPullToRefresh() {
        const mainEl = elements.mainElement;
        if (!mainEl) return;
        
        mainEl.addEventListener('touchstart', function(event) {
            state.touchStartY = event.touches[0].clientY;
        }, { passive: true });
        
        mainEl.addEventListener('touchmove', function(event) {
            const scrollTop = mainEl.scrollTop;
            const isAtTop = scrollTop === 0;
            const currentTouchY = event.touches[0].clientY;
            const hasPulledDown = currentTouchY > state.touchStartY + 50;
            
            if (isAtTop && hasPulledDown && !state.isRefreshing) {
                event.preventDefault();
                refreshOrders();
            }
        }, { passive: false });
    }
    
    /**
     * Configura actualización automática cada N segundos
     */
    function setupAutoRefresh() {
        if (CONFIG.refreshInterval > 0) {
            setInterval(function() {
                // Solo actualizar si la página está visible
                if (document.visibilityState === 'visible') {
                    fetchOrders(state.filter);
                }
            }, CONFIG.refreshInterval);
        }
    }
    
    // ============================================================
    // INICIALIZACIÓN
    // ============================================================
    
    function init() {
        console.log('Inicializando página de pedidos...');
        
        // Configurar eventos
        setupFilters();
        setupRefreshButtons();
        setupPullToRefresh();
        setupAutoRefresh();
        
        // Cargar pedidos iniciales
        fetchOrders(state.filter);
        
        console.log('Página de pedidos inicializada');
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // ============================================================
    // EXPOSICIÓN DE FUNCIONES (para uso en consola)
    // ============================================================
    
    globalThis.Orders = {
        fetchOrders,
        refreshOrders,
        renderOrders,
        state
    };
    
})();