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
    var totalFigs = 0;
    var currentIdx = 0;

    function measure() {
        totalFigs = track.children.length / 2;
        var lastOriginal = track.children[totalFigs - 1];
        halfway = lastOriginal ? lastOriginal.offsetLeft + lastOriginal.offsetWidth + 24 : 0;
        itemWidth = track.children[0] ? track.children[0].offsetWidth + 24 : 300;
        containerWidth = track.parentElement.clientWidth;
    }

    function centerFig(idx) {
        var fig = track.children[idx % totalFigs];
        var off = fig.offsetLeft;
        var centerAdjust = (containerWidth - fig.offsetWidth) / 2;
        return off - centerAdjust;
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

        if (!paused) {
            position += speed * (delta / 16);
        }

        position = wrap(position);
        currentIdx = Math.round(position / itemWidth) % totalFigs;
        track.style.transform = 'translateX(' + (-position) + 'px)';
        lastTs = ts;
        raf = requestAnimationFrame(loop);
    }

    function pause()  { paused = true; }
    function resume() { paused = false; }

    track.addEventListener('mouseenter', pause);
    track.addEventListener('mouseleave', resume);

    if (prevBtn) {
        prevBtn.addEventListener('click', function (e) {
            e.preventDefault();
            var prev = (currentIdx - 1 + totalFigs) % totalFigs;
            position = centerFig(prev);
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        prevBtn.addEventListener('mouseenter', pause);
        prevBtn.addEventListener('mouseleave', resume);
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', function (e) {
            e.preventDefault();
            var next = (currentIdx + 1) % totalFigs;
            position = centerFig(next);
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        nextBtn.addEventListener('mouseenter', pause);
        nextBtn.addEventListener('mouseleave', resume);
    }

    var touchStartX = 0;
    var touchMoved = false;

    track.addEventListener('touchstart', function (e) {
        touchStartX = e.touches[0].clientX;
        touchMoved = false;
    }, { passive: true });

    track.addEventListener('touchmove', function (e) {
        touchMoved = true;
    }, { passive: true });

    track.addEventListener('touchend', function (e) {
        if (!touchMoved) return;
        var dx = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(dx) < 40) return;
        if (dx < 0 && nextBtn) {
            nextBtn.click();
        } else if (dx > 0 && prevBtn) {
            prevBtn.click();
        }
    });

    raf = requestAnimationFrame(loop);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
    });
})();
