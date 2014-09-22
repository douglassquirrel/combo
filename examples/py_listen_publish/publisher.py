#! /usr/bin/env python

from json import dumps
from pika import BlockingConnection, ConnectionParameters
from sys import argv

print argv

host = '54.76.183.35'
connection = BlockingConnection(ConnectionParameters(host=host, port=5672))
channel = connection.channel()

product = {'sku': argv[1], 'name': argv[2], 'price': float(argv[3])}
channel.basic_publish(exchange='alex2',
                      routing_key='new_products',
                      body=dumps(product))
print 'Published product %s' % (product,)
connection.close()
