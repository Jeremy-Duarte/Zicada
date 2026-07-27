from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class Command(BaseCommand):
    """
    Configures system roles (Administrator and Delivery) and their permissions.
    This command should be executed after migrations to ensure roles exist.
    """
    help = 'Configures system roles (Administrator and Delivery)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-assign all permissions even if roles exist',
        )

    def _get_delivery_permissions(self):
        """Returns the list of permissions for the Delivery role."""
        delivery_perms = []
        
        # Define permission sets by app
        permission_sets = {
            'products': ['view_product', 'view_collection', 'view_category', 
                        'view_size', 'view_color', 'view_productcolor', 'view_productvariant'],
            'orders': ['view_order', 'change_order'],
            'users': ['view_user', 'change_user'],
            'core': ['view_heroconfig'],
        }
        
        for app_label, codenames in permission_sets.items():
            for codename in codenames:
                try:
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type__app_label=app_label
                    )
                    delivery_perms.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        f'  Warning: Permission {codename} not found for app {app_label}'
                    )
        
        return delivery_perms

    def _setup_administrator_role(self, group, force=False):
        """Sets up the Administrator role with all permissions."""
        if force or group.permissions.count() == 0:
            all_perms = Permission.objects.all().iterator()
            group.permissions.set(all_perms)
            self.stdout.write(
                f'Administrator role configured with {Permission.objects.all().count()} permissions'
            )
        else:
            self.stdout.write(
                f'Administrator role already has {group.permissions.count()} permissions '
                '(use --force to reassign)'
            )

    def _setup_delivery_role(self, group, force=False):
        """Sets up the Delivery role with limited permissions."""
        if force or group.permissions.count() == 0:
            delivery_perms = self._get_delivery_permissions()
            group.permissions.set(delivery_perms)
            self.stdout.write(
                f'Delivery role configured with {len(delivery_perms)} permissions'
            )
        else:
            self.stdout.write(
                f'Delivery role already has {group.permissions.count()} permissions '
                '(use --force to reassign)'
            )

    def _assign_users_to_groups(self):
        """Assigns existing users to their corresponding groups."""
        admin_group = Group.objects.get(name='Administrador')
        delivery_group = Group.objects.get(name='Entregador')
        
        # Assign staff users to Administrator group
        staff_users = User.objects.filter(is_staff=True)
        for user in staff_users:
            user.groups.add(admin_group)
            self.stdout.write(f'  Assigned {user.email} to Administrator')
        
        # Assign delivery users to Delivery group
        delivery_users = User.objects.filter(is_delivery=True)
        for user in delivery_users:
            user.groups.add(delivery_group)
            self.stdout.write(f'  Assigned {user.email} to Delivery')

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write('Configuring system roles...')
        
        # Create or retrieve Administrator group
        admin_group, created = Group.objects.get_or_create(name='Administrador')
        if created:
            self.stdout.write('Administrator group created')
        else:
            self.stdout.write('Administrator group already exists')
        
        # Create or retrieve Delivery group
        delivery_group, created = Group.objects.get_or_create(name='Entregador')
        if created:
            self.stdout.write('Delivery group created')
        else:
            self.stdout.write('Delivery group already exists')
        
        # Configure Administrator role
        self._setup_administrator_role(admin_group, force)
        
        # Configure Delivery role
        self._setup_delivery_role(delivery_group, force)
        
        # Assign existing users
        self._assign_users_to_groups()
        
        self.stdout.write(
            self.style.SUCCESS('System roles configured successfully')
        )