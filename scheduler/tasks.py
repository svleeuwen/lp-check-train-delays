from datetime import datetime
from celery import Celery
from flask import json
from lpapp import db, app

# Run with celery -A scheduler.tasks.celery worker --beat --loglevel=info
from nsapi.api import NSApi

celery = Celery('tasks')
celery.config_from_object('scheduler.celeryconfig')

@celery.task
def check_time_frames():
    with app.app_context():
        for subscription_id, config in db().hgetall('train_delays:subscriptions').iteritems():
            user_settings = json.loads(config)
            now = datetime.now().time()
            time_slot_begin = datetime.strptime(user_settings['time_slot_begin'], '%H:%M').time()
            time_slot_end = datetime.strptime(user_settings['time_slot_end'], '%H:%M').time()
            # add to api queue
            if time_slot_begin <= now <= time_slot_end:
                db().hset('train_delays:api_queue', subscription_id, config)
            elif db().hexists('train_delays:api_queue', subscription_id):
                db().hdel('train_delays:api_queue', subscription_id)

@celery.task
def poll_api():
    with app.app_context():
        api = NSApi(app.config['NS_AUTH_STRING'])
        for subscription_id, config in db().hgetall('train_delays:api_queue').iteritems():
            user_settings = json.loads(config)
            today = datetime.today()
            time_slot_begin = datetime.combine(today, datetime.strptime(user_settings['time_slot_begin'], '%H:%M').time())
            delays = api.get(user_settings['from_station'], user_settings['to_station'], time_slot_begin)
            time_slot_end = datetime.combine(today, datetime.strptime(user_settings['time_slot_end'], '%H:%M').time())
            # filter delays to match time frame
            delays = [d for d in delays if d['departure_actual'] <= time_slot_end.time()]
            #if delays:
            print delays



#def make_celery(app):
#    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
#    celery.conf.update(app.config)
#    TaskBase = celery.Task
#    class ContextTask(TaskBase):
#        abstract = True
#        def __call__(self, *args, **kwargs):
#            with app.app_context():
#                return TaskBase.__call__(self, *args, **kwargs)
#    celery.Task = ContextTask
#    return celery

#celery = make_celery(app)