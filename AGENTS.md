# AGENTS.md — Zicada

## Settings modules

Three settings files exist; pick the right one for the environment:

| Module | When | Notes |
|--------|------|-------|
| `config.settings` | `manage.py runserver` (dev) | Reads `.env`, SQLite by default |
| `config.settings_test` | Tests | In-memory SQLite, mock API keys, `locmem` email, `DummyCache`, `MD5PasswordHasher` |
| `config.settings_production` | Railway deploy | Reads `.env.prod` (optional), PostgreSQL via `DATABASE_URL`, Whitenoise, Anymail (Resend) |

Test settings are wired through `pytest.ini`, not `manage.py test`. Always use `config.settings_test` for running tests — it disables HTTPS redirects, avoids real API calls, and speeds up execution.

## Packages

Six Zicada Django apps under `apps/`:

- `core` — Landing page, about/contact/terms, staff login, breadcrumbs/cart context processors, `HeroConfig` CRUD with soft-delete
- `products` — Catalog, product detail, collections, inventory/variants, importers (CSV), `update_collections_status` cron, color/size models
- `orders` — Session-based cart (`apps.orders.cart.Cart`), checkout, order tracking, Stripe integration, email notifications
- `users` — Custom `User` model (`AUTH_USER_MODEL = 'users.User'`), `setup_roles` management command, `is_delivery` flag
- `delivery` — PWA for delivery personnel (offline-first), login, daily orders, cash summary, Delivery API
- `backoffice` — Admin dashboard, metrics, reports (WeasyPrint)

## Commands

```bash
# Dev server (portal on port 8080, optional cloudflared tunnel)
python serve.py
python serve.py --tunnel --port 3000

# Django dev server
python manage.py runserver

# Run all tests
DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/ -v

# Run a single app’s tests
DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/products/tests/ -v

# Run a single test file
DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/products/tests/test_views.py -v

# Coverage (outputs coverage.xml at project root for SonarCloud)
DJANGO_SETTINGS_MODULE=config.settings_test pytest apps/ --cov=apps --cov-report=xml:coverage.xml

# Shell shortcut
./scripts/run.sh products   # runs apps/products tests
./scripts/run.sh all        # runs all tests
./scripts/run.sh full       # all tests + coverage reports
```

The `scripts/run.sh` wrapper accepts: `core`, `products`, `orders`, `users`, `backoffice`, `all`, `coverage`, `full`, `clean`.

## Production startup

The `Procfile` runs these in order on every deploy:
```
python manage.py migrate && python manage.py setup_roles && python manage.py collectstatic --noinput && gunicorn config.wsgi --log-file -
```

The `setup_roles` command (in `apps.users.management.commands.setup_roles`) creates the `Administrador` and `Entregador` groups. It must run after migrations.

## Conventions (from `continue` rules)

- **Language**: English for code/names; Spanish only for user-facing strings (`verbose_name`, templates, error messages, emails).
- **ORM**: Always use `select_related` and `prefetch_related` when accessing related objects.
- **CSS**: Tailwind utility classes only; no custom CSS.
- **Functions**: Keep under 15 lines, single responsibility (KISS). Extract repeated logic to `utils.py` or `crud/`.
- **Validation**: Validate all inputs at form or serializer level. Use Django `messages` framework for user feedback.
- **Type hints**: Required on all function signatures.
- **Imports**: Module-level imports; never inline inside functions unless avoiding circular imports.

## Key quirks

- **Cart is session-based**, not in the DB. Stored at `request.session['cart']`. The `Cart` class (`apps/orders/cart.py`) handles serialization via `self.cart_data`.
- **Cloudinary** is used as media storage backend even in tests (with dummy credentials). Do not test file uploads without mocking Cloudinary.
- **WeasyPrint** (used in `apps/backoffice/reports/`) requires system libraries listed in `apt-packages.txt` and `railpack.json`.
- **Soft-delete**: The `core.HeroConfig` model uses `is_active` + a trashcan view pattern (`hero_trashcan`, `hero_restore`).
- **Cron**: `update_collections_status` runs Sundays at 2am Colombia time (UTC-5). Uses `django-crontab`.
- **CSV importers** live in `apps/products/importers/` (categories, colors, sizes).

## CI (SonarCloud)

The GitHub Actions workflow (`build.yml`) runs on pushes to `main` and PRs:
1. Installs `requirements.txt` + `pytest pytest-cov pytest-django`
2. Runs `pytest apps/ --cov=apps --cov-report=xml:coverage.xml` with `DJANGO_SETTINGS_MODULE=config.settings_test`
3. Uploads `coverage.xml` to SonarCloud

The `sonar-project.properties` file configures the same analysis locally. Test paths in `sonar.tests` are relative to the project root.
