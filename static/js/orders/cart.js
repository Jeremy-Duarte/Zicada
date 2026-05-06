class CartModal {
    modal = null;
    backdrop = null;
    modalBody = null;
    modalFooter = null;
    cartCountSpan = null;
    currentCartData = null;

    constructor() {
        this.init();
    }

    init() {
        this.modal = document.getElementById('cart-modal');
        this.backdrop = document.getElementById('modal-backdrop');
        
        if (!this.modal) return;

        this.modalBody = document.getElementById('cart-modal-body');
        this.modalFooter = document.getElementById('cart-modal-footer');
        this.cartCountSpan = document.getElementById('cart-count');
        
        this.attachGlobalEvents();
        
        if (typeof this.modal.showModal === 'function') {
            this.modal.showModal = () => this.open();
            this.modal.close = () => this.close();
        }
    }

    attachGlobalEvents() {
        const cartIcon = document.getElementById('cart-icon');
        const closeBtn = document.getElementById('close-modal');

        if (cartIcon) {
            cartIcon.addEventListener('click', (e) => {
                e.preventDefault();
                this.open();
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        if (this.backdrop) {
            this.backdrop.addEventListener('click', () => this.close());
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal && !this.modal.classList.contains('hidden')) {
                this.close();
            }
        });
    }

    open() {
        this.modal.classList.remove('hidden');
        if (this.backdrop) this.backdrop.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        this.modal.focus();
        
        this.loadCartData();
    }

    close() {
        this.modal.classList.add('hidden');
        if (this.backdrop) this.backdrop.classList.add('hidden');
        document.body.style.overflow = '';
        
        const cartIcon = document.getElementById('cart-icon');
        if (cartIcon) cartIcon.focus();
    }

    loadCartData() {
        const url = this.modal.dataset.cartUrl || '/orders/carrito/datos/';
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.currentCartData = data;
                this.render(data);
            })
            .catch(error => {
                console.error('Error al cargar carrito:', error);
                if (this.modalBody) {
                    this.modalBody.innerHTML = `
                        <div class="text-center py-8 text-red-600">
                            Error al cargar el carrito. Intente de nuevo.
                        </div>
                    `;
                }
                if (this.modalFooter) {
                    this.modalFooter.innerHTML = '';
                }
            });
    }

    render(data) {
        const { items, subtotal, shipping_cost, total, is_empty, total_items } = data;
        
        if (is_empty) {
            this.renderEmptyCart();
            return;
        }

        // Actualizar contador global
        if (this.cartCountSpan && total_items !== undefined) {
            this.cartCountSpan.innerText = total_items;
        }

        this.renderItems(items);
        this.renderFooter(subtotal, shipping_cost, total);
        this.attachItemEvents();
    }

    renderEmptyCart() {
        if (this.modalBody) {
            this.modalBody.innerHTML = `
                <div class="text-center py-12">
                    <svg class="mx-auto h-20 w-20 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-1.5 6M17 13l1.5 6M9 21h6M6 21h.01M18 21h.01" />
                    </svg>
                    <p class="mt-4 text-gray-500 text-lg">Tu carrito está vacío</p>
                    <p class="text-sm text-gray-400 mt-1">¡Agrega productos para comenzar!</p>
                    <button id="continue-shopping-empty" class="mt-6 bg-zicada-accent text-white px-6 py-2.5 rounded-lg font-medium hover:bg-opacity-90 transition shadow-sm">
                        Seguir comprando
                    </button>
                </div>
            `;
        }
        
        if (this.modalFooter) {
            this.modalFooter.innerHTML = '';
        }

        const continueBtn = document.getElementById('continue-shopping-empty');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => this.close());
        }
    }

    renderItems(items) {
        if (!this.modalBody) return;

        this.modalBody.innerHTML = items.map(item => `
            <div class="cart-item flex gap-4 mb-4 pb-4 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition rounded-lg p-2 -mx-2" data-variant-id="${item.variant_id}">
                <img src="${item.image || this.getPlaceholderImage()}" 
                     alt="${this.escapeHtml(item.product_name)}" 
                     class="w-20 h-20 object-cover rounded-lg bg-gray-100 shadow-sm"
                     onerror="this.src='${this.getPlaceholderImage()}'">
                <div class="flex-1">
                    <h4 class="font-semibold text-gray-900">${this.escapeHtml(item.product_name)}</h4>
                    <p class="text-sm text-gray-500 mt-0.5">
                        Talla: ${this.escapeHtml(item.size_name)} | Color: ${this.escapeHtml(item.color_name)}
                    </p>
                    <div class="flex items-center justify-between mt-3">
                        <div class="flex items-center gap-2 bg-gray-100 rounded-full px-1 py-0.5">
                            <button class="qty-decr w-7 h-7 bg-white hover:bg-gray-200 text-gray-700 rounded-full transition shadow-sm flex items-center justify-center font-bold">−</button>
                            <span class="qty-value w-8 text-center font-medium text-gray-900 text-sm">${item.quantity}</span>
                            <button class="qty-incr w-7 h-7 bg-white hover:bg-gray-200 text-gray-700 rounded-full transition shadow-sm flex items-center justify-center font-bold">+</button>
                        </div>
                        <div class="font-bold text-gray-900">$${(item.price * item.quantity).toLocaleString('es-CO')}</div>
                        <button class="remove-item text-red-400 hover:text-red-600 transition p-1 rounded-full hover:bg-red-50" title="Eliminar">
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
        if (!this.modalFooter) return;

        const subtotalFormatted = subtotal.toLocaleString('es-CO');
        const shippingFormatted = shipping_cost.toLocaleString('es-CO');
        const totalFormatted = total.toLocaleString('es-CO');
        const isFreeShipping = shipping_cost === 0 && subtotal > 0;
        const remainingForFree = 150000 - subtotal;
        
        let shippingMessage = '';
        if (subtotal > 0) {
            if (!isFreeShipping) {
                shippingMessage = `
                    <div class="bg-amber-50 rounded-lg p-3 text-sm">
                        <p class="text-amber-700 flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Faltan $${remainingForFree.toLocaleString('es-CO')} para envío gratis
                        </p>
                    </div>
                `;
            } else if (isFreeShipping) {
                shippingMessage = `
                    <div class="bg-green-50 rounded-lg p-3 text-sm">
                        <p class="text-green-700 flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            ¡Envío gratis aplicado!
                        </p>
                    </div>
                `;
            }
        }
        
        const shippingText = isFreeShipping ? 'GRATIS' : `$${shippingFormatted}`;

        this.modalFooter.innerHTML = `
            <div class="space-y-3">
                ${shippingMessage}
                
                <div class="flex justify-between text-gray-700 text-sm">
                    <span>Subtotal</span>
                    <span class="font-medium">$${subtotalFormatted}</span>
                </div>
                <div class="flex justify-between text-gray-700 text-sm">
                    <span>Envío</span>
                    <span class="font-medium">${shippingText}</span>
                </div>
                <div class="flex justify-between text-lg font-bold text-gray-900 pt-3 border-t border-gray-200">
                    <span>Total</span>
                    <span class="text-zicada-accent">$${totalFormatted}</span>
                </div>
                
                <div class="grid grid-cols-3 gap-2 pt-4">
                    <button id="clear-cart-btn" class="text-red-500 hover:text-red-700 text-sm font-medium py-2.5 rounded-lg hover:bg-red-50 transition flex items-center justify-center gap-1">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Vaciar
                    </button>
                    <button id="goto-cart-btn" class="col-span-2 bg-zicada-accent text-white py-2.5 rounded-lg font-semibold hover:bg-opacity-90 transition shadow-sm">
                        Ver carrito completo
                    </button>
                </div>
                <button id="close-modal-footer-btn" class="w-full border border-gray-300 text-gray-600 py-2 rounded-lg font-medium hover:bg-gray-50 transition text-sm">
                    Seguir comprando
                </button>
            </div>
        `;

        // Eventos del footer
        const clearCartBtn = document.getElementById('clear-cart-btn');
        const gotoCartBtn = document.getElementById('goto-cart-btn');
        const closeFooterBtn = document.getElementById('close-modal-footer-btn');

        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', () => this.clearCart());
        }
        if (gotoCartBtn) {
            gotoCartBtn.addEventListener('click', () => {
                globalThis.location.href = this.modal.dataset.cartDetailUrl || '/orders/carrito/';
            });
        }
        if (closeFooterBtn) {
            closeFooterBtn.addEventListener('click', () => this.close());
        }
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
        return itemDiv ? Number.parseInt(itemDiv.dataset.variantId) : null;
    }

    handleIncrement(e) {
        e.preventDefault();
        const variantId = this.getVariantIdFromButton(e.currentTarget);
        if (!variantId) return;
        this.updateItemQuantity(variantId, 'increase');
    }

    handleDecrement(e) {
        e.preventDefault();
        const variantId = this.getVariantIdFromButton(e.currentTarget);
        if (!variantId) return;
        this.updateItemQuantity(variantId, 'decrease');
    }

    handleRemove(e) {
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
            let currentQty = Number.parseInt(qtySpan.innerText);
            url = this.modal.dataset.cartUpdateUrl || '/orders/carrito/actualizar/';
            body = { variant_id: variantId, quantity: currentQty + 1 };
        } else if (action === 'decrease') {
            const itemDiv = document.querySelector(`[data-variant-id="${variantId}"]`);
            if (!itemDiv) return;
            const qtySpan = itemDiv.querySelector('.qty-value');
            if (!qtySpan) return;
            let currentQty = Number.parseInt(qtySpan.innerText);
            if (currentQty <= 1) {
                action = 'remove';
            } else {
                url = this.modal.dataset.cartUpdateUrl || '/orders/carrito/actualizar/';
                body = { variant_id: variantId, quantity: currentQty - 1 };
            }
        }
        
        if (action === 'remove') {
            url = this.modal.dataset.cartRemoveUrl || '/orders/carrito/eliminar/';
            body = { variant_id: variantId };
        }

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: JSON.stringify(body)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.total_items !== undefined && this.cartCountSpan) {
                    this.cartCountSpan.innerText = data.total_items;
                }
                this.loadCartData();
            } else {
                alert(data.error || 'Error al actualizar');
                this.loadCartData();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.loadCartData();
        });
    }

    clearCart() {
        if (!confirm('¿Estás seguro de que deseas vaciar todo tu carrito?')) {
            return;
        }

        const url = this.modal.dataset.cartClearUrl || '/orders/carrito/vaciar/';
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (this.cartCountSpan) {
                    this.cartCountSpan.innerText = '0';
                }
                this.loadCartData();
            } else {
                alert(data.error || 'Error al vaciar el carrito');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al vaciar el carrito');
        });
    }

    getCookie(name) {
        if (!document.cookie || document.cookie === '') return null;
        
        const cookie = document.cookie.split(';')
            .find(c => c.trim().startsWith(name + '='));
        
        if (!cookie) return null;
        
        return decodeURIComponent(cookie.trim().substring(name.length + 1));
    }

    getPlaceholderImage() {
        return '/static/img/product-placeholder.jpeg';
    }

    escapeHtml(str) {
        if (!str) return '';
        return str.replaceAll(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    globalThis.cartModal = new CartModal();
});