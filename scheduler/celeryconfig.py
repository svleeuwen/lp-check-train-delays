from datetime import timedelta
REDIS_URL = 'redis://127.0.0.1:6379'
BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERYBEAT_SCHEDULE={
        'every-30-seconds': {
            'task': 'scheduler.tasks.add',
            'schedule': timedelta(seconds=5),
            'args': (1, 2),
        },
    }
CELERY_TIMEZONE = 'Europe/Amsterdam'
