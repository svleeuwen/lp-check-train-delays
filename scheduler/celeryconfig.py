import os
from datetime import timedelta
REDIS_URL = os.environ.get('REDISCLOUD_URL', 'redis://127.0.0.1:6379')
BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERYBEAT_SCHEDULE={
        'check-time-frames': {
            'task': 'scheduler.tasks.check_time_frames',
            'schedule': timedelta(seconds=60),
        },
        'poll-api': {
            'task': 'scheduler.tasks.poll_api',
            'schedule': timedelta(seconds=30),
        },
    }
CELERY_TIMEZONE = 'Europe/Amsterdam'
