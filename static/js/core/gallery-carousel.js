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

    var targetPos = null;
    var EASING = 0.08;

    function measure() {
        halfway = 0;
        var count = track.children.length / 2;
        for (var i = 0; i < count; i++) {
            var child = track.children[i];
            if (child) halfway += child.offsetWidth + 24;
        }
        itemWidth = track.children[0] ? track.children[0].offsetWidth + 24 : 300;
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

        if (targetPos === null) position = wrap(position);
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
            targetPos = position + itemWidth;
        });
    });

    raf = requestAnimationFrame(loop);

    window.addEventListener('beforeunload', function () {
        if (raf) cancelAnimationFrame(raf);
    });
})();
