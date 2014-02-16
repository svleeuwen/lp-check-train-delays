# coding: utf-8
from datetime import datetime
from flask import json, jsonify, make_response, render_template, Response, request, send_from_directory, url_for
import hashlib
from random import choice

from lpapp import app, db, client
from nsapi.api import NSApi


@app.route('/')
def root():
    return make_response('A Little Printer publication.')

@app.route('/meta.json')
@app.route('/icon.png')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


FROM_STATION = 'Amsterdam'
TO_STATION = 'Rotterdam'

@app.route('/edition/')
def ns_api():
    api = NSApi(app.config['NS_AUTH_STRING'])
    results = api.get(FROM_STATION, TO_STATION, datetime.now())
    #results = []
    return render_template('edition.html', results=results,
                                       from_station=FROM_STATION,
                                       to_station=TO_STATION)

@app.route('/test/')
def test():
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

        data = dict(results=delays, from_station=user_settings['from_station'], to_station=user_settings['to_station'])
        return render_edition(data)

def render_edition(data):
    return render_template('edition.html', **data)


# == POST parameters:
# 'config'
#   request.form['config'] contains a JSON array of responses to the options defined
#   by the fields object in meta.json. In this case, something like:
#   request.form['config'] = {"name":"SomeName", "lang":"SomeLanguage"}
# 'endpoint'
#   the URL to POST content to be printed out by Push.
# 'subscription_id'
#   a string used to identify the subscriber and their Little Printer.
#
# Most of this is identical to a non-Push publication.
# The only difference is that we have an `endpoint` and `subscription_id` and
# need to store this data in our database. All validation is the same.
#
# == Returns:
# A JSON response object.
# If the parameters passed in are valid: {"valid":true}
# If the parameters passed in are not valid: {"valid":false,"errors":["No name was provided"], ["The language you chose does not exist"]}
#
@app.route('/validate_config/', methods=['POST'])
def validate_config():
    if 'config' not in request.form:
        return Response(response='There is no config to validate', status=400)
    
    # Preparing what will be returned:
    response = {
        'errors': [],
        'valid': True,
    }

    # Extract the config from the POST data and parse its JSON contents.
    # user_settings will be something like: {"name":"Alice", "lang":"english"}.
    user_settings = json.loads(request.form.get('config', {}))

    # If the user did not choose a language:
    if 'lang' not in user_settings or user_settings['lang'] == '':
        response['valid'] = False
        response['errors'].append('Please choose a language from the menu.')

    # If the user did not fill in the name option:
    if 'name' not in user_settings or user_settings['name'] == '':
        response['valid'] = False
        response['errors'].append('Please enter your name into the name box.')

    if user_settings['lang'].lower() not in app.config['GREETINGS']:
        # Given that the select field is populated from a list of languages
        # we defined this should never happen. Just in case.
        response['valid'] = False
        response['errors'].append("We couldn't find the language you selected (%s). Please choose another." % user_settings['lang'])

    ########################
    # This section is Push-specific, different to a conventional publication:
    if request.form.get('endpoint', '') == '':
        response['valid'] = False
        response['errors'].append('No Push endpoint was provided.')

    if request.form.get('subscription_id', '') == '':
        response['valid'] = False
        response['errors'].append('No Push subscription_id was provided.')

    if response['valid']:
        # Assuming the form validates, we store the endpoint, plus this user's
        # language choice and name, keyed by their subscription_id.
        user_settings['endpoint'] = request.form.get('endpoint')
        db().hset('train_delays:subscriptions',
                    request.form.get('subscription_id'),
                    json.dumps(user_settings))

    # Ending the Push-specific section.
    ########################

    return jsonify(**response)


# Called to generate the sample shown on BERG Cloud Remote.
#
# == Parameters:
#   None.
#
# == Returns:
# HTML/CSS edition.
#
@app.route('/sample/')
def sample():
    # The values we'll use for the sample:
    language = 'english'
    name = 'Little Printer'
    response = make_response(render_template(
            'edition.html',
            greeting="%s, %s" % (app.config['GREETINGS'][language][0], name),
        ))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    # Set the ETag to match the content.
    response.headers['ETag'] = '"%s"' % (
        hashlib.md5(
            language + name + datetime.utcnow().strftime('%d%m%Y')
        ).hexdigest()
    )
    return response


# A button to press to send print events to subscribed Little Printers.
@app.route('/push/', methods=['GET'])
def push_get():
    return render_template('push.html', pushed=False)


# When the button is pressed, this happens.
# Push a greeting to all subscribed Little Printers.
@app.route('/push/', methods=['POST'])
def push_post():
    subscribed_count = 0
    unsubscribed_count = 0

    for subscription_id, config in db().hgetall('train_delays:subscriptions').iteritems():
        # config contains the subscriber's language, name and endpoint.
        config = json.loads(config)

        # Get a random greeting in this subscriber's chosen language.
        #greeting = choice(app.config['GREETINGS'][ config['lang'] ])

        # Make the HTML content to push to the printer.
        content = render_template(
                                'edition.html')
                                #greeting="%s, %s" % (greeting, config['name']))

        # Post this content to BERG Cloud using OAuth.
        response, data = client().request(
                        config['endpoint'],
                        method='POST',
                        body=content,
                        headers={'Content-Type': 'text/html; charset=utf-8'})

        if response.status == '410':
            # By sending a 410 status code, BERG Cloud has informed us this
            # user has unsubscribed. So delete their subscription from our
            # database.
            db().hdel('push_example:subscriptions', subscription_id)
            unsubscribed_count += 1
        else:
            subscribed_count += 1

    # Show the same form again, with a message to confirm this worked.
    return render_template('push.html',
                            pushed=True,
                            subscribed_count=subscribed_count,
                            unsubscribed_count=unsubscribed_count)
