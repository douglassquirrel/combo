#!/usr/bin/env python
from pika import BlockingConnection, ConnectionParameters
from sys import argv

EXCHANGE = 'combotest'

host = argv[1]
connection = BlockingConnection(ConnectionParameters(host=host, port=5672))
channel = connection.channel()
channel.exchange_declare(exchange=EXCHANGE, type='topic')

result = channel.queue_declare()
queue = result.method.queue
channel.queue_bind(exchange=EXCHANGE,
                   queue=queue,
                   routing_key='combotest')

channel.basic_publish(exchange=EXCHANGE,
                      routing_key='combotest',
                      body='Jazz Hands!')
print "Sent test message"
received_message = channel.basic_get(queue=queue, no_ack=True)[2]
print "Received message %s" % (received_message,)

connection.close()
