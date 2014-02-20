# coding: utf-8
import os
import urlparse
import oauth2 as oauth
import redis
from flask import Flask, g


# Default configuration
DEBUG = False

app = Flask(__name__)
app.config.from_object(__name__)

try:
    # If there's a settings file, use that:
    filename = os.path.join(os.path.dirname(__file__), '../settings.cfg')
    with open(filename) as f:
        app.config.from_pyfile(filename)
except IOError as e:
    # Otherwise, use environment variables.
    for var in ['BERGCLOUD_CONSUMER_TOKEN', 'BERGCLOUD_CONSUMER_TOKEN_SECRET', 'BERGCLOUD_ACCESS_TOKEN',
                'BERGCLOUD_ACCESS_TOKEN_SECRET', 'NS_AUTH_STRING', 'DEBUG']:
        app.config[var] = os.environ.get(var)

    app.config['REDIS_URL'] = os.environ.get('REDISCLOUD_URL', False)

app.debug = app.config['DEBUG']

# Returns the Redis object (either new or existing).
def db():
    db = getattr(g, '_database', None)
    if db is None:
        if 'REDIS_URL' in app.config and app.config['REDIS_URL']:
            # If there's a REDIS_URL config variable, connect with that.
            url = urlparse.urlparse(app.config['REDIS_URL'])
            db = g._database = redis.Redis(
                    host=url.hostname, port=url.port, password=url.password)
        else:
            # Otherwise, use local Redis.
            db = g._database = redis.Redis()
    return db


# The BERG Cloud OAuth consumer object.
def consumer():
    consumer = getattr(g, '_oauth_consumer', None)
    if consumer is None:
        consumer = g._oauth_consumer = oauth.Consumer(
                        key=app.config['BERGCLOUD_CONSUMER_TOKEN'], 
                        secret=app.config['BERGCLOUD_CONSUMER_TOKEN_SECRET'])
    return consumer

# The BERG Cloud OAuth access token.
def access_token():
    token = getattr(g, '_oauth_access_token', None)
    if token is None:
        token = g._oauth_access_token = oauth.Token(
                            key=app.config['BERGCLOUD_ACCESS_TOKEN'],
                            secret=app.config['BERGCLOUD_ACCESS_TOKEN_SECRET'])
    return token

# The BERG Cloud OAuth client.
# Use something like:
#   response, data = client().request(url, 
#                       method='POST', body='Hello',
#                       headers={'Content-Type': 'text/html; charset=utf-8'})
def client():
    client = getattr(g, '_oauth_client', None)
    if client is None:
        client = g._oauth_client = oauth.Client(consumer(), access_token())
    return client


import lpapp.views

