#! /usr/bin/env python

from mock import Mock
from json import dumps
from logging import getLogger, WARNING
from pika import BlockingConnection, URLParameters
from Queue import Empty, Queue as PythonQueue
from sys import exit
from time import sleep
from threading import Thread
from traceback import print_exc
from unittest import TestCase
from web.spinner import spin
from web.pubsub import PubSub, PubSubError

getLogger('pika').setLevel(WARNING)

RABBIT_URL = 'amqp://guest:guest@localhost:5672'
EXCHANGE = 'unittest'
FACT = {"headline": "Aliens Land", "body": "They just arriv--AAGH!"}
FACT2 = {"headline": "Moon Eaten", "body": "It's just gone!"}

class PubSubTest(TestCase):
    def setUp(self):
        try:
            self.conn = BlockingConnection(URLParameters(RABBIT_URL))
        except Exception as e:
            print 'Exception: %s' % e.message
            print_exc()
            print 'Expect RabbitMQ running on %s' % (RABBIT_URL,)
            exit(1)

        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange=EXCHANGE, type='topic')
        self.pubsub = PubSub(RABBIT_URL, EXCHANGE)

    def test_publish(self):
        queue = self.channel.queue_declare(exclusive=True).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key='publish_test_topic')
        self.pubsub.publish('publish_test_topic', FACT)
        self._wait_for_queue(queue, FACT, 'publication')

    def test_subscribe(self):
        queue = self.pubsub.subscribe('subscribe_test_topic')
        self._publish_fact('subscribe_test_topic', FACT)
        self._wait_for_queue(queue, FACT, 'published fact to arrive')

    def test_fetch_from_sub(self):
        queue = self.channel.queue_declare(exclusive=False).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key='fetch_from_sub_test_topic')
        self.channel.basic_publish(exchange=EXCHANGE,
                                   routing_key='fetch_from_sub_test_topic',
                                   body=dumps(FACT))
        fact = self.pubsub.fetch_from_sub('fetch_from_sub_test_topic',
                                          queue, 2)
        self.assertEqual(fact, FACT)

    def test_fetch_from_sub_timeout(self):
        queue = self.channel.queue_declare(exclusive=False).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key='timeout_test_topic')
        spin = Mock(return_value=None)
        result = self.pubsub.fetch_from_sub('timeout_test_topic', queue,
                                            5, spin=spin)
        self.assertIsNone(result)
        self.assertEqual(5, spin.call_args[0][1])

    def test_fetch_from_sub_with_nonexistent_sub_id(self):
        try:
            self.pubsub.fetch_from_sub('fetch_from_sub_bad_id_test',
                                       'does_not_exist', 1)
            self.fail('Should raise PubSubError when sub id does not exist')
        except PubSubError:
            pass # Expected

    def test_consume(self):
        queue = PythonQueue()
        thread = Thread(target=self._consume_caller, args=('news', queue))
        thread.daemon = True
        thread.start()
        sleep(0.1)
        self._publish_fact('news', FACT)
        self._publish_fact('news', FACT2)
        self._assertPythonQueue(queue, {'topic': 'news', 'fact': FACT})
        self._assertPythonQueue(queue, {'topic': 'news', 'fact': FACT2})

    def _consume_caller(self, topic, queue):
        consumer = lambda t, f: queue.put({'topic': t, 'fact': f})
        self.pubsub.consume(topic, consumer)

    def _publish_fact(self, topic, fact):
        self.channel.basic_publish(exchange=EXCHANGE,
                                   routing_key=topic,
                                   body=dumps(fact))

    def _assertPythonQueue(self,queue, expected):
        try:
            actual = queue.get(block=True, timeout=1)
            self.assertEqual(expected, actual)
        except Empty:
            self.fail('timed out waiting for %s' % (expected,))

    def _wait_for_queue(self, queue, fact, waiting_for):
        result = spin(lambda: self._check_queue(queue), 1)
        if result is not None:
            self.assertEqual(dumps(fact), result)
        else:
            self.fail('timed out waiting for %s' % (waiting_for,))

    def _check_queue(self, queue):
        return self.channel.basic_get(queue=queue, no_ack=True)[2]
