import datetime as dt
import hashlib
from celery import Celery
from flask import json, render_template
from lpapp import db, app, client

# Run with celery -A scheduler.tasks.celery worker --beat --loglevel=info
from nsapi.api import NSApi

celery = Celery('tasks')
celery.config_from_object('scheduler.celeryconfig')

@celery.task
def check_time_frames():
    with app.app_context():
        for subscription_id, config in db().hgetall('train_delays:subscriptions').iteritems():
            user_settings = json.loads(config)

            # create datetime objects
            now = dt.datetime.now().time()
            time_slot_begin = dt.datetime.strptime(user_settings['time_slot_begin'], '%H:%M').time()
            time_slot_end = dt.datetime.strptime(user_settings['time_slot_end'], '%H:%M').time()

            # check offset if we need to call api earlier
            minutes_delta = dt.timedelta(seconds=int(['push_offset_minutes']) * 60)
            offset_time = (dt.datetime.combine(dt.date(1,1,1), time_slot_begin) - minutes_delta).time()

            # within timeframe?
            if offset_time <= now <= time_slot_end:
                # exists already?
                if not db().hexists('train_delays:api_queue', subscription_id):
                    # add to api queue
                    db().hset('train_delays:api_queue', subscription_id, config)
            elif db().hexists('train_delays:api_queue', subscription_id):
                # otherwise delete
                db().hdel('train_delays:api_queue', subscription_id)


@celery.task
def poll_api():
    with app.app_context():
        api = NSApi(app.config['NS_AUTH_STRING'])
        for subscription_id, config in db().hgetall('train_delays:api_queue').iteritems():
            user_settings = json.loads(config)

            today = dt.datetime.today()
            time_slot_begin = dt.datetime.combine(today, dt.datetime.strptime(user_settings['time_slot_begin'], '%H:%M').time())
            delays = api.get(user_settings['from_station'], user_settings['to_station'], time_slot_begin)
            time_slot_end = dt.datetime.combine(today, dt.datetime.strptime(user_settings['time_slot_end'], '%H:%M').time())

            # filter delays to match time frame
            delays = [d for d in delays if d['departure_actual'] <= time_slot_end.time()]
            #if delays:
            send_to_printer(subscription_id, delays, user_settings)


def send_to_printer(subscription_id, delays, user_settings):
    content = render_template('edition.html', results=delays,
                              from_station=user_settings['from_station'],
                              to_station=user_settings['to_station'])

    # new content?
    tag = '"%s"' % (
        hashlib.md5(
            content + dt.datetime.utcnow().strftime('%d%m%Y')
        ).hexdigest())


    stored_tag = db().hget('train_delays:content_tag', subscription_id)
    #print "stored: " + stored_content
    #print "content: " + content
    print "new content %s" % (stored_tag != tag)
    if not stored_tag or stored_tag != tag:
        db().hset('train_delays:content_tag', subscription_id, tag)
    elif stored_tag == tag:
        return

    print 'DO REQUEST'
    # Post this content to BERG Cloud using OAuth.
    response, data = client().request(
        user_settings['endpoint'],
        method='POST',
        body=content,
        headers={'Content-Type': 'text/html; charset=utf-8'})

    print 'RESPONSE STATUS: %d' % response.status
    if response.status == '410':
        # By sending a 410 status code, BERG Cloud has informed us this
        # user has unsubscribed. So delete their subscription from our
        # database.
        # TODO enable in production
        #db().hdel('train_delays:subscriptions', subscription_id)
        pass
    else:
        pass
        #db().hdel('train_delays:subscriptions', subscription_id)
