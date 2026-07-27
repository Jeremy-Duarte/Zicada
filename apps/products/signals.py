import logging
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Collection, Product

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Collection)
def collection_status_changed(sender, instance, **kwargs):
    if kwargs.get('created', False):
        return
    try:
        old = Collection.objects.get(pk=instance.pk)
        if old.status != instance.status:
            instance.update_products_type()
    except Collection.DoesNotExist:
        logger.warning("Collection %d not found in post_save signal.", instance.pk)


@receiver(m2m_changed, sender=Collection.products.through)
def collection_products_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if reverse:
        return

    if action == 'pre_clear' and instance.status == 'publicada':
        instance._cleared_product_ids = list(
            instance.products.values_list('id', flat=True)
        )

    if action == 'post_clear' and instance.status == 'publicada':
        product_ids = getattr(instance, '_cleared_product_ids', [])
        if product_ids:
            products = Product.objects.filter(pk__in=product_ids)
            _update_product_types(products)

    if action in ('post_add', 'post_remove') and instance.status == 'publicada':
        products = model.objects.filter(pk__in=pk_set)
        _update_product_types(products)


def _update_product_types(products):
    if not products:
        return
    published_ids = set(
        Product.objects.filter(
            collections__status='publicada',
            id__in=[p.id for p in products]
        ).values_list('id', flat=True)
    )
    to_update = []
    for product in products:
        if product.id in published_ids:
            product.product_type = 'coleccion_limitada'
        else:
            product.product_type = 'fabrica'
        to_update.append(product)
    if to_update:
        Product.objects.bulk_update(to_update, ['product_type'])
