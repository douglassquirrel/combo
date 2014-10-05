#! /usr/bin/env python

from flask import Flask, Response
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
    return respond_json(topics)

@app.route('/topics/<topic>/subscription', methods=['POST'])
def subscription(topic):
    subscription_id = app.config['PUBSUB'].subscribe(topic)
    return respond_json(subscription_id)

@app.route('/topics/<topic>/facts', methods=['GET'])
def get_facts(topic):
    return '[]'

@app.route('/topics/<topic>/facts', methods=['POST'])
def publish_fact(topic):
    return ''

def respond(data, mimetype):
    response = Response(data, mimetype=mimetype)
    response.charset = app.config['CHARSET']
    return response

def respond_json(data):
    return respond(dumps(data), mimetype='application/json')

default_config_file = pathjoin(dirname(__file__), 'settings.cfg')
config_file = environ.get('COMBO_SETTINGS_FILE', default_config_file)
app.config.from_pyfile(config_file)

if __name__ == '__main__':
    app.run()

