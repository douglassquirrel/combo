#! /usr/bin/env python

from flask import Flask, Response, request, url_for
from json import dumps
from os import environ
from os.path import dirname, join as pathjoin

app = Flask('combo')

@app.route('/')
def home():
    return respond(app.config['HOME_HTML'], mimetype='text/html')

@app.route('/topics', methods=['GET'])
def topics():
    topics = app.config['FACTSPACE'].list_topics()
    return respond_json(map(format_topic, topics))

@app.route('/topics/<topic>/subscription', methods=['POST'])
def subscription(topic):
    subscription_id = app.config['PUBSUB'].subscribe(topic=topic)
    return respond_json(format_subscription(topic, subscription_id))

@app.route('/topics/<topic>/facts', methods=['GET'])
def get_facts(topic):
    return '[]'

@app.route('/topics/<topic>/facts', methods=['POST'])
def publish_fact(topic):
    app.config['PUBSUB'].publish(topic=topic, fact=request.data)
    return respond('', 'text/plain', status=202)

def format_topic(topic):
    return {'topic_name': topic,
            'subscription_url': ext_url_for('subscription', topic),
            'facts_url': ext_url_for('get_facts', topic)}

def format_subscription(topic, sub_id):
    RETRIEVAL_URL = ext_url_for('get_facts', topic) \
                      + '?subscription_id=%s' % (sub_id,)
    return {'retrieval_url': RETRIEVAL_URL, 'subscription_id': sub_id}

def respond(data, mimetype, status=200):
    response = Response(data, mimetype=mimetype)
    response.charset = app.config['CHARSET']
    response.status_code = status
    return response

def respond_json(data):
    return respond(dumps(data), mimetype='application/json')

def ext_url_for(function, topic):
    return url_for(function, topic=topic, _external=True)

default_config_file = pathjoin(dirname(__file__), 'settings.cfg')
config_file = environ.get('COMBO_SETTINGS_FILE', default_config_file)
app.config.from_pyfile(config_file)

if __name__ == '__main__':
    app.run()
