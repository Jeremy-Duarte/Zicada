/**
 * Galería con carrusel infinito + centrado animado al hacer hover.
 * Bloquea hover durante la animación para evitar glitches.
 */
(function () {
    var track = document.getElementById('galleryTrack');
    var prevBtn = document.getElementById('galleryPrev');
    var nextBtn = document.getElementById('galleryNext');
    if (!track || track.children.length < 4) return;

    var position = 0;
    var speed = 0.6;
    var paused = false;
    var raf = null;
    var lastTs = 0;
    var halfway = 0;
    var itemWidth = 0;
    var containerWidth = 0;
    var targetPosition = null;
    var animating = false; // bloquea hover durante la animacion de centrado
    var EASING = 0.08; // factor de easing (0-1, mas bajo = mas suave)

    function measure() {
        halfway = 0;
        var count = track.children.length / 2;
        for (var i = 0; i < count; i++) {
            var child = track.children[i];
            if (child) halfway += child.offsetWidth + 24;
        }
        itemWidth = track.children[0] ? track.children[0].offsetWidth + 24 : 300;
        containerWidth = track.parentElement.clientWidth;
    }

    measure();
    window.addEventListener('resize', function () { measure(); if (!animating) track.style.transform = 'translateX(' + (-position) + 'px)'; });

    function wrapPosition(pos) {
        while (pos >= halfway) pos -= halfway;
        while (pos < 0) pos += halfway;
        return pos;
    }

    function loop(ts) {
        if (!lastTs) lastTs = ts;
        var delta = Math.min(ts - lastTs, 200);

        if (animating && targetPosition !== null) {
            // Easing hacia el centro de la imagen
            position += (targetPosition - position) * EASING;
            if (Math.abs(targetPosition - position) < 0.5) {
                position = targetPosition;
                targetPosition = null;
                animating = false; // re-habilitar hover
            }
        } else if (!paused && !animating) {
            // Auto-scroll normal
            position += speed * (delta / 16);
        }

        position = wrapPosition(position);
        track.style.transform = 'translateX(' + (-position) + 'px)';
        lastTs = ts;
        raf = requestAnimationFrame(loop);
    }

    function pause()  { if (!animating) paused = true; }
    function resume() { paused = false; }

    track.addEventListener('mouseenter', pause);
    track.addEventListener('mouseleave', resume);

    if (prevBtn) prevBtn.addEventListener('click', function () {
        paused = true;
        animating = false;
        targetPosition = null;
        position -= itemWidth;
        position = wrapPosition(position);
        track.style.transform = 'translateX(' + (-position) + 'px)';
    });
    if (nextBtn) nextBtn.addEventListener('click', function () {
        paused = true;
        animating = false;
        targetPosition = null;
        position += itemWidth;
        position = wrapPosition(position);
        track.style.transform = 'translateX(' + (-position) + 'px)';
    });

    // Hover sobre imagen original → centrar con animacion, bloquear hover mientras
    Array.prototype.forEach.call(track.children, function (fig, i) {
        if (i >= track.children.length / 2) return; // solo originales, no clones
        fig.addEventListener('mouseenter', function () {
            if (animating) return;
            paused = true;
            animating = true;
            var offset = fig.offsetLeft - (containerWidth - fig.offsetWidth) / 2;
            targetPosition = wrapPosition(offset);
        });
        fig.addEventListener('mouseleave', function () {
            if (animating) return; // ignorar si la animacion no ha terminado
            paused = false;
        });
    });

    raf = requestAnimationFrame(loop);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
    });
})();
