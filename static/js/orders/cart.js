class CartSidebar {
    sidebar = null;
    backdrop = null;
    body = null;
    footer = null;
    cartCountSpan = null;
    currentCartData = null;
    toastTimeout = null;

    constructor() {
        this.init();
    }

    init() {
        this.sidebar = document.getElementById('cart-sidebar');
        if (!this.sidebar) return;

        this.backdrop = document.getElementById('cart-backdrop');
        this.body = document.getElementById('cart-sidebar-body');
        this.footer = document.getElementById('cart-sidebar-footer');
        this.cartCountSpan = document.getElementById('cart-count');
        
        this.attachEvents();
    }

    // Sistema de notificaciones toast
    showToast(message, type = 'success') {
        const container = document.getElementById('cart-toast-container');
        if (!container) return;

        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-amber-500',
            info: 'bg-blue-500'
        };

        const icons = {
            success: `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
            `,
            error: `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            `,
            warning: `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
            `,
            info: `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            `
        };

        const toast = document.createElement('div');
        toast.className = `pointer-events-auto ${colors[type]} text-white rounded-lg shadow-lg p-3 flex items-center gap-3 transform transition-all duration-300 translate-x-full opacity-0`;
        toast.innerHTML = `
            <div class="flex-shrink-0">${icons[type]}</div>
            <div class="flex-1 text-sm font-medium">${message}</div>
            <button class="toast-close flex-shrink-0 hover:opacity-75 transition">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        `;

        container.appendChild(toast);

        // Animación de entrada
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
            toast.classList.add('translate-x-0', 'opacity-100');
        }, 10);

        // Botón cerrar
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));

        // Auto-cerrar después de 3 segundos
        const timeoutId = setTimeout(() => this.removeToast(toast), 3000);
        
        // Guardar timeout para limpiar si es necesario
        toast.dataset.timeoutId = timeoutId;
    }

    removeToast(toast) {
        if (toast.dataset.timeoutId) {
            clearTimeout(Number.parseInt(toast.dataset.timeoutId, 10));
        }
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }

    attachEvents() {
        const cartIcon = document.getElementById('cart-icon');
        const closeBtn = document.getElementById('close-sidebar');

        if (cartIcon) {
            cartIcon.addEventListener('click', (e) => {
                e.preventDefault();
                this.open();
            });
        }
        if (closeBtn) closeBtn.addEventListener('click', () => this.close());
        if (this.backdrop) this.backdrop.addEventListener('click', () => this.close());

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.sidebar && !this.sidebar.classList.contains('hidden')) {
                this.close();
            }
        });
    }

    open() {
        if (!this.sidebar) return;
        this.sidebar.classList.remove('hidden');
        
        setTimeout(() => {
            const content = document.getElementById('cart-sidebar-content');
            if (content) content.classList.remove('translate-x-full');
        }, 10);
        
        if (this.backdrop) {
            this.backdrop.classList.remove('bg-opacity-0');
            this.backdrop.classList.add('bg-opacity-50');
        }
        
        document.body.style.overflow = 'hidden';
        this.loadCartData();
    }

    close() {
        const content = document.getElementById('cart-sidebar-content');
        if (content) {
            content.classList.add('translate-x-full');
            setTimeout(() => {
                if (this.sidebar) this.sidebar.classList.add('hidden');
                if (this.backdrop) {
                    this.backdrop.classList.remove('bg-opacity-50');
                    this.backdrop.classList.add('bg-opacity-0');
                }
                document.body.style.overflow = '';
            }, 300);
        } else {
            if (this.sidebar) this.sidebar.classList.add('hidden');
            if (this.backdrop) {
                this.backdrop.classList.remove('bg-opacity-50');
                this.backdrop.classList.add('bg-opacity-0');
            }
            document.body.style.overflow = '';
        }
    }

    loadCartData() {
        const url = this.sidebar.dataset.cartUrl || '/orders/carrito/datos/';
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.currentCartData = data;
                this.render(data);
            })
            .catch(error => {
                console.error('Error al cargar carrito:', error);
                if (this.body) {
                    this.body.innerHTML = `
                        <div class="text-center py-8 text-red-600">
                            Error al cargar el carrito. Intente de nuevo.
                        </div>
                    `;
                }
                if (this.footer) this.footer.innerHTML = '';
            });
    }

    render(data) {
        const { items, subtotal, shipping_cost, total, is_empty, total_items } = data;
        
        if (is_empty) {
            this.renderEmptyCart();
            return;
        }

        if (this.cartCountSpan && total_items !== undefined) {
            this.cartCountSpan.innerText = total_items;
        }
        
        const sidebarCount = document.getElementById('cart-sidebar-count');
        if (sidebarCount) sidebarCount.innerText = total_items;

        this.renderItems(items);
        this.renderFooter(subtotal, shipping_cost, total);
        this.attachItemEvents();
    }

    renderEmptyCart() {
        if (this.body) {
            this.body.innerHTML = `
                <div class="text-center py-12">
                    <svg class="mx-auto h-20 w-20 text-neutral-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-1.5 6M17 13l1.5 6M9 21h6M6 21h.01M18 21h.01" />
                    </svg>
                    <p class="mt-4 text-neutral-400 text-lg">Tu carrito está vacío</p>
                    <p class="text-sm text-neutral-500 mt-1">¡Agrega productos para comenzar!</p>
                    <button id="continue-shopping-empty" class="mt-6 bg-zicada-accent text-white px-6 py-2.5 rounded-lg font-medium hover:bg-zicada-accent/90 transition shadow-sm">
                        Seguir comprando
                    </button>
                </div>
            `;
        }
        if (this.footer) this.footer.innerHTML = '';

        const continueBtn = document.getElementById('continue-shopping-empty');
        if (continueBtn) continueBtn.addEventListener('click', () => this.close());
    }

    renderItems(items) {
        if (!this.body) return;
        this.body.innerHTML = items.map(item => `
            <div class="cart-item flex gap-4 mb-4 pb-4 border-b border-neutral-800 last:border-0 hover:bg-neutral-900 transition rounded-lg p-2 -mx-2" data-variant-id="${item.variant_id}">
                <img src="${item.image || this.getPlaceholderImage()}" 
                     alt="${this.escapeHtml(item.product_name)}" 
                     class="w-20 h-20 object-cover rounded-lg bg-neutral-900 shadow-sm"
                     onerror="this.src='${this.getPlaceholderImage()}'">
                <div class="flex-1 min-w-0">
                    <h4 class="font-semibold text-white truncate">${this.escapeHtml(item.product_name)}</h4>
                    <p class="text-sm text-neutral-400 mt-0.5">
                        Talla: ${this.escapeHtml(item.size_name)} | ${this.escapeHtml(item.color_name)}
                    </p>
                    <div class="flex items-center justify-between mt-3 gap-2">
                        <div class="flex items-center gap-2 bg-neutral-800 rounded-full px-1 py-0.5 flex-shrink-0">
                            <button class="qty-decr w-7 h-7 bg-neutral-900 hover:bg-neutral-700 text-neutral-300 rounded-full transition shadow-sm flex items-center justify-center font-bold">−</button>
                            <span class="qty-value w-8 text-center font-medium text-white text-sm">${item.quantity}</span>
                            <button class="qty-incr w-7 h-7 bg-neutral-900 hover:bg-neutral-700 text-neutral-300 rounded-full transition shadow-sm flex items-center justify-center font-bold">+</button>
                        </div>
                        <div class="font-bold text-zicada-accent flex-shrink-0">$${(item.price * item.quantity).toLocaleString('es-CO')}</div>
                        <button class="remove-item text-neutral-500 hover:text-zicada-accent transition p-1 rounded-full hover:bg-neutral-800 flex-shrink-0" title="Eliminar">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderFooter(subtotal, shipping_cost, total) {
        if (!this.footer) return;

        const subtotalFormatted = subtotal.toLocaleString('es-CO');
        const shippingFormatted = shipping_cost.toLocaleString('es-CO');
        const totalFormatted = total.toLocaleString('es-CO');
        const isFreeShipping = shipping_cost === 0 && subtotal > 0;
        const remainingForFree = 150000 - subtotal;
        
        let shippingMessage = '';
        
        if (subtotal > 0) {
            if (isFreeShipping) {
                shippingMessage = `
                    <div class="bg-neutral-800 rounded-lg p-3 text-sm">
                        <p class="text-green-400 flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            ¡Envío gratis aplicado!
                        </p>
                    </div>
                `;
            } else {
                shippingMessage = `
                    <div class="bg-neutral-800 rounded-lg p-3 text-sm">
                        <p class="text-amber-400 flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Faltan $${remainingForFree.toLocaleString('es-CO')} para envío gratis
                        </p>
                    </div>
                `;
            }
        }
        
        const shippingText = isFreeShipping ? 'GRATIS' : `$${shippingFormatted}`;

        this.footer.innerHTML = `
            <div class="space-y-3">
                ${shippingMessage}
                
                <div class="flex justify-between text-neutral-300 text-sm">
                    <span>Subtotal</span>
                    <span class="font-medium text-white">$${subtotalFormatted}</span>
                </div>
                <div class="flex justify-between text-neutral-300 text-sm">
                    <span>Envío</span>
                    <span class="font-medium text-white">${shippingText}</span>
                </div>
                <div class="flex justify-between text-lg font-bold text-white pt-3 border-t border-neutral-800">
                    <span>Total</span>
                    <span class="text-zicada-accent">$${totalFormatted}</span>
                </div>
                
                <div class="grid grid-cols-3 gap-2 pt-4">
                    <button id="clear-cart-btn" class="text-neutral-400 hover:text-zicada-accent text-sm font-medium py-2.5 rounded-lg hover:bg-neutral-800 transition flex items-center justify-center gap-1">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Vaciar
                    </button>
                    <button id="goto-cart-btn" class="col-span-2 bg-zicada-accent text-white py-2.5 rounded-lg font-semibold hover:bg-zicada-accent/90 transition shadow-sm">
                        Ver carrito completo
                    </button>
                </div>
                <button id="close-sidebar-footer-btn" class="w-full border border-neutral-700 text-neutral-400 py-2 rounded-lg font-medium hover:border-neutral-500 hover:text-white transition text-sm">
                    Seguir comprando
                </button>
            </div>
        `;

        const clearCartBtn = document.getElementById('clear-cart-btn');
        const gotoCartBtn = document.getElementById('goto-cart-btn');
        const closeFooterBtn = document.getElementById('close-sidebar-footer-btn');

        if (clearCartBtn) clearCartBtn.addEventListener('click', () => this.clearCart());
        if (gotoCartBtn) {
            gotoCartBtn.addEventListener('click', () => {
                globalThis.location.href = this.sidebar.dataset.cartDetailUrl || '/orders/carrito/';
            });
        }
        if (closeFooterBtn) closeFooterBtn.addEventListener('click', () => this.close());
    }

    attachItemEvents() {
        document.querySelectorAll('.qty-incr').forEach(btn => {
            btn.removeEventListener('click', this.handleIncrement);
            btn.addEventListener('click', (e) => this.handleIncrement(e));
        });
        document.querySelectorAll('.qty-decr').forEach(btn => {
            btn.removeEventListener('click', this.handleDecrement);
            btn.addEventListener('click', (e) => this.handleDecrement(e));
        });
        document.querySelectorAll('.remove-item').forEach(btn => {
            btn.removeEventListener('click', this.handleRemove);
            btn.addEventListener('click', (e) => this.handleRemove(e));
        });
    }

    getVariantIdFromButton(btn) {
        const itemDiv = btn.closest('[data-variant-id]');
        return itemDiv ? Number.parseInt(itemDiv.dataset.variantId, 10) : null;
    }

    handleIncrement = (e) => {
        e.preventDefault();
        const variantId = this.getVariantIdFromButton(e.currentTarget);
        if (!variantId) return;
        this.updateItemQuantity(variantId, 'increase');
    }

    handleDecrement = (e) => {
        e.preventDefault();
        const variantId = this.getVariantIdFromButton(e.currentTarget);
        if (!variantId) return;
        this.updateItemQuantity(variantId, 'decrease');
    }

    handleRemove = (e) => {
        e.preventDefault();
        const variantId = this.getVariantIdFromButton(e.currentTarget);
        if (!variantId) return;
        this.updateItemQuantity(variantId, 'remove');
    }

    updateItemQuantity(variantId, action) {
        let url = '';
        let body = {};
        
        if (action === 'increase') {
            const itemDiv = document.querySelector(`[data-variant-id="${variantId}"]`);
            if (!itemDiv) return;
            const qtySpan = itemDiv.querySelector('.qty-value');
            if (!qtySpan) return;
            const currentQty = Number.parseInt(qtySpan.innerText, 10);
            url = this.sidebar.dataset.cartUpdateUrl || '/orders/carrito/actualizar/';
            body = { variant_id: variantId, quantity: currentQty + 1 };
        } else if (action === 'decrease') {
            const itemDiv = document.querySelector(`[data-variant-id="${variantId}"]`);
            if (!itemDiv) return;
            const qtySpan = itemDiv.querySelector('.qty-value');
            if (!qtySpan) return;
            const currentQty = Number.parseInt(qtySpan.innerText, 10);
            if (currentQty <= 1) {
                action = 'remove';
            } else {
                url = this.sidebar.dataset.cartUpdateUrl || '/orders/carrito/actualizar/';
                body = { variant_id: variantId, quantity: currentQty - 1 };
            }
        }
        
        if (action === 'remove') {
            url = this.sidebar.dataset.cartRemoveUrl || '/orders/carrito/eliminar/';
            body = { variant_id: variantId };
        }

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this._csrfToken()
            },
            body: JSON.stringify(body)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.total_items !== undefined && this.cartCountSpan) {
                    this.cartCountSpan.innerText = data.total_items;
                }
                // Mostrar notificación de éxito
                if (data.message) {
                    this.showToast(data.message, 'success');
                } else if (action === 'increase') {
                    this.showToast('Producto actualizado correctamente', 'success');
                } else if (action === 'decrease') {
                    this.showToast('Cantidad actualizada', 'success');
                } else if (action === 'remove') {
                    this.showToast('Producto eliminado del carrito', 'success');
                }
                this.loadCartData();
            } else {
                // Mostrar error en toast en lugar de alert
                this.showToast(data.error || 'Error al actualizar el carrito', 'error');
                this.loadCartData();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showToast('Error de conexión al servidor', 'error');
            this.loadCartData();
        });
    }

    clearCart() {
        // Reemplazar confirm nativo por un diálogo personalizado
        this.showConfirmDialog(
            '¿Vaciar carrito?',
            'Todos los productos serán eliminados. ¿Estás seguro?',
            () => {
                const url = this.sidebar.dataset.cartClearUrl || '/orders/carrito/vaciar/';
                
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this._csrfToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (this.cartCountSpan) this.cartCountSpan.innerText = '0';
                        this.showToast(data.message || 'Carrito vaciado correctamente', 'success');
                        this.loadCartData();
                    } else {
                        this.showToast(data.error || 'Error al vaciar el carrito', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    this.showToast('Error al vaciar el carrito', 'error');
                });
            }
        );
    }

    // Diálogo de confirmación personalizado (sin alert nativo)
    showConfirmDialog(title, message, onConfirm) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';
        modal.innerHTML = `
            <div class="bg-neutral-900 rounded-2xl shadow-2xl max-w-sm w-full mx-4 transform transition-all border border-neutral-800">
                <div class="p-6">
                    <h3 class="text-lg font-bold text-white mb-2">${title}</h3>
                    <p class="text-neutral-400 mb-6">${message}</p>
                    <div class="flex gap-3">
                        <button id="confirm-cancel" class="flex-1 px-4 py-2 border border-neutral-700 rounded-lg text-neutral-300 hover:bg-neutral-800 hover:text-white transition">
                            Cancelar
                        </button>
                        <button id="confirm-ok" class="flex-1 px-4 py-2 bg-zicada-accent text-white rounded-lg hover:bg-zicada-accent/90 transition">
                            Vaciar
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const cancelBtn = modal.querySelector('#confirm-cancel');
        const confirmBtn = modal.querySelector('#confirm-ok');

        const closeModal = () => modal.remove();

        cancelBtn.addEventListener('click', closeModal);
        confirmBtn.addEventListener('click', () => {
            closeModal();
            onConfirm();
        });

        // Cerrar con ESC
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }

    _csrfToken() {
        const config = globalThis.cartConfig;
        if (config && config.csrfToken) {
            return config.csrfToken;
        }
        return this.getCookie('csrftoken');
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (const cookie of cookies) {
                const trimmedCookie = cookie.trim();
                if (trimmedCookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(trimmedCookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    getPlaceholderImage() {
        return '/static/img/product-placeholder.jpeg';
    }

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, (match) => {
            if (match === '&') return '&amp;';
            if (match === '<') return '&lt;';
            if (match === '>') return '&gt;';
            return match;
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    globalThis.cartSidebar = new CartSidebar();
});