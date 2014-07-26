#! /usr/bin/env python

from json import loads
from pika import BlockingConnection, ConnectionParameters

RABBIT_MQ_HOST = '54.76.183.35'
RABBIT_MQ_PORT = 5672

def announce(ch, method, properties, body):
    product = loads(body)
    print "New product! %s" % (product,)

connection = BlockingConnection(ConnectionParameters(host=RABBIT_MQ_HOST,
                                                     port=RABBIT_MQ_PORT))
channel = connection.channel()

channel.exchange_declare(exchange='alex2', type='topic')

result = channel.queue_declare(exclusive=True)
queue = result.method.queue

channel.queue_bind(exchange='alex2', queue=queue, routing_key='new_products')

channel.basic_consume(announce, queue=queue, no_ack=True)
channel.start_consuming()

