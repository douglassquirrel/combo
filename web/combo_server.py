#! /usr/bin/env python

from flask import Flask, Response
app = Flask('combo')

@app.route('/')
def hello():
    return Response('Hello Flask World!', mimetype='text/plain')

if __name__ == '__main__':
    app.run()

