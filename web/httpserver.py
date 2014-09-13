#! /usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from json import load, dump
from pika import BlockingConnection, ConnectionParameters
#from psycopg2 import connect
from sys import argv
from time import time as now
from urlparse import urlparse, parse_qs

ALL_TOPICS_SQL = 'SELECT DISTINCT topic FROM facts;'
LAST_TEN_TOPICS_SQL = '''
    SELECT id, topic, ts, content FROM
        (SELECT id, topic, ts, content FROM facts ORDER BY id DESC LIMIT 10)
    ORDER BY id ASC;
'''
SINCE_ID_SQL = 'SELECT id, topic, ts, content FROM facts WHERE id >= %s'
QUEUE_URL_TEMPLATE = '%s/queues/%s'

with open(argv[1]) as config_file:
    config = load(config_file)

class Alarm:
    def __init__(self, duration):
        if duration is not None:
            self.alarm_time = now() + duration
        else:
            self.alarm_time = None

    def is_ringing(self):
        return self.alarm_time is not None and now() > self.alarm_time

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_comp = parse_qs(parsed_url.query)
        path_elements = parsed_url.path.split('/')
        if len(path_elements) < 2:
            self.bad_request()
        elif path_elements[1] == 'queues' and len(path_elements) > 2:
            self.get_from_queue(path_elements[2])
        elif path_elements[1] == 'topics':
            if len(path_elements) == 2 or path_elements[2] == '':
                self.all_topics()
            elif 'from_id' in query_comp and query_comp[from_id].isdigit():
                self.facts_since(path_elements[2], int(query_comp['from_id']))
            elif len(query_comp) == 0:
                self.last_ten_facts(path_elements[2])
            else:
                self.bad_request()
        else:
            self.bad_request()
    
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
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def all_topics(self):
        """Return a list of all topics."""
        conn = connect(host=config['pg_host'], database=config['pg_database'],
                       user=config['pg_user'], password=config['pg_password'])
        cursor = conn.cursor()
        try:
            cursor.execute(ALL_TOPICS_SQL)
            topics = [row[0] for row in cursor.fetchall()]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            dump(topics, self.wfile)
        except Exception as e:
            print e.message
        finally:
            cursor.close()
            conn.close()

    def facts_since(self, topic, id):
        """Get all facts for topic since the given id"""
        print "facts for %s since %d" % (topic, id)
    
    def last_ten_facts(self, topic):
        """Get last ten facts for topic"""
        print "last 10 for %s" % (topic,)

    def make_queue(self, topic):
        """Create a queue for the given topic."""
        connection = BlockingConnection(ConnectionParameters(host=config['rabbit_host'],
                                                             port=config['rabbit_port']))
        channel = connection.channel()
        channel.exchange_declare(exchange=config['exchange'], type='topic')
        queue = channel.queue_declare().method.queue
        channel.queue_bind(exchange=config['exchange'],
                           queue=queue,
                           routing_key=topic)        
        connection.close()

        out = {'queue_name': queue,
               'queue_url': QUEUE_URL_TEMPLATE % (config['web_url'], queue,)}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        dump(out, self.wfile)

    def wait_on_queue(self, channel, queue):
        alarm = Alarm(10)
        while True:
            fact = channel.basic_get(queue=queue, no_ack=True)[2]
            if fact is not None:
                return fact
            if alarm.is_ringing():
                return None

    def get_from_queue(self, queue):
        """Get fact from front of queue."""
        connection = BlockingConnection(ConnectionParameters(host=config['rabbit_host'],
                                                             port=config['rabbit_port']))
        channel = connection.channel()
        channel.exchange_declare(exchange=config['exchange'], type='topic')
        fact = self.wait_on_queue(channel, queue)
        connection.close()

        if fact is not None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(fact)
        else:
            self.send_response(204)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()

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
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

class ForkingServer(ForkingMixIn, HTTPServer):
    pass

if __name__ == '__main__':
    httpd = ForkingServer((config['web_host'], config['web_port']), MyHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
