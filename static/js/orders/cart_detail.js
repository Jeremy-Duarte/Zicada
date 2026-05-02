// ============================================
// UTILIDADES
// ============================================
function formatPrice(price) {
    return new Intl.NumberFormat('es-CO').format(price);
}

function getCsrfToken() {
    return globalThis.cartConfig?.csrfToken || '';
}

function updateGlobalCartCount(count) {
    const cartCountSpan = document.getElementById('cart-count');
    if (cartCountSpan) cartCountSpan.innerText = count;
}

function updateTotals(subtotal, shipping, total) {
    const subtotalEl = document.getElementById('cart-subtotal');
    const shippingEl = document.getElementById('cart-shipping');
    const totalEl = document.getElementById('cart-total');
    
    if (subtotalEl) subtotalEl.innerText = `$${formatPrice(subtotal)}`;
    if (shippingEl) shippingEl.innerText = `$${formatPrice(shipping)}`;
    if (totalEl) totalEl.innerText = `$${formatPrice(total)}`;
}

function updateItemQuantityUI(variantId, newQuantity, newSubtotal) {
    const itemDiv = document.querySelector(`.cart-item[data-variant-id="${variantId}"]`);
    if (!itemDiv) return;
    
    const qtySpan = itemDiv.querySelector('.qty-value');
    if (qtySpan) qtySpan.innerText = newQuantity;
    
    const subtotalSpan = itemDiv.querySelector('.item-subtotal');
    if (subtotalSpan) subtotalSpan.innerText = `$${formatPrice(newSubtotal)}`;
}

function removeItemUI(variantId) {
    const itemDiv = document.querySelector(`.cart-item[data-variant-id="${variantId}"]`);
    if (itemDiv) itemDiv.remove();
    
    const remainingItems = document.querySelectorAll('.cart-item');
    if (remainingItems.length === 0) {
        location.reload();
    }
}

// ============================================
// ACCIONES DEL CARRITO (AJAX)
// ============================================
let isUpdating = false;

async function updateItemQuantity(variantId, newQuantity) {
    if (isUpdating) return;
    isUpdating = true;
    
    const config = globalThis.cartConfig;
    const url = newQuantity <= 0 ? config.removeUrl : config.updateUrl;
    const body = newQuantity <= 0 
        ? { variant_id: variantId }
        : { variant_id: variantId, quantity: newQuantity };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.total_items !== undefined) {
                updateGlobalCartCount(data.total_items);
            }
            
            if (newQuantity <= 0) {
                removeItemUI(variantId);
            } else {
                location.reload();
            }
            
            if (data.subtotal !== undefined && data.shipping_cost !== undefined && data.total !== undefined) {
                updateTotals(data.subtotal, data.shipping_cost, data.total);
            }
        } else {
            alert(data.error || 'Error al actualizar');
            location.reload();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al actualizar el carrito');
        location.reload();
    } finally {
        isUpdating = false;
    }
}

// ============================================
// MANEJADORES DE EVENTOS
// ============================================
function getVariantId(btn) {
    const itemDiv = btn.closest('.cart-item');
    return itemDiv ? Number.parseInt(itemDiv.dataset.variantId, 10) : null;
}

function handleIncrement(e) {
    e.preventDefault();
    const variantId = getVariantId(e.currentTarget);
    if (!variantId) return;
    
    const itemDiv = e.currentTarget.closest('.cart-item');
    const qtySpan = itemDiv.querySelector('.qty-value');
    const currentQty = Number.parseInt(qtySpan.innerText, 10);
    
    updateItemQuantity(variantId, currentQty + 1);
}

function handleDecrement(e) {
    e.preventDefault();
    const variantId = getVariantId(e.currentTarget);
    if (!variantId) return;
    
    const itemDiv = e.currentTarget.closest('.cart-item');
    const qtySpan = itemDiv.querySelector('.qty-value');
    const currentQty = Number.parseInt(qtySpan.innerText, 10);
    
    if (currentQty <= 1) {
        updateItemQuantity(variantId, 0);
    } else {
        updateItemQuantity(variantId, currentQty - 1);
    }
}

function handleRemove(e) {
    e.preventDefault();
    const variantId = getVariantId(e.currentTarget);
    if (!variantId) return;
    updateItemQuantity(variantId, 0);
}

function attachItemEvents() {
    document.querySelectorAll('.qty-incr').forEach(btn => {
        btn.removeEventListener('click', handleIncrement);
        btn.addEventListener('click', handleIncrement);
    });
    
    document.querySelectorAll('.qty-decr').forEach(btn => {
        btn.removeEventListener('click', handleDecrement);
        btn.addEventListener('click', handleDecrement);
    });
    
    document.querySelectorAll('.remove-item').forEach(btn => {
        btn.removeEventListener('click', handleRemove);
        btn.addEventListener('click', handleRemove);
    });
}

// ============================================
// INICIALIZACIÓN
// ============================================
function initCartPage() {
    attachItemEvents();
    
    const checkoutBtn = document.getElementById('checkout-btn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', () => {
            if (globalThis.cartConfig?.checkoutUrl) {
                globalThis.location.href = globalThis.cartConfig.checkoutUrl;
            }
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCartPage);
} else {
    initCartPage();
}