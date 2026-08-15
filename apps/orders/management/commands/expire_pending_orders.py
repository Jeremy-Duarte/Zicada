from django.core.management.base import BaseCommand

from apps.orders.use_cases import cancel_expired_pending_orders


class Command(BaseCommand):
    help = 'Cancela pedidos pendientes sin pago aprobado tras el periodo configurado.'

    def handle(self, *args, **options):
        count = cancel_expired_pending_orders()
        self.stdout.write(self.style.SUCCESS(f'{count} pedido(s) expirado(s).'))
