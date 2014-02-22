web: gunicorn lpapp:app
celery: celery -A scheduler.tasks.celery worker --beat --loglevel=debug