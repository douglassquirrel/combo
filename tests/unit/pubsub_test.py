#! /usr/bin/env python

from mock import Mock
from json import dumps
from logging import getLogger, WARNING
from pika import BlockingConnection, ConnectionParameters
from sys import exit
from time import time as now
from unittest import TestCase
from web.spinner import spin
from web.pubsub import PubSub

getLogger('pika').setLevel(WARNING)

HOST = 'localhost'
PORT = 5672
EXCHANGE = 'unittest'
FACT = {"headline": "Aliens Land", "body": "They just arriv--AAGH!"}

class PubSubTest(TestCase):
    def setUp(self):
        try:
            self.conn = BlockingConnection(ConnectionParameters(host=HOST,
                                                                port=PORT))
        except Exception as e:
            print e
            print 'Expect RabbitMQ running on %s at port %d' % (HOST, PORT)
            exit(1)

        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange=EXCHANGE, type='topic')
        self.pubsub = PubSub(HOST, PORT, EXCHANGE)

    def test_publish(self):
        queue = self.channel.queue_declare(exclusive=True).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key='publish_test_topic')
        self.pubsub.publish('publish_test_topic', dumps(FACT))
        self._wait_for_queue(queue, FACT, 'publication')

    def test_subscribe(self):
        queue = self.pubsub.subscribe('subscribe_test_topic')
        self.channel.basic_publish(exchange=EXCHANGE,
                                   routing_key='subscribe_test_topic',
                                   body=dumps(FACT))
        self._wait_for_queue(queue, FACT, 'published fact to arrive')

    def test_fetch_from_sub(self):
        queue = self.channel.queue_declare(exclusive=False).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key='fetch_from_sub_test_topic')
        self.channel.basic_publish(exchange=EXCHANGE,
                                   routing_key='fetch_from_sub_test_topic',
                                   body=dumps(FACT))
        fact = self.pubsub.fetch_from_sub('fetch_from_sub_test_topic', queue)
        self.assertEqual(fact, dumps(FACT))

    def test_fetch_from_sub_timeout(self):
        queue = self.channel.queue_declare(exclusive=False).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key='timeout_test_topic')
        spin = Mock(return_value=None)
        result = self.pubsub.fetch_from_sub('timeout_test_topic', queue,
                                            spin=spin)
        self.assertIsNone(result)
        self.assertEqual(10, spin.call_args[0][1])

    def _wait_for_queue(self, queue, fact, waiting_for):
        result = spin(lambda: self._check_queue(queue), 1)
        if result is not None:
            self.assertEqual(dumps(fact), result)
        else:
            self.fail('timed out waiting for %s' % (waiting_for,))

    def _check_queue(self, queue):
        return self.channel.basic_get(queue=queue, no_ack=True)[2]
