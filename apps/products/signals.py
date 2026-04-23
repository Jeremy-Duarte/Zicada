from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Collection


@receiver(post_save, sender=Collection)
def collection_status_changed(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Collection.objects.get(pk=instance.pk)
            if old.status != instance.status:
                instance.update_products_type()
        except Collection.DoesNotExist:
            pass


@receiver(m2m_changed, sender=Collection.products.through)
def collection_products_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Cuando se añaden o quitan productos de una colección, actualizar el tipo de esos productos.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        if instance.status == 'publicada':
            # Obtener los productos afectados
            if action == 'post_clear':
                productos = instance.products.all()
            else:
                productos = model.objects.filter(pk__in=pk_set)
            for product in productos:
                # Verificar si pertenece a alguna colección publicada
                tiene_publicada = product.collections.filter(status='publicada').exists()
                if tiene_publicada:
                    product.product_type = 'coleccion_limitada'
                else:
                    product.product_type = 'fabrica'
                product.save(update_fields=['product_type'])