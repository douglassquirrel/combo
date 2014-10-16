#! /usr/bin/env python

from flask import Flask, Response, request, url_for
from json import dumps, loads
from logging import INFO, StreamHandler
from os import environ
from os.path import dirname, join as pathjoin

app = Flask('combo')

@app.route('/')
def home():
    return _respond(app.config['HOME_HTML'], mimetype='text/html')

@app.route('/topics', methods=['GET'])
def topics():
    topics = app.config['FACTSPACE'].list_topics()
    return _respond_json(map(_format_topic, topics))

@app.route('/topics/<topic>/subscriptions', methods=['POST'])
def subscription(topic):
    subscription_id = app.config['PUBSUB'].subscribe(topic=topic)
    return _respond_json(_format_subscription(topic, subscription_id))

@app.route('/topics/<topic>/facts', methods=['GET'])
def get_facts(topic):
    factspace = app.config['FACTSPACE']
    after_id = request.args.get('after_id')
    if after_id is not None:
        return _respond_json(factspace.after_id(topic, int(after_id)))
    else:
        return _respond_json(factspace.last_n(topic, 10))

@app.route('/topics/<topic>/subscriptions/<sub_id>/next', methods=['GET'])
def get_next_fact_from_sub(topic, sub_id):
    pubsub = app.config['PUBSUB']
    result = pubsub.fetch_from_sub(topic, sub_id)
    if result is not None:
        return _respond_json(result)
    else:
        return _respond('', 'text/plain', 204)

@app.route('/topics/<topic>/facts', methods=['POST'])
def publish_fact(topic):
    fact = request.get_json(force=True)
    app.config['PUBSUB'].publish(topic=topic, fact=fact)
    return _respond('', 'text/plain', status=202)

def _format_topic(topic):
    return {'topic_name': topic,
            'subscription_url': _ext_url_for('subscription', topic),
            'facts_url': _ext_url_for('get_facts', topic)}

def _format_subscription(topic, sub_id):
    RETRIEVAL_URL = _ext_url_for('get_next_fact_from_sub', topic, sub_id)
    return {'retrieval_url': RETRIEVAL_URL, 'subscription_id': sub_id}

def _respond(data, mimetype, status=200):
    response = Response(data, mimetype=mimetype)
    response.charset = app.config['CHARSET']
    response.status_code = status
    return response

def _respond_json(data):
    return _respond(dumps(data), mimetype='application/json')

def _ext_url_for(function, topic, sub_id=None):
    return url_for(function, topic=topic, sub_id=sub_id, _external=True)

default_config_file = pathjoin(dirname(__file__), 'settings.py')
config_file = environ.get('COMBO_SETTINGS_FILE', default_config_file)
app.config.from_pyfile(config_file)

if not app.debug:
    stream_handler = StreamHandler()
    stream_handler.setLevel(INFO)
    app.logger.addHandler(stream_handler)

if __name__ == '__main__':
    app.run()
