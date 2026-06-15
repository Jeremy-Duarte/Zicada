"""
Tests para vistas del backoffice (panel de administración).

Estos tests verifican:
- Autenticación y autorización (comportamiento de StaffPermissionRequiredMixin)
- Que las vistas retornan 200 para usuarios staff con permisos
- Que el contexto contiene las claves esperadas
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.core.url_names import (
    CORE_STAFF_LOGIN,
    PRODUCTS_CATALOG,
    BACKOFFICE_DASHBOARD,
    BACKOFFICE_ORDERS,
    BACKOFFICE_PRODUCTS,
    BACKOFFICE_USERS,
    BACKOFFICE_CONFIG,
    BACKOFFICE_REPORT_GENERATOR,
    BACKOFFICE_IMPORTERS_DASHBOARD,
)

from apps.backoffice.constants import (
    TEMPLATE_ADMIN_DASHBOARD,
    TEMPLATE_ADMIN_ORDERS_DASHBOARD,
    TEMPLATE_ADMIN_PRODUCTS_DASHBOARD,
    TEMPLATE_ADMIN_USERS_DASHBOARD,
    TEMPLATE_ADMIN_CONFIG,
    TEMPLATE_REPORT_GENERATOR,
    TEMPLATE_IMPORTERS_DASHBOARD,
    CONTEXT_STATS,
    CONTEXT_SECTION,
    CONTEXT_URLS,
    CONTEXT_ACTION_BUTTONS,
    CONTEXT_RECENT_ORDERS,
    CONTEXT_LOW_STOCK_PRODUCTS,
    CONTEXT_TOP_PRODUCTS,
    CONTEXT_RECENT_PRODUCTS,
    CONTEXT_QUICK_ACCESS_BUTTONS,
    CONTEXT_RECENT_DELIVERIES,
    CONTEXT_ACTIVE_DELIVERIES,
    CONTEXT_IMPORT_BUTTONS,
)

User = get_user_model()


# =============================================================================
# HELPERS
# =============================================================================

def _create_superuser(**kwargs):
    """Crea un superusuario con todos los permisos."""
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True, 'is_superuser': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_normal_user(**kwargs):
    """Crea un usuario normal (no staff)."""
    defaults = {'username': 'normal', 'password': 'pass1234', 'is_staff': False}
    defaults.update(kwargs)
    password = defaults.pop('password')
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


# =============================================================================
# TESTS: ADMIN DASHBOARD (Principal)
# =============================================================================

class AdminDashboardTest(TestCase):
    """Pruebas para el dashboard principal de administración."""

    def setUp(self):
        self.client = Client()
        self.admin = _create_superuser()
        self.client.force_login(self.admin)

    def test_admin_dashboard_requires_authentication(self):
        """Usuario no autenticado → redirige al login."""
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_DASHBOARD))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_DASHBOARD)}'
        )

    def test_admin_dashboard_requires_permission(self):
        """Usuario normal (autenticado sin permiso) → redirige al catálogo."""
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_DASHBOARD))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_admin_dashboard_returns_200(self):
        """Admin autenticado con permisos → dashboard cargado exitosamente."""
        response = self.client.get(reverse(BACKOFFICE_DASHBOARD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_DASHBOARD)

    def test_admin_dashboard_context_has_keys(self):
        """El contexto contiene las claves esperadas."""
        response = self.client.get(reverse(BACKOFFICE_DASHBOARD))
        self.assertIsNotNone(response.context)
        self.assertIn(CONTEXT_SECTION, response.context)
        self.assertIn(CONTEXT_STATS, response.context)
        self.assertIn(CONTEXT_ACTION_BUTTONS, response.context)
        self.assertIn(CONTEXT_RECENT_ORDERS, response.context)
        self.assertIn(CONTEXT_LOW_STOCK_PRODUCTS, response.context)
        self.assertIn(CONTEXT_TOP_PRODUCTS, response.context)


# =============================================================================
# TESTS: ADMIN ORDERS DASHBOARD
# =============================================================================

class AdminOrdersDashboardTest(TestCase):
    """Pruebas para el dashboard de órdenes."""

    def setUp(self):
        self.client = Client()
        self.admin = _create_superuser()
        self.client.force_login(self.admin)

    def test_admin_orders_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_ORDERS))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_ORDERS_DASHBOARD)

    def test_admin_orders_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_ORDERS))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_ORDERS)}'
        )

    def test_admin_orders_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_ORDERS))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_admin_orders_dashboard_context_has_keys(self):
        response = self.client.get(reverse(BACKOFFICE_ORDERS))
        self.assertIsNotNone(response.context)
        self.assertIn(CONTEXT_SECTION, response.context)
        self.assertIn(CONTEXT_STATS, response.context)
        self.assertIn(CONTEXT_URLS, response.context)
        self.assertIn(CONTEXT_ACTION_BUTTONS, response.context)
        self.assertIn(CONTEXT_RECENT_ORDERS, response.context)


# =============================================================================
# TESTS: ADMIN PRODUCTS DASHBOARD
# =============================================================================

class AdminProductsDashboardTest(TestCase):
    """Pruebas para el dashboard de productos."""

    def setUp(self):
        self.client = Client()
        self.admin = _create_superuser()
        self.client.force_login(self.admin)

    def test_admin_products_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_PRODUCTS))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_PRODUCTS_DASHBOARD)

    def test_admin_products_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_PRODUCTS))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_PRODUCTS)}'
        )

    def test_admin_products_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_PRODUCTS))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_admin_products_dashboard_context_has_keys(self):
        response = self.client.get(reverse(BACKOFFICE_PRODUCTS))
        self.assertIsNotNone(response.context)
        self.assertIn(CONTEXT_SECTION, response.context)
        self.assertIn(CONTEXT_STATS, response.context)
        self.assertIn(CONTEXT_URLS, response.context)
        self.assertIn(CONTEXT_ACTION_BUTTONS, response.context)
        self.assertIn(CONTEXT_RECENT_PRODUCTS, response.context)
        self.assertIn(CONTEXT_LOW_STOCK_PRODUCTS, response.context)
        self.assertIn(CONTEXT_TOP_PRODUCTS, response.context)
        self.assertIn(CONTEXT_QUICK_ACCESS_BUTTONS, response.context)


# =============================================================================
# TESTS: ADMIN USERS DASHBOARD
# =============================================================================

class AdminUsersDashboardTest(TestCase):
    """Pruebas para el dashboard de usuarios (entregadores)."""

    def setUp(self):
        self.client = Client()
        self.admin = _create_superuser()
        self.client.force_login(self.admin)

    def test_admin_users_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_USERS))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_USERS_DASHBOARD)

    def test_admin_users_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_USERS))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_USERS)}'
        )

    def test_admin_users_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_USERS))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_admin_users_dashboard_context_has_keys(self):
        response = self.client.get(reverse(BACKOFFICE_USERS))
        self.assertIsNotNone(response.context)
        self.assertIn(CONTEXT_SECTION, response.context)
        self.assertIn(CONTEXT_STATS, response.context)
        self.assertIn(CONTEXT_URLS, response.context)
        self.assertIn(CONTEXT_ACTION_BUTTONS, response.context)
        self.assertIn(CONTEXT_RECENT_DELIVERIES, response.context)
        self.assertIn(CONTEXT_ACTIVE_DELIVERIES, response.context)
        self.assertIn(CONTEXT_QUICK_ACCESS_BUTTONS, response.context)


# =============================================================================
# TESTS: ADMIN CONFIG
# =============================================================================

class AdminConfigTest(TestCase):
    """Pruebas para la vista de configuración."""

    def setUp(self):
        self.client = Client()
        self.admin = _create_superuser()
        self.client.force_login(self.admin)

    def test_admin_config_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_CONFIG))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_CONFIG)

    def test_admin_config_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_CONFIG))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_CONFIG)}'
        )

    def test_admin_config_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_CONFIG))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_admin_config_context_has_keys(self):
        response = self.client.get(reverse(BACKOFFICE_CONFIG))
        self.assertIsNotNone(response.context)
        self.assertIn(CONTEXT_SECTION, response.context)
        self.assertIn(CONTEXT_QUICK_ACCESS_BUTTONS, response.context)


# =============================================================================
# TESTS: IMPORTERS DASHBOARD
# =============================================================================

class ImportersDashboardTest(TestCase):
    """Pruebas para el dashboard de importación."""

    def setUp(self):
        self.client = Client()
        self.admin = _create_superuser()
        self.client.force_login(self.admin)

    def test_importers_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_IMPORTERS_DASHBOARD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_IMPORTERS_DASHBOARD)

    def test_importers_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_IMPORTERS_DASHBOARD))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_IMPORTERS_DASHBOARD)}'
        )

    def test_importers_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_IMPORTERS_DASHBOARD))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_importers_dashboard_context_has_keys(self):
        response = self.client.get(reverse(BACKOFFICE_IMPORTERS_DASHBOARD))
        self.assertIsNotNone(response.context)
        self.assertIn(CONTEXT_SECTION, response.context)
        self.assertIn(CONTEXT_IMPORT_BUTTONS, response.context)


# =============================================================================
# TESTS: REPORT GENERATOR
# =============================================================================

class ReportGeneratorTest(TestCase):
    """Pruebas para el generador de reportes PDF."""

    def setUp(self):
        self.client = Client()
        self.admin = _create_superuser()
        self.client.force_login(self.admin)

    def test_report_generator_get_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_REPORT_GENERATOR)
        self.assertIn('form', response.context)

    def test_report_generator_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_REPORT_GENERATOR)}'
        )

    def test_report_generator_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    def test_report_generator_context_has_form(self):
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertIn('form', response.context)