/**
 * Galería auto-deslizante con pausa en hover.
 * RequestAnimationFrame para scroll suave, cache de elementos DOM,
 * limpieza en beforeunload.
 */
(function () {
    var track = document.getElementById('galleryTrack');
    if (!track || track.children.length === 0) return;

    var speed = 0.8; // píxeles por frame (~60fps → 48px/s)
    var paused = false;
    var lastTs = 0;
    var raf = null;
    var prevBtn = document.getElementById('galleryPrev');
    var nextBtn = document.getElementById('galleryNext');

    function slide(ts) {
        if (!lastTs) lastTs = ts;
        var delta = ts - lastTs;
        if (!paused && delta < 200) {
            track.scrollLeft += speed * (delta / 16);
            if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 1) {
                track.scrollLeft = 0;
            }
        }
        lastTs = ts;
        raf = requestAnimationFrame(slide);
    }

    function pause()  { paused = true; }
    function resume() { paused = false; }

    track.addEventListener('mouseenter', pause);
    track.addEventListener('mouseleave', resume);

    if (prevBtn) prevBtn.addEventListener('click', function () {
        track.scrollTo({ left: track.scrollLeft - track.clientWidth * 0.75, behavior: 'smooth' });
    });
    if (nextBtn) nextBtn.addEventListener('click', function () {
        track.scrollTo({ left: track.scrollLeft + track.clientWidth * 0.75, behavior: 'smooth' });
    });

    // Hover sobre imagen específica → centrar instantáneo
    Array.prototype.forEach.call(track.children, function (fig) {
        fig.addEventListener('mouseenter', function () {
            paused = true;
            var offset = fig.offsetLeft - (track.clientWidth - fig.offsetWidth) / 2;
            track.scrollTo({ left: offset, behavior: 'smooth' });
        });
    });

    raf = requestAnimationFrame(slide);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
    });
})();
