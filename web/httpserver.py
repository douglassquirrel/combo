\#! /usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from json import load, dump
from pika import BlockingConnection, ConnectionParameters
from psycopg2 import connect
from sys import argv

ALL_TOPICS_SQL = 'SELECT DISTINCT topic FROM facts'

with open(argv[1]) as config_file:
    config = load(config_file)

class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path_elements = self.path.split('/')
        if len(path_elements) < 3 or path_elements[1] != 'topics':
            self.bad_request()
        elif len(path_elements) < 4 or path_elements[3] == '':
            self.publish(path_elements[2])
        elif path_elements[3] == 'queue':
            self.make_queue(path_elements[2])
        else:
            self.bad_request()

    def bad_request(self):
        self.send_response(400)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def all_topics(self):
        """Return a list of all topics."""
        conn = connect(host=config['pg_host'], database=config['pg_database'],
                       user=config['pg_user'], password=config['pg_password'])
        cursor = conn.cursor()
        try:
            topic, content = method.routing_key, body
            cursor.execute(ALL_TOPICS_SQL)
            topics = [row[0] for row in cursor.fetchall()]
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            dump(topics, self.wfile)
        except Exception as e:
            print e.message
        finally:
            cursor.close()
            conn.close()

    def make_queue(self, topic):
        """Create a queue for the given topic."""
        
    def publish(self, topic):
        """Publish the given fact."""
        content_len = int(self.headers.getheader('content-length', 0))
        fact = self.rfile.read(content_len)

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
