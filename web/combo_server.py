#! /usr/bin/env python

from flask import Flask, Response
from os.path import dirname, join as pathjoin
app = Flask('combo')

@app.route('/')
def home():
    with open(pathjoin(dirname(__file__), 'home.html')) as f:
        home = f.read()
    return Response(home, content_type='text/html; charset=utf-8')

if __name__ == '__main__':
    app.run()

