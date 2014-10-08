#! /usr/bin/env python

from mock import Mock
from json import dumps
from logging import getLogger, WARNING
from pika import BlockingConnection, ConnectionParameters
from time import time as now
from unittest import TestCase
from web.spinner import spin
from web.pubsub import PubSub

getLogger('pika').setLevel(WARNING)

HOST = 'localhost'
PORT = 5672
EXCHANGE = 'unittest'
TOPIC = 'news'
FACT = {"headline": "Aliens Land", "body": "They just arriv--AAGH!"}

class PubSubTest(TestCase):
    def setUp(self):
        self.conn = BlockingConnection(ConnectionParameters(host=HOST,
                                                            port=PORT))
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange=EXCHANGE, type='topic')
        self.pubsub = PubSub(HOST, PORT, EXCHANGE)

    def test_publish(self):
        queue = self.channel.queue_declare(exclusive=True).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key=TOPIC)
        self.pubsub.publish(TOPIC, dumps(FACT))
        result = spin(lambda: self._check_queue(queue), 1)
        if result is not None:
            self.assertEqual(dumps(FACT), result)
        else:
            self.fail('timed out waiting for publication')

    def test_subscribe(self):
        sub_id = self.pubsub.subscribe(TOPIC)
        queue = self.channel.queue_declare(queue=sub_id, passive=True)

    def _check_queue(self, queue):
        return self.channel.basic_get(queue=queue, no_ack=True)[2]
