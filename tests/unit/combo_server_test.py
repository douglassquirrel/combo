#! /usr/bin/env python

from json import loads
from unittest import TestCase
from web import combo_server

TEST_HOME_PAGE = 'test home page'
TEST_TOPICS = ['headlines', 'story.creation', 'story.update']
#Use template, map here
TEST_TOPICS_RESPONSE = \
    [{'topic_name': 'headlines',
      'facts_url': 'http://foo.com/topics/headlines/facts',
      'subscription_url': 'http://foo.com/topics/headlines/subscription'},
     {'topic_name': 'story.creation',
      'facts_url': 'http://foo.com/topics/story.creation/facts',
      'subscription_url': 'http://foo.com/topics/story.creation/subscription'},
     {'topic_name': 'story.update',
      'facts_url': 'http://foo.com/topics/story.update/facts',
      'subscription_url': 'http://foo.com/topics/story.update/subscription'}]
TEST_TOPIC = 'story.creation'
TEST_SUB_ID = '%s.subscription' % (TEST_TOPIC,)
TEST_FACT = '{"headline": "Aliens Land", "body": "They just arriv--AAGH!"}'

class MockFactspace:
    def list_topics(self):
        return TEST_TOPICS

class MockPubSub:
    def subscribe(self, topic):
        self.last_subscription = {'topic': topic}
        return '%s.subscription' % (topic,)

    def publish(self, topic, fact):
        self.last_fact = {'topic': topic, 'fact': fact}

class ComboServerTest(TestCase):
    def setUp(self):
        self.app = combo_server.app
        self.app.testing = True
        self.app.config['SERVER_NAME'] = 'foo.com'
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
        self.assertEqual(TEST_TOPICS_RESPONSE, loads(response.data))

    def test_publish(self):
        response = self.client.post('/topics/%s/facts' % (TEST_TOPIC,),
                                    data=TEST_FACT)
        self.assertEqual(202, response.status_code)
        self.assertEqual('text/plain; charset=utf-8', response.content_type)
        self.assertEqual({'topic': TEST_TOPIC, 'fact': TEST_FACT},
                         self.app.config['PUBSUB'].last_fact)

    def test_get_last_10_facts(self):
        pass
    def test_get_facts_after_id(self):
        pass
    def test_get_fact_from_subscription(self):
        pass
    def test_get_fact_from_subscription_and_timeout(self):
        pass

    def test_subscription(self):
        response = self.client.post('/topics/%s/subscription' % (TEST_TOPIC,))
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(TEST_SUB_ID, loads(response.data))
        #assert correct format
        self.assertEqual({'topic': TEST_TOPIC},
                         self.app.config['PUBSUB'].last_subscription)
