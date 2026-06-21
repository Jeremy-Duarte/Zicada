// ==================== INCIDENCE.JS - FORMULARIO DE INCIDENCIAS ====================

(function () {
    'use strict';

    /**
     * Actualiza la apariencia visual de las tarjetas de tipo de incidencia
     * cuando se selecciona un radio button.
     */
    function setupRadioCards() {
        var radios = document.querySelectorAll('input[type="radio"][name="incidence_type"]');

        radios.forEach(function (radio) {
            radio.addEventListener('change', function () {
                // Resetear todas las tarjetas
                document.querySelectorAll('.incidence-card').forEach(function (card) {
                    card.classList.remove('border-black', 'bg-gray-50');
                    card.classList.add('border-gray-200');
                });
                document.querySelectorAll('.w-6.h-6 > div').forEach(function (dot) {
                    dot.classList.add('scale-0');
                });

                // Activar la tarjeta seleccionada
                if (this.checked) {
                    var card = this.nextElementSibling;
                    if (card) {
                        card.classList.remove('border-gray-200');
                        card.classList.add('border-black', 'bg-gray-50');
                        var dot = card.querySelector('.w-6.h-6 > div');
                        if (dot) {
                            dot.classList.remove('scale-0');
                        }
                    }
                }
            });
        });
    }

    /**
     * Configura la validación y confirmación del formulario de incidencias.
     */
    function setupIncidenceForm() {
        var form = document.getElementById('incidenceForm');
        if (!form) {
            return;
        }

        form.addEventListener('submit', function (event) {
            var selected = document.querySelector('input[name="incidence_type"]:checked');

            if (!selected) {
                event.preventDefault();
                if (globalThis.showToast) {
                    globalThis.showToast('Por favor selecciona un tipo de incidencia', 'error');
                }
                return;
            }

            var labelEl = selected.nextElementSibling
                ? selected.nextElementSibling.querySelector('.font-medium')
                : null;
            var label = labelEl ? labelEl.textContent.trim() : selected.value;

            var message = '¿Confirmas reportar esta incidencia?\n\nTipo: ' + label + '\n\nSi seleccionas cancelar, el pedido será cancelado.';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            setupRadioCards();
            setupIncidenceForm();
        });
    } else {
        setupRadioCards();
        setupIncidenceForm();
    }

})();
