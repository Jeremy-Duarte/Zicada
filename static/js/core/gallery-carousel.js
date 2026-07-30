/**
 * Galería con carrusel infinito suave.
 * Hover pausa, click centra + cooldown 500ms, flechas navegan.
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

    var targetPos = null;
    var EASING = 0.08;
    var cooldown = false;
    var cdTimer = null;
    var CD_MS = 450; // tiempo muerto anti-sobreclick
    var activeFig = null;

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

    function wrap(pos) {
        while (pos >= halfway) pos -= halfway;
        while (pos < 0) pos += halfway;
        return pos;
    }

    measure();
    window.addEventListener('resize', function () {
        measure();
        track.style.transform = 'translateX(' + (-position) + 'px)';
    });

    function loop(ts) {
        if (!lastTs) lastTs = ts;
        var delta = Math.min(ts - lastTs, 200);

        if (targetPos !== null) {
            position += (targetPos - position) * EASING;
            if (Math.abs(targetPos - position) < 0.5) {
                position = targetPos;
                targetPos = null;
            }
        } else if (!paused) {
            position += speed * (delta / 16);
        }

        position = wrap(position);
        track.style.transform = 'translateX(' + (-position) + 'px)';
        lastTs = ts;
        raf = requestAnimationFrame(loop);
    }

    function pause()  { paused = true; }
    function resume() { paused = false; }

    track.addEventListener('mouseenter', pause);
    track.addEventListener('mouseleave', resume);

    if (prevBtn) {
        prevBtn.addEventListener('click', function () {
            targetPos = null;
            position -= itemWidth;
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        prevBtn.addEventListener('mouseenter', pause);
        prevBtn.addEventListener('mouseleave', resume);
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', function () {
            targetPos = null;
            position += itemWidth;
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        nextBtn.addEventListener('mouseenter', pause);
        nextBtn.addEventListener('mouseleave', resume);
    }

    // Click sobre imagen original → centrar con animacion + cooldown
    Array.prototype.forEach.call(track.children, function (fig, i) {
        if (i >= track.children.length / 2) return; // solo originales, no clones

        fig.addEventListener('click', function (e) {
            if (cooldown) return;
            cooldown = true;
            paused = true;

            if (activeFig) activeFig.style.pointerEvents = '';
            activeFig = fig;
            activeFig.style.pointerEvents = 'none';

            clearTimeout(cdTimer);
            cdTimer = setTimeout(function () {
                cooldown = false;
                if (activeFig) activeFig.style.pointerEvents = '';
                activeFig = null;
            }, CD_MS);

            var offset = fig.offsetLeft - (containerWidth - fig.offsetWidth) / 2;
            targetPos = wrap(offset);
        });
    });

    raf = requestAnimationFrame(loop);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
        clearTimeout(cdTimer);
    });
})();
