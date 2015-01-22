#! /usr/bin/env python

from flask import Flask, Response, request, url_for
from json import dumps, loads
from logging import INFO, StreamHandler
from os import environ
from os.path import dirname, join as pathjoin
from web.pubsub import PubSubError
from traceback import print_exc

app = Flask('combo')

@app.route('/')
def home():
    home_page = _get_home_page()
    return _respond(home_page, mimetype='text/html')

def _get_home_page():
    repl = {'%ROOT_URL%': _ext_url_for('home'),
            '%TOPICS_URL%': _ext_url_for('topics'),
            '%FACTS_URL%': _ext_url_for('get_facts', topic='TOPIC'),
            '%SUBSCRIPTION_URL%': 
            _ext_url_for('subscription', topic='TOPIC'),
            '%FROM_SUB_URL%':
                _ext_url_for('get_next_fact_from_sub',
                             topic='TOPIC', sub_id='SUB_ID')}
    page = app.config['HOME_HTML']
    return reduce(lambda x, y: x.replace(y, repl[y]), repl, page)

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
    if after_id is None:
        return _respond_json(factspace.last_n(topic, 10))
    elif _is_valid_int_string(after_id):
        return _respond_json(factspace.after_id(topic, int(after_id)))
    else:
        return _bad_request()

@app.route('/topics/<topic>/subscriptions/<sub_id>/next', methods=['GET'])
def get_next_fact_from_sub(topic, sub_id):
    try:
        patience_string = request.headers.get('Patience', '2')
        if patience_string == '' or not _is_valid_int_string(patience_string):
            return _bad_request()
        timeout = int(patience_string)
        if timeout <= 0:
            return _bad_request()
        pubsub = app.config['PUBSUB']
        result = pubsub.fetch_from_sub(topic, sub_id, timeout)
        if result is not None:
            return _respond_json(result)
        else:
            return _respond('', 'text/plain', 204)
    except PubSubError as e:
        print_exc(file=app.config['ERROR_OUT'])
        return _respond('', 'text/plain', 404)

@app.route('/topics/<topic>/facts', methods=['POST'])
def publish_fact(topic):
    fact = request.get_json(force=True, silent=True)
    if not isinstance(fact, dict):
        return _bad_request()
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
    response.headers.add('Expires', 'Thu, 01 Jan 1970 00:00:00 GMT')
    response.headers.add('Cache-control', 'no-cache, must-revalidate')
    return response

def _respond_json(data):
    return _respond(dumps(data), mimetype='application/json')

def _bad_request():
    return _respond('', 'text/plain', status=400)

def _is_valid_int_string(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def _ext_url_for(function, topic=None, sub_id=None):
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
