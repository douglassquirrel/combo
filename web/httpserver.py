#! /usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from json import load
from pika import BlockingConnection, ConnectionParameters
from sys import argv

with open(argv[1]) as config_file:
    config = load(config_file)

class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Publish the given fact."""
        content_len = int(self.headers.getheader('content-length', 0))
        fact = self.rfile.read(content_len)
        topic = self.path.split('/')[2]

        connection = BlockingConnection(ConnectionParameters(host=config['rabbit_host'],
                                                             port=config['rabbit_port']))
        channel = connection.channel()
        channel.exchange_declare(exchange=config['exchange'], type='topic')

        channel.basic_publish(exchange=config['exchange'],
                              routing_key=topic,
                              body=fact)
        connection.close()

        self.send_response(202)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

if __name__ == '__main__':
    httpd = HTTPServer((config['web_host'], config['web_port']), MyHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
