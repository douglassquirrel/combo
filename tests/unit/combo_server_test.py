#! /usr/bin/env python

from json import loads
from mock import Mock
from unittest import TestCase
from web import combo_server

TEST_HOME_PAGE = 'test home page'
TEST_TOPICS = ['headlines', 'story.creation', 'story.update']
FACTS_URL_PATTERN = 'http://foo.com/topics/%s/facts'
SUB_URL_PATTERN = 'http://foo.com/topics/%s/subscription'
def make_topic_response_element(topic):
    return {'topic_name': topic,
            'facts_url': FACTS_URL_PATTERN % (topic,),
            'subscription_url': SUB_URL_PATTERN % (topic,)}
TEST_TOPICS_RESPONSE = map(make_topic_response_element, TEST_TOPICS)
TEST_TOPIC = 'story.creation'
TEST_SUB_ID = '%s.subscription' % (TEST_TOPIC,)
RETR_URL_PATTERN = 'http://foo.com/topics/%s/facts?subscription_id=%s'
TEST_SUB_RESPONSE = {'retrieval_url': RETR_URL_PATTERN % (TEST_TOPIC,
                                                          TEST_SUB_ID),
                     'subscription_id': TEST_SUB_ID}
TEST_FACT = '{"headline": "Aliens Land", "body": "They just arriv--AAGH!"}'

class ComboServerTest(TestCase):
    def setUp(self):
        self.app = combo_server.app
        self.app.testing = True
        self.app.config['SERVER_NAME'] = 'foo.com'
        self.client = self.app.test_client()

    def test_home(self):
        self.app.config['HOME_HTML'] = TEST_HOME_PAGE
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response.content_type)
        self.assertEqual(TEST_HOME_PAGE, response.data)

    def test_topics(self):
        factspace = self._mock_factspace()
        response = self.client.get('/topics')
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.content_type)
        factspace.list_topics.assert_called_with()
        self.assertEqual(TEST_TOPICS_RESPONSE, loads(response.data))

    def test_publish(self):
        pubsub = self._mock_pubsub(TEST_TOPIC, TEST_FACT)
        response = self.client.post('/topics/%s/facts' % (TEST_TOPIC,),
                                    data=TEST_FACT)
        self.assertEqual(202, response.status_code)
        self.assertEqual('text/plain; charset=utf-8', response.content_type)
        pubsub.publish.assert_called_once_with(topic=TEST_TOPIC,
                                               fact=TEST_FACT)

    def test_get_last_10_facts(self):
        pass
    def test_get_facts_after_id(self):
        pass
    def test_get_fact_from_subscription(self):
        pass
    def test_get_fact_from_subscription_and_timeout(self):
        pass

    def test_subscription(self):
        pubsub = self._mock_pubsub(TEST_TOPIC, TEST_FACT)
        response = self.client.post('/topics/%s/subscription' % (TEST_TOPIC,))
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(TEST_SUB_RESPONSE, loads(response.data))
        #assert correct format
        pubsub.subscribe.assert_called_once_with(topic=TEST_TOPIC)

    def _mock_factspace(self):
        MockFactspace = Mock()
        MockFactspace.list_topics = Mock(return_value=TEST_TOPICS)
        self.app.config['FACTSPACE'] = MockFactspace
        return MockFactspace

    def _mock_pubsub(self, topic, fact):
        MockPubSub = Mock()
        MockPubSub.subscribe = Mock(return_value='%s.subscription' % (topic,))
        MockPubSub.publish = Mock(return_value={'topic': topic, 'fact': fact})
        self.app.config['PUBSUB'] = MockPubSub
        return MockPubSub
