#! /usr/bin/env python  

from json import loads
from unittest import TestCase
from web import combo_server

TEST_HOME_PAGE = 'test home page'
TEST_TOPICS = ['headlines', 'story.creation', 'story.update']
TEST_TOPIC = 'story.creation'
TEST_SUB_ID = '%s.subscription' % (TEST_TOPIC,)

class MockFactspace:
    def list_topics(self):
        return TEST_TOPICS

class MockPubSub:
    def subscribe(self, topic):
        return '%s.subscription' % (topic,)

class ComboServerTest(TestCase):
    def setUp(self):
        self.app = combo_server.app
        self.app.testing = True
        self.app.config['FACTSPACE'] = MockFactspace()
        self.app.config['PUBSUB'] = MockPubSub()
        self.client = self.app.test_client()

    def tearDown(self):
        pass

    def test_home(self):
        self.app.config['HOME_HTML'] = TEST_HOME_PAGE
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response.content_type)
        self.assertEqual(TEST_HOME_PAGE, response.data)

    def test_topics(self):
        response = self.client.get('/topics')
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(TEST_TOPICS, loads(response.data))

    def test_subscription(self):
        response = self.client.post('/topics/%s/subscription' % (TEST_TOPIC,))
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(TEST_SUB_ID, loads(response.data))
