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

    function posToIdx(pos) {
        var centerPos = pos + containerWidth / 2;
        return Math.round(centerPos / halfway * totalFigs) % (totalFigs * 2);
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
        currentIdx = posToIdx(position);
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
            position -= itemWidth;
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        prevBtn.addEventListener('mouseenter', pause);
        prevBtn.addEventListener('mouseleave', resume);
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', function () {
            position += itemWidth;
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
        nextBtn.addEventListener('mouseenter', pause);
        nextBtn.addEventListener('mouseleave', resume);
    }

    Array.prototype.forEach.call(track.children, function (fig, i) {
        if (i >= track.children.length / 2) return;

        fig.addEventListener('click', function (e) {
            paused = true;

            var candidate1 = i;
            var candidate2 = i + totalFigs;
            var d1 = Math.abs(candidate1 - currentIdx);
            var d2 = Math.abs(candidate2 - currentIdx);
            var idx = d1 <= d2 ? candidate1 : candidate2;

            var figIdx = idx % totalFigs;
            var figEl = track.children[figIdx];
            var off = figEl.offsetLeft;
            var centerAdjust = (containerWidth - figEl.offsetWidth) / 2;
            position = idx < totalFigs ? off - centerAdjust : off + halfway - centerAdjust;
            position = wrap(position);
            track.style.transform = 'translateX(' + (-position) + 'px)';
        });
    });

    raf = requestAnimationFrame(loop);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
    });
})();
