# ==================================================
# FILE: tests/unit/backoffice/test_views.py
# APP: backoffice
# MODULE: views
# ==================================================

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
    defaults = {'username': 'admin', 'password': 'pass1234', 'is_staff': True, 'is_superuser': True}
    defaults.update(kwargs)
    password = defaults.pop('password')
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


def _create_normal_user(**kwargs):
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

    # UT-601: Admin Dashboard - Usuario no autenticado redirige al login
    def test_admin_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_DASHBOARD))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_DASHBOARD)}'
        )

    # UT-602: Admin Dashboard - Usuario normal redirige al catálogo
    def test_admin_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_DASHBOARD))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-603: Admin Dashboard - Admin autenticado con permisos carga exitosamente
    def test_admin_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_DASHBOARD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_DASHBOARD)

    # UT-604: Admin Dashboard - Contexto contiene las claves esperadas
    def test_admin_dashboard_context_has_keys(self):
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

    # UT-605: Admin Orders Dashboard - Vista retorna 200
    def test_admin_orders_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_ORDERS))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_ORDERS_DASHBOARD)

    # UT-606: Admin Orders Dashboard - Usuario no autenticado redirige al login
    def test_admin_orders_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_ORDERS))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_ORDERS)}'
        )

    # UT-607: Admin Orders Dashboard - Usuario normal redirige al catálogo
    def test_admin_orders_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_ORDERS))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-608: Admin Orders Dashboard - Contexto contiene las claves esperadas
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

    # UT-609: Admin Products Dashboard - Vista retorna 200
    def test_admin_products_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_PRODUCTS))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_PRODUCTS_DASHBOARD)

    # UT-610: Admin Products Dashboard - Usuario no autenticado redirige al login
    def test_admin_products_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_PRODUCTS))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_PRODUCTS)}'
        )

    # UT-611: Admin Products Dashboard - Usuario normal redirige al catálogo
    def test_admin_products_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_PRODUCTS))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-612: Admin Products Dashboard - Contexto contiene las claves esperadas
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

    # UT-613: Admin Users Dashboard - Vista retorna 200
    def test_admin_users_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_USERS))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_USERS_DASHBOARD)

    # UT-614: Admin Users Dashboard - Usuario no autenticado redirige al login
    def test_admin_users_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_USERS))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_USERS)}'
        )

    # UT-615: Admin Users Dashboard - Usuario normal redirige al catálogo
    def test_admin_users_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_USERS))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-616: Admin Users Dashboard - Contexto contiene las claves esperadas
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

    # UT-617: Admin Config - Vista retorna 200
    def test_admin_config_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_CONFIG))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_ADMIN_CONFIG)

    # UT-618: Admin Config - Usuario no autenticado redirige al login
    def test_admin_config_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_CONFIG))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_CONFIG)}'
        )

    # UT-619: Admin Config - Usuario normal redirige al catálogo
    def test_admin_config_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_CONFIG))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-620: Admin Config - Contexto contiene las claves esperadas
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

    # UT-621: Importers Dashboard - Vista retorna 200
    def test_importers_dashboard_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_IMPORTERS_DASHBOARD))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_IMPORTERS_DASHBOARD)

    # UT-622: Importers Dashboard - Usuario no autenticado redirige al login
    def test_importers_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_IMPORTERS_DASHBOARD))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_IMPORTERS_DASHBOARD)}'
        )

    # UT-623: Importers Dashboard - Usuario normal redirige al catálogo
    def test_importers_dashboard_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_IMPORTERS_DASHBOARD))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-624: Importers Dashboard - Contexto contiene las claves esperadas
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

    # UT-625: Report Generator GET - Retorna 200 con formulario
    def test_report_generator_get_returns_200(self):
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TEMPLATE_REPORT_GENERATOR)
        self.assertIn('form', response.context)

    # UT-626: Report Generator - Usuario no autenticado redirige al login
    def test_report_generator_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertRedirects(
            response,
            f'{reverse(CORE_STAFF_LOGIN)}?next={reverse(BACKOFFICE_REPORT_GENERATOR)}'
        )

    # UT-627: Report Generator - Usuario normal redirige al catálogo
    def test_report_generator_requires_permission(self):
        normal_user = _create_normal_user()
        self.client.force_login(normal_user)
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertRedirects(response, reverse(PRODUCTS_CATALOG))

    # UT-628: Report Generator - Contexto contiene el formulario
    def test_report_generator_context_has_form(self):
        response = self.client.get(reverse(BACKOFFICE_REPORT_GENERATOR))
        self.assertIn('form', response.context)