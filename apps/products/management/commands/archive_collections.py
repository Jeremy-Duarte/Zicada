from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.products.models import Collection


class Command(BaseCommand):
    help = 'Archiva colecciones publicadas cuya fecha de fin ya pasó'

    def handle(self, *args, **options):
        hoy = timezone.now()
        expiradas = Collection.objects.filter(
            status='publicada',
            end_date__lt=hoy,
            is_active=True
        )
        
        count = 0
        for collection in expiradas:
            collection.status = 'archivada'
            collection.save(update_fields=['status'])
            collection.update_products_type()
            count += 1
            self.stdout.write(f'Archivada: {collection.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Se archivaron {count} colecciones.'))