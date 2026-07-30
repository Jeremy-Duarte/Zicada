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
        halfway = 0;
        totalFigs = track.children.length / 2;
        for (var i = 0; i < totalFigs; i++) {
            var child = track.children[i];
            if (child) halfway += child.offsetWidth + 24;
        }
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
        prevBtn.addEventListener('click', function () {
            var prev = (currentIdx - 1 + totalFigs) % totalFigs;
            position = centerFig(prev);
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        prevBtn.addEventListener('mouseenter', pause);
        prevBtn.addEventListener('mouseleave', resume);
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', function () {
            var next = (currentIdx + 1) % totalFigs;
            position = centerFig(next);
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        nextBtn.addEventListener('mouseenter', pause);
        nextBtn.addEventListener('mouseleave', resume);
    }

    raf = requestAnimationFrame(loop);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
    });
})();
