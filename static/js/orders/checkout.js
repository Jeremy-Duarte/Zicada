(function() {
    'use strict';

    // ============================================
    // DOM ELEMENTS CACHE
    // ============================================
    const elements = {
        payBtn: null,
        customerName: null,
        customerPhone: null,
        customerEmail: null,
        shippingAddress: null,
        deliveryNotes: null
    };

    function cacheElements() {
        elements.payBtn = document.getElementById('pay-now-btn');
        elements.customerName = document.getElementById('customer_name');
        elements.customerPhone = document.getElementById('customer_phone');
        elements.customerEmail = document.getElementById('customer_email');
        elements.shippingAddress = document.getElementById('shipping_address');
        elements.deliveryNotes = document.getElementById('delivery_notes');
    }

    // ============================================
    // CSRF TOKEN
    // ============================================
    function getCookie(name) {
        if (!globalThis.document?.cookie) return null;
        
        const cookies = globalThis.document.cookie.split(';');
        for (const cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if (key === name) {
                return decodeURIComponent(value);
            }
        }
        return null;
    }

    // ============================================
    // FORM VALIDATION
    // ============================================
    function getFormData() {
        if (!elements.customerName || !elements.customerPhone || !elements.shippingAddress) {
            return null;
        }

        const customerName = elements.customerName.value.trim();
        const customerPhone = elements.customerPhone.value.trim();
        const shippingAddress = elements.shippingAddress.value.trim();
        const customerEmail = elements.customerEmail ? elements.customerEmail.value.trim() : '';
        const deliveryNotes = elements.deliveryNotes ? elements.deliveryNotes.value.trim() : '';

        if (!customerName || !customerPhone || !shippingAddress) {
            return null;
        }

        const formData = new FormData();
        formData.append('customer_name', customerName);
        formData.append('customer_phone', customerPhone);
        formData.append('customer_email', customerEmail);
        formData.append('shipping_address', shippingAddress);
        formData.append('delivery_notes', deliveryNotes);

        return formData;
    }

    // ============================================
    // UI STATE MANAGEMENT
    // ============================================
    let isProcessing = false;

    function setProcessingState(isProcessingFlag) {
        isProcessing = isProcessingFlag;
        if (elements.payBtn) {
            elements.payBtn.disabled = isProcessingFlag;
            elements.payBtn.textContent = isProcessingFlag ? 'Procesando...' : 'Pagar ahora';
        }
    }

    // ============================================
    // PAYMENT HANDLER
    // ============================================
    async function handlePayment() {
        if (isProcessing) return;

        const formData = getFormData();
        if (!formData) {
            globalThis.location.reload();
            return;
        }

        setProcessingState(true);

        try {
            const response = await globalThis.fetch(globalThis.checkoutConfig.createSessionUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            const data = await response.json();

            if (data.redirect_url) {
                globalThis.location.href = data.redirect_url;
            } else {
                console.error('Payment error:', data.error);
                globalThis.location.reload();
            }
        } catch (error) {
            console.error('Connection error:', error);
            globalThis.location.reload();
        } finally {
            setProcessingState(false);
        }
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================
    function attachEventListeners() {
        if (elements.payBtn) {
            elements.payBtn.addEventListener('click', handlePayment);
        }
    }

    // ============================================
    // INITIALIZATION
    // ============================================
    function init() {
        cacheElements();
        attachEventListeners();
    }

    if (globalThis.document?.readyState === 'loading') {
        globalThis.document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();