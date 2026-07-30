/**
 * Galería con carrusel infinito suave.
 * Transform translateX + dos sets de imágenes para loop continuo.
 */
(function () {
    var track = document.getElementById('galleryTrack');
    var prevBtn = document.getElementById('galleryPrev');
    var nextBtn = document.getElementById('galleryNext');
    if (!track || track.children.length < 4) return;

    var position = 0;
    var speed = 0.6; // píxeles por frame (~36px/s)
    var paused = false;
    var raf = null;
    var lastTs = 0;
    var halfway = 0; // ancho del primer set (posición de reinicio)
    var itemWidth = 0;

    function measure() {
        halfway = 0;
        var count = track.children.length / 2;
        for (var i = 0; i < count; i++) {
            var child = track.children[i];
            if (child) {
                halfway += child.offsetWidth + 24; // gap-6 = 24px
            }
        }
        itemWidth = track.children[0] ? track.children[0].offsetWidth + 24 : 300;
    }

    measure();
    window.addEventListener('resize', measure);

    function loop(ts) {
        if (!lastTs) lastTs = ts;
        var delta = Math.min(ts - lastTs, 200);
        if (!paused) {
            position += speed * (delta / 16);
            if (position >= halfway) position -= halfway;
            else if (position < 0) position += halfway;
            track.style.transform = 'translateX(' + (-position) + 'px)';
        }
        lastTs = ts;
        raf = requestAnimationFrame(loop);
    }

    function pause()  { paused = true; }
    function resume() { paused = false; }

    track.addEventListener('mouseenter', pause);
    track.addEventListener('mouseleave', resume);

    if (prevBtn) prevBtn.addEventListener('click', function () {
        paused = true;
        position -= itemWidth;
        if (position < 0) position += halfway;
        track.style.transform = 'translateX(' + (-position) + 'px)';
    });
    if (nextBtn) nextBtn.addEventListener('click', function () {
        paused = true;
        position += itemWidth;
        if (position >= halfway) position -= halfway;
        track.style.transform = 'translateX(' + (-position) + 'px)';
    });

    // Hover sobre imagen original → centrar
    Array.prototype.forEach.call(track.children, function (fig, i) {
        if (i >= track.children.length / 2) return; // solo originales
        fig.addEventListener('mouseenter', function () {
            paused = true;
            var offset = fig.offsetLeft - (track.parentElement.clientWidth - fig.offsetWidth) / 2;
            position = offset;
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        fig.addEventListener('mouseleave', function () {
            paused = false;
        });
    });

    raf = requestAnimationFrame(loop);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
    });
})();
