#! /usr/bin/env python

from json import load, dumps
from pika import BlockingConnection, ConnectionParameters
from psycopg2 import connect
from SocketServer import ForkingMixIn
from sys import argv
from time import time as now
from traceback import print_exc
from urlparse import urlparse, parse_qs
from wsgiref.simple_server import WSGIServer

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

def all_topics(start_response):
    """Return a list of all topics."""
    topics = [row[0] for row in run_sql(ALL_TOPICS_SQL)]
    start_response('200', [('Content-Type', 'application/json')])
    return dumps(topics)

def last_ten(start_response, topic):
    """Get last ten facts on topic"""
    facts = run_sql(LAST_TEN_SQL, (topic,))
    start_response('200', [('Content-Type', 'application/json')])
    return dumps(facts)

def facts_after(start_response, topic, id):
    """Get all facts for topic after the given id"""
    facts = run_sql(AFTER_ID_SQL, (topic, id))
    start_response('200', [('Content-Type', 'application/json')])
    return dumps(facts)

def subscribe(start_response, topic):
    """Create a subscription for the given topic."""
    channel = rabbit_channel()
    queue = channel.queue_declare().method.queue
    channel.queue_bind(exchange=config['exchange'],
                       queue=queue,
                       routing_key=topic)        
    close_rabbit(channel)
    
    retrieval_url = RETRIEVAL_URL_TEMPLATE % (config['web_url'], topic, queue)
    start_response('200', [('Content-Type', 'application/json')])
    return dumps({'subscription_name': queue, 'retrieval_url': retrieval_url})
    
def wait_on_queue(queue, channel):
    alarm = Alarm(10)
    while True:
        fact = channel.basic_get(queue=queue, no_ack=True)[2]
        if fact is not None:
            return fact
        if alarm.is_ringing():
            return None

def get_from_queue(start_response, queue):
    """Get fact from front of queue."""
    channel = rabbit_channel()
    fact = wait_on_queue(queue, channel)
    close_rabbit(channel)
    if fact is not None:
        start_response('200', [('Content-Type', 'application/json')])
        return fact
    else:
        start_response('204', [('Content-Type', 'application/json')])
        return ''
        
def publish(start_response, topic, fact):
    """Publish the given fact."""
    channel = rabbit_channel()    
    channel.basic_publish(exchange=config['exchange'],
                          routing_key=topic,
                          body=fact)
    close_rabbit(channel)

    start_response('202', [('Content-Type', 'application/json')])
    return ''

def extract_from_path(path_elements):
    if len(path_elements) < 4 or path_elements[1] != 'topics' \
            or path_elements[2] == '':
        return None, None
    else:
        return path_elements[2:4]

def extract_query_component(name, query_components):
    return query_components.get(name, [None])[0]

def handler(environ, start_response):
    method = environ.get('REQUEST_METHOD')
    if method == 'GET':
        do_GET(environ, start_response)
    elif method == 'POST':
        do_POST(environ, start_response)
    else:
        start_response('405', [('Content-Type', 'application/json')])
        return ''

def do_GET(environ, start_response):
    query_components = parse_qs(environ.get('QUERY_STRING', ''))    
    after_id = extract_query_component('after_id', query_components)
    sub_id = extract_query_component('subscription_id', query_components)

    topic, res = extract_from_path(environ['PATH_INFO'].split('/'))
    
    if topic is None:
        return [all_topics(start_response)]
    elif res == 'facts' and after_id is not None and after_id.isdigit():
        return [facts_after(start_response, topic, int(after_id))]
    elif res == 'facts' and sub_id is not None:
        return [get_from_queue(start_response, sub_id)]
    elif res == 'facts':
        return [last_ten(start_response, topic)]
    else:
        start_response('400', [('Content-Type', 'text/plain')])
        return ['']

def do_POST(environ, start_response):
    content_len = int(environ.get('CONTENT_LENGTH', 0))
    data = environ['wsgi.input'].read(content_len)
    
    topic, res = extract_from_path(environ['PATH_INFO'].split('/'))
    
    if res == 'subscription':
        subscribe(start_response, topic)
    elif res == 'facts':
        publish(start_response, topic, data)
    else:
        start_response('400', [('Content-Type', 'text/plain')])
        return ['']

class ForkingServer(ForkingMixIn, WSGIServer):
    pass

if __name__ == '__main__':
    host = config['web_host']
    port = config['web_port']
    server = ForkingWSGIServer((host, port), WSGIRequestHandler))
    server.set_app(app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
