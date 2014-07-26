#! /usr/bin/env python

from pika import BlockingConnection, ConnectionParameters
from psycopg2 import connect

RABBIT_MQ_HOST = '54.76.183.35'
RABBIT_MQ_PORT = 5672

POSTGRES_HOST = 'microservices.cc9uedlzx2lk.eu-west-1.rds.amazonaws.com'
POSTGRES_DATABASE = 'micro'
POSTGRES_USER = 'microservices'
POSTGRES_PASSWORD = 'microservices'

def store(ch, method, properties, body):
    topic, content = method.routing_key, body
    conn = connect(host=POSTGRES_HOST, database=POSTGRES_DATABASE, 
                   user=POSTGRES_USER, password=POSTGRES_PASSWORD)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO facts VALUES (%s, now(), %s);',
                   (topic, content))
    conn.commit()
    cursor.close()
    connection.close()
    print 'Recorded topic %s, content %s' % (topic, content)

connection = BlockingConnection(ConnectionParameters(host=RABBIT_MQ_HOST,
                                                     port=RABBIT_MQ_PORT))
channel = connection.channel()

channel.exchange_declare(exchange='alex2', type='topic')

result = channel.queue_declare(exclusive=True)
queue = result.method.queue

channel.queue_bind(exchange='alex2', queue=queue, routing_key='*')

channel.basic_consume(store, queue=queue, no_ack=True)
channel.start_consuming()
