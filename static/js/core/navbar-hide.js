/**
 * Auto-hide del navbar + breadcrumbs al hacer scroll hacia abajo.
 * Reaparecen al subir. Mejora el espacio visible durante la navegacion.
 */
(function () {
    var header = document.getElementById('site-header');
    if (!header) {
        return;
    }

    var lastScroll = 0;
    var ticking = false;
    var HIDE_THRESHOLD = 120;

    function onScroll() {
        if (ticking) {
            return;
        }
        ticking = true;
        window.requestAnimationFrame(function () {
            var current = window.scrollY;
            if (current > lastScroll && current > HIDE_THRESHOLD) {
                header.classList.add('-translate-y-full');
            } else {
                header.classList.remove('-translate-y-full');
            }
            lastScroll = current;
            ticking = false;
        });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
})();
