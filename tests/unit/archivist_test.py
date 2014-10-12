#! /usr/bin/env python

from mock import Mock
from unittest import TestCase
from archivist.archivist import run

TOPIC_WILDCARD = '#'
TOPIC = 'story.creation'
FACT = {"headline": "Aliens Land", "body": "They just arriv--AAGH!"}

class ArchivistTest(TestCase):
    def test_run(self):
        factspace = Mock()
        factspace.add_fact = Mock()
        pubsub = Mock()
        pubsub.consume = Mock()
        run(factspace=factspace, pubsub=pubsub)
        
        consume_args = pubsub.consume.call_args[0]
        self.assertEqual(2, len(consume_args))
        topic_consumed, consumer = consume_args
        self.assertEqual(TOPIC_WILDCARD, topic_consumed)
        
        consumer(TOPIC, FACT)
        factspace.add_fact.assert_called_once_with(TOPIC, FACT)
        
