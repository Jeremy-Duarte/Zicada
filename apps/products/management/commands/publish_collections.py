from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.products.models import Collection


class Command(BaseCommand):
    help = 'Publica colecciones en borrador cuya fecha de inicio ya llegó'

    def handle(self, *args, **options):
        hoy = timezone.now()
        
        por_publicar = Collection.objects.filter(
            status='borrador',
            start_date__lte=hoy,
            is_active=True
        )
        
        count_published = 0
        for collection in por_publicar:
            if collection.products.exists():
                collection.check_and_update_status()
                count_published += 1
                self.stdout.write(f'Publicada: {collection.name}')
            else:
                self.stdout.write(self.style.WARNING(
                    f'⚠️ {collection.name} no se publicó (no tiene productos)'
                ))
        
        self.stdout.write(self.style.SUCCESS(f'Se publicaron {count_published} colecciones.'))