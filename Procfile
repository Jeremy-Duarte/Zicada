web: DJANGO_SETTINGS_MODULE=config.settings_production python manage.py migrate && DJANGO_SETTINGS_MODULE=config.settings_production python manage.py setup_roles && DJANGO_SETTINGS_MODULE=config.settings_production python manage.py collectstatic --noinput && DJANGO_SETTINGS_MODULE=config.settings_production gunicorn config.wsgi --log-file -
# Worker de Celery: SOLO activar si ASYNC_BACKEND=celery (requiere Redis).
# Con ASYNC_BACKEND=threading o sync no se necesita worker ni broker.
# worker: DJANGO_SETTINGS_MODULE=config.settings_production celery -A config worker --loglevel=info --concurrency=2
