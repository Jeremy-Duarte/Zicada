let isSubmitting = false;
const form = document.getElementById('checkout-form');
const submitBtn = form ? form.querySelector('button[type="submit"]') : null;

if (form && submitBtn) {
    form.addEventListener('submit', function() {
        if (isSubmitting) {
            return false;
        }
        isSubmitting = true;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Procesando...';
    });
}