#! /usr/bin/env python

from json import loads, dumps
from pika import BlockingConnection, ConnectionParameters

RABBIT_MQ_HOST = '54.76.183.35'
RABBIT_MQ_PORT = 5672

def shipping(ch, method, properties, body):
    product = loads(body)
    sku, price = product['sku'], product['price']
    if price < 50:
        shipping = 5.0
    else:
        shipping = 10.0
    shipping_fact = {'sku': sku, 'shipping': shipping}

    print 'Calculated shipping %s' % (shipping_fact,)

    channel.basic_publish(exchange='alex2',
                          routing_key='shipping',
                          body=dumps(shipping_fact))

connection = BlockingConnection(ConnectionParameters(host=RABBIT_MQ_HOST,
                                                     port=RABBIT_MQ_PORT))
channel = connection.channel()

channel.exchange_declare(exchange='alex2', type='topic')

result = channel.queue_declare(exclusive=True)
queue = result.method.queue

channel.queue_bind(exchange='alex2', queue=queue, routing_key='new_products')

channel.basic_consume(shipping, queue=queue, no_ack=True)
channel.start_consuming()
