#! /usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from json import load, dumps
from pika import BlockingConnection, ConnectionParameters
from psycopg2 import connect
from SocketServer import ForkingMixIn
from sys import argv
from time import time as now
from traceback import print_exc
from urlparse import urlparse, parse_qs

ALL_TOPICS_SQL = 'SELECT DISTINCT topic FROM facts;'
LAST_TEN_SQL = '''
    SELECT id, topic, ts, content FROM
        (SELECT id, topic, round(extract(epoch from ts)) AS ts, content
             FROM facts WHERE topic = %s ORDER BY id DESC LIMIT 10)
        AS lastten
    ORDER BY id ASC;
'''
AFTER_ID_SQL = '''
SELECT id, topic, round(extract(epoch from ts)), content
    FROM facts WHERE topic = %s and id > %s;
'''
RETRIEVAL_URL_TEMPLATE = '%s/topics/%s/facts?subscription_id=%s'

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

def run_sql(sql, parameters=None):
    """Run SQL and return result"""
    conn = connect(host=config['pg_host'], database=config['pg_database'],
                   user=config['pg_user'], password=config['pg_password'])
    cursor = conn.cursor()
    try:
        if parameters is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, parameters)
        return cursor.fetchall()
    except Exception as e:
        print 'Exception: %s' % e.message
        print_exc()
        return []
    finally:
        cursor.close()
        conn.close()    

def rabbit_connect():
    host=config['rabbit_host']
    port=config['rabbit_port']
    return BlockingConnection(ConnectionParameters(host=host, port=port))

def rabbit_channel():
    connection = rabbit_connect()
    channel = connection.channel()
    channel.exchange_declare(exchange=config['exchange'], type='topic')
    return channel

def close_rabbit(channel):
    channel.connection.close()

def all_topics(respond):
    """Return a list of all topics."""
    topics = [row[0] for row in run_sql(ALL_TOPICS_SQL)]
    respond(code=200, content_type='application/json', content=dumps(topics))

def last_ten(respond, topic):
    """Get last ten facts on topic"""
    facts = run_sql(LAST_TEN_SQL, (topic,))
    respond(code=200, content_type='application/json', content=dumps(facts))

def facts_after(respond, topic, id):
    """Get all facts for topic after the given id"""
    facts = run_sql(AFTER_ID_SQL, (topic, id))
    respond(code=200, content_type='application/json', content=dumps(facts))

def subscribe(respond, topic):
    """Create a subscription for the given topic."""
    channel = rabbit_channel()
    queue = channel.queue_declare().method.queue
    channel.queue_bind(exchange=config['exchange'],
                       queue=queue,
                       routing_key=topic)        
    close_rabbit(channel)
    
    retrieval_url = RETRIEVAL_URL_TEMPLATE % (config['web_url'], topic, queue)
    content = {'subscription_name': queue, 'retrieval_url': retrieval_url}
    respond(code=200, content_type='application/json', content=content)
    
def wait_on_queue(queue, channel):
    alarm = Alarm(10)
    while True:
        fact = channel.basic_get(queue=queue, no_ack=True)[2]
        if fact is not None:
            return fact
        if alarm.is_ringing():
            return None

def get_from_queue(respond, queue):
    """Get fact from front of queue."""
    channel = rabbit_channel()
    fact = wait_on_queue(queue, channel)
    close_rabbit(channel)
    if fact is not None:
        respond(code=200, content_type='application/json', content=fact)
    else:
        respond(code=204, content_type='text/plain', content='')
        
def publish(respond, topic, fact):
    """Publish the given fact."""
    channel = rabbit_channel()    
    channel.basic_publish(exchange=config['exchange'],
                          routing_key=topic,
                          body=fact)
    close_rabbit(channel)

    respond(code=202, content_type='text/plain', content='')

def _respond(handler, code, content_type, content):
    handler.send_response(code)
    handler.send_header("Content-Type", content_type)
    handler.end_headers()
    handler.wfile.write(content)

def extract_from_path(path_elements):
    if len(path_elements) < 4 or path_elements[1] != 'topics' \
            or path_elements[2] == '':
        return None, None
    else:
        return path_elements[2:4]

def extract_query_component(name, query_components):
    return query_components.get(name, [None])[0]

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_components = parse_qs(parsed_url.query)

        after_id = extract_query_component('after_id', query_components)
        sub_id = extract_query_component('subscription_id', query_components)
        topic, res = extract_from_path(parsed_url.path.split('/'))

        respond = lambda code, content_type, content: \
                  _respond(self, code, content_type, content)

        if topic is None:
            all_topics(respond)
        elif res == 'facts' and after_id is not None and after_id.isdigit():
            facts_after(respond, topic, int(after_id))
        elif res == 'facts' and sub_id is not None:
            get_from_queue(respond, sub_id)
        elif res == 'facts':
            last_ten(respond, topic)
        else:
            respond(400, 'text/plain', '')

    def do_POST(self):
        content_len = int(self.headers.getheader('content-length', 0))
        data = self.rfile.read(content_len)

        parsed_url = urlparse(self.path)
        query_components = parse_qs(parsed_url.query)
        topic, res = extract_from_path(parsed_url.path.split('/'))

        respond = lambda code, content_type, content: \
                  _respond(self, code, content_type, content)

        if res == 'subscription':
            subscribe(respond, topic)
        elif res == 'facts':
            publish(respond, topic, data)
        else:
            respond(400, 'text/plain', '')

class ForkingServer(ForkingMixIn, HTTPServer):
    pass

if __name__ == '__main__':
    httpd = ForkingServer((config['web_host'], config['web_port']), MyHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
