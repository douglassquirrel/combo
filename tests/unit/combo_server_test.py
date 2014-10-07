#! /usr/bin/env python

from json import loads, dumps
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
TEST_FACTS = [{"headline": "Aliens Land", "body": "They just arriv--AAGH!"},
              {"headline": "Moon Eaten", "body": "It's just gone!"},
              {"headline": "Bananas Banned", "body": "Bad for teeth."}]
TEST_ID = 123

class ComboServerTest(TestCase):
    def setUp(self):
        self.app = combo_server.app
        self.app.testing = True
        self.app.config['SERVER_NAME'] = 'foo.com'
        self.client = self.app.test_client()

    def test_home(self):
        self.app.config['HOME_HTML'] = TEST_HOME_PAGE
        self._assertResponsePlain(self.client.get('/'),
                                  200, 'text/html', TEST_HOME_PAGE)

    def test_topics(self):
        factspace = self._mock_factspace()
        factspace.list_topics = Mock(return_value=TEST_TOPICS)
        self._assertResponseJSON(self.client.get('/topics'),
                                200, TEST_TOPICS_RESPONSE)
        factspace.list_topics.assert_called_with()

    def test_publish(self):
        pubsub = self._mock_pubsub()
        response = self.client.post('/topics/%s/facts' % (TEST_TOPIC,),
                                    data=dumps(TEST_FACTS[0]))
        self._assertResponsePlain(response, 202, 'text/plain', '')
        pubsub.publish.assert_called_once_with(topic=TEST_TOPIC,
                                               fact=dumps(TEST_FACTS[0]))

    def test_get_last_10_facts(self):
        factspace = self._mock_factspace()
        self._mock_pubsub()
        factspace.last_n = Mock(return_value=TEST_FACTS)
        response = self.client.get('/topics/%s/facts' % (TEST_TOPIC,))
        self._assertResponseJSON(response, 200, TEST_FACTS)
        factspace.last_n.assert_called_with(TEST_TOPIC, 10)

    def test_get_facts_after_id(self):
        factspace = self._mock_factspace()
        self._mock_pubsub()
        factspace.after_id = Mock(return_value=TEST_FACTS)
        url = '/topics/%s/facts?after_id=%d' % (TEST_TOPIC, TEST_ID)
        self._assertResponseJSON(self.client.get(url), 200, TEST_FACTS)
        factspace.after_id.assert_called_with(TEST_TOPIC, TEST_ID)

    def test_get_fact_from_subscription(self):
        self._mock_factspace()
        pubsub = self._mock_pubsub()
        pubsub.fetch_from_sub = Mock(return_value=TEST_FACTS[0])
        url = '/topics/%s/facts?subscription_id=%s' % (TEST_TOPIC, TEST_SUB_ID)
        self._assertResponseJSON(self.client.get(url), 200, TEST_FACTS[0])
        pubsub.fetch_from_sub.assert_called_with(TEST_TOPIC, TEST_SUB_ID)

    def test_get_fact_from_subscription_and_timeout(self):
        self._mock_factspace()
        pubsub = self._mock_pubsub()
        pubsub.fetch_from_sub = Mock(return_value=None)
        url = '/topics/%s/facts?subscription_id=%s' % (TEST_TOPIC, TEST_SUB_ID)
        self._assertResponsePlain(self.client.get(url), 204, 'text/plain', '')
        pubsub.fetch_from_sub.assert_called_with(TEST_TOPIC, TEST_SUB_ID)

    def test_subscription(self):
        pubsub = self._mock_pubsub()
        pubsub.subscribe = Mock(return_value='%s.subscription' % (TEST_TOPIC,))
        response = self.client.post('/topics/%s/subscription' % (TEST_TOPIC,))
        self._assertResponseJSON(response, 200, TEST_SUB_RESPONSE)
        pubsub.subscribe.assert_called_once_with(topic=TEST_TOPIC)

    def _mock_factspace(self):
        self.app.config['FACTSPACE'] = Mock()
        return self.app.config['FACTSPACE']

    def _mock_pubsub(self):
        self.app.config['PUBSUB'] = Mock()
        return self.app.config['PUBSUB']

    def _assertResponsePlain(self, response, status_code, mimetype, data):
        self.assertEqual(status_code, response.status_code)
        self.assertEqual('%s; charset=utf-8' % (mimetype,),
                         response.content_type)
        self.assertEqual(data, response.data)

    def _assertResponseJSON(self, response, status_code, data):
        self.assertEqual(status_code, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(data, loads(response.data))
