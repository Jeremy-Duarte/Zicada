// Radio cards
document.querySelectorAll('input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', function() {
        document.querySelectorAll('.incidence-card').forEach(card => {
            card.classList.remove('border-black', 'bg-gray-50');
            card.classList.add('border-gray-200');
        });
        document.querySelectorAll('.w-6.h-6 > div').forEach(dot => dot.classList.add('scale-0'));
        if (this.checked) {
            const card = this.nextElementSibling;
            card.classList.remove('border-gray-200');
            card.classList.add('border-black', 'bg-gray-50');
            const dot = card.querySelector('.w-6.h-6 > div');
            if (dot) dot.classList.remove('scale-0');
        }
    });
});

// Confirmar envío
document.getElementById('incidenceForm')?.addEventListener('submit', (e) => {
    const selected = document.querySelector('input[name="incidence_type"]:checked');
    if (!selected) {
        e.preventDefault();
        alert('Por favor selecciona un tipo de incidencia');
        return;
    }
    const label = selected.nextElementSibling.querySelector('.font-medium').textContent;
    if (!confirm(`¿Confirmas reportar esta incidencia?\n\nTipo: ${label}\n\nEl pedido será cancelado y el administrador será notificado.`))
        e.preventDefault();
});