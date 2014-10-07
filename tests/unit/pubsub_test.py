#! /usr/bin/env python

from mock import Mock
from logging import getLogger, WARNING
from pika import BlockingConnection, ConnectionParameters
from time import time as now
from unittest import TestCase
from web.pubsub import PubSub

getLogger('pika').setLevel(WARNING)

HOST = 'localhost'
PORT = 5672
EXCHANGE = 'unittest'
TOPIC = 'news'
FACT = {"headline": "Aliens Land", "body": "They just arriv--AAGH!"}

class Alarm:
    def __init__(self, duration):
        if duration is not None:
            self.alarm_time = now() + duration
        else:
            self.alarm_time = None

    def is_ringing(self):
        return self.alarm_time is not None and now() > self.alarm_time

class PubSubTest(TestCase):
    def setUp(self):
        self.conn = BlockingConnection(ConnectionParameters(host=HOST,
                                                            port=PORT))
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange=EXCHANGE, type='topic')

    def test_publish(self):
        queue = self.channel.queue_declare(exclusive=True).method.queue
        self.channel.queue_bind(exchange=EXCHANGE, queue=queue,
                                routing_key=TOPIC)
        pubsub = PubSub(HOST, PORT, EXCHANGE)
        pubsub.publish(TOPIC, FACT)
        alarm = Alarm(1)
        while True:
            result = self.channel.basic_get(queue=queue, no_ack=True)[2]
            if result is not None:
                self.assertEqual(FACT, result)
            if alarm.is_ringing():
                self.fail('timed out waiting for publication')
