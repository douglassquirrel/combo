#! /usr/bin/env python

from json import load
from pika import BlockingConnection, ConnectionParameters
from psycopg2 import connect
from sys import argv

with open(argv[1]) as config_file:
    config = load(config_file)

def store(ch, method, properties, body):
    conn = connect(host=config['pg_host'], database=config['pg_database'], 
                   user=config['pg_user'], password=config['pg_password'])
    cursor = conn.cursor()

    try:
        topic, content = method.routing_key, body
        cursor.execute('INSERT INTO facts VALUES (%s, now(), %s);',
                       (topic, content))
        conn.commit()
        print 'Recorded topic %s, content %s' % (topic, content)
    except Exception as e:
        print e.message
    finally:
        cursor.close()
        conn.close()        

conn = BlockingConnection(ConnectionParameters(host=config['rabbit_host'],
                                               port=config['rabbit_port']))
channel = conn.channel()

channel.exchange_declare(exchange=config['exchange'], type='topic')

result = channel.queue_declare(exclusive=True)
queue = result.method.queue

channel.queue_bind(exchange=config['exchange'], queue=queue, routing_key='#')

channel.basic_consume(store, queue=queue, no_ack=True)
channel.start_consuming()
