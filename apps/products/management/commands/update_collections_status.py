from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Actualiza el estado de todas las colecciones (archiva expiradas y publica programadas)'

    def handle(self, *args, **options):
        self.stdout.write('Actualizando estados de colecciones...')
        
        self.stdout.write('\nArchivando colecciones expiradas...')
        call_command('archive_collections')
        
        self.stdout.write('\nPublicando colecciones programadas...')
        call_command('publish_collections')
        
        self.stdout.write(self.style.SUCCESS('\nActualización completada.'))