#! /usr/bin/env python

from flask import Flask, Response
from os import environ
from os.path import dirname, join as pathjoin

app = Flask('combo')

@app.route('/')
def home():
    return respond(app.config['HOME_HTML'], mimetype='text/html')

def respond(data, mimetype):
    response = Response(data, mimetype=mimetype)
    response.charset = app.config['CHARSET']
    return response

default_config_file = pathjoin(dirname(__file__), 'settings.cfg')
config_file = environ.get('COMBO_SETTINGS_FILE', default_config_file)
app.config.from_pyfile(config_file)

if __name__ == '__main__':
    app.run()

