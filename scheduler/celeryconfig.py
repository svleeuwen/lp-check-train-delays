from datetime import timedelta
REDIS_URL = 'redis://127.0.0.1:6379'
BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERYBEAT_SCHEDULE={
        'check-time-frames': {
            'task': 'scheduler.tasks.check_time_frames',
            'schedule': timedelta(seconds=10),
        },
        'poll-api': {
            'task': 'scheduler.tasks.poll_api',
            'schedule': timedelta(seconds=10),
        },
    }
CELERY_TIMEZONE = 'Europe/Amsterdam'
