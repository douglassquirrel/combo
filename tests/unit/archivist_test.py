#! /usr/bin/env python

from mock import Mock
from unittest import TestCase
from archivist.archivist import run

TOPIC_WILDCARD = '#'
TOPIC = 'story.creation'
FACTS = {"headline": "Aliens Land", "body": "They just arriv--AAGH!"}

class ArchivistTest(TestCase):
    def test_run(self):
        pubsub = Mock()
        pubsub.consume = Mock()
        run(pubsub=pubsub)
        self.assertEqual(TOPIC_WILDCARD, pubsub.consume.call_args[0][0])
