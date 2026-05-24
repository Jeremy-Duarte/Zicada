(function(global) {
    class SortableWidget {
        constructor(widget) {
            this.widget = widget;
            this.input = widget.querySelector('.sortable-order-input');
            this.list = widget.querySelector('.sortable-list');
            if (!this.input || !this.list) return;
            this.init();
        }
        init() {
            new Sortable(this.list, {
                animation: 300,
                handle: '.sortable-item',
                onEnd: () => this.update()
            });
        }
        update() {
            const items = this.list.querySelectorAll('.sortable-item');
            const order = Array.from(items).map(item => item.dataset.id);
            this.input.value = JSON.stringify(order);
            this.input.dispatchEvent(new Event('change'));
        }
    }
    function init() {
        document.querySelectorAll('.sortable-order-widget').forEach(w => {
            if (w._sortable) return;
            w._sortable = new SortableWidget(w);
        });
    }
    document.addEventListener('DOMContentLoaded', init);
    new MutationObserver(init).observe(document.body, { childList: true, subtree: true });
})(globalThis);