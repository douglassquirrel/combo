#! /usr/bin/env python

from datetime import datetime
from json import loads, dumps
from mock import Mock
from unittest import TestCase
from web.combo_server import app
from web.pubsub import PubSubError
from sys import stderr

TEST_HOME_PAGE = '''
    root:         %ROOT_URL%
    topics:       %TOPICS_URL%
    facts:        %FACTS_URL%
    subscription: %SUBSCRIPTION_URL%
    from_sub:     %FROM_SUB_URL%
'''
TEST_HOME_PAGE_WITH_SUBS = '''
    root:         http://foo.com/
    topics:       http://foo.com/topics
    facts:        http://foo.com/topics/TOPIC/facts
    subscription: http://foo.com/topics/TOPIC/subscriptions
    from_sub:     http://foo.com/topics/TOPIC/subscriptions/SUB_ID/next
'''
TEST_TOPICS = ['headlines', 'story.creation', 'story.update']
FACTS_URL_PATTERN = 'http://foo.com/topics/%s/facts'
SUB_URL_PATTERN = 'http://foo.com/topics/%s/subscriptions'
def make_topic_response_element(topic):
    return {'topic_name': topic,
            'facts_url': FACTS_URL_PATTERN % (topic,),
            'subscription_url': SUB_URL_PATTERN % (topic,)}
TEST_TOPICS_RESPONSE = map(make_topic_response_element, TEST_TOPICS)
TEST_TOPIC = 'story.creation'
TEST_SUB_ID = '%s.subscription' % (TEST_TOPIC,)
RETR_URL_PATTERN = 'http://foo.com/topics/%s/subscriptions/%s/next'
TEST_SUB_RESPONSE = {'retrieval_url': RETR_URL_PATTERN % (TEST_TOPIC,
                                                          TEST_SUB_ID),
                     'subscription_id': TEST_SUB_ID}
TEST_FACTS = [{"headline": "Aliens Land", "body": "They just arriv--AAGH!"},
              {"headline": "Moon Eaten", "body": "It's just gone!"},
              {"headline": "Bananas Banned", "body": "Bad for teeth."}]
TEST_ID = 123

class ComboServerTest(TestCase):
    def setUp(self):
        self.app = app
        self.app.testing = True
        self.app.config['SERVER_NAME'] = 'foo.com'
        self.app.config['ERROR_OUT'] = stderr
        self.client = self.app.test_client()

    def test_home(self):
        self.app.config['HOME_HTML'] = TEST_HOME_PAGE
        self._assertResponsePlain('Should respond to / with correct subs',
                                  self.client.get('/'),
                                  200, 'text/html', TEST_HOME_PAGE_WITH_SUBS)

    def test_topics(self):
        factspace = self._mock_factspace()
        factspace.list_topics = Mock(return_value=TEST_TOPICS)
        self._assertResponseJSON('Should list topics', 
                                 self.client.get('/topics'),
                                 200, TEST_TOPICS_RESPONSE)
        factspace.list_topics.assert_called_with()

    def test_publish(self):
        pubsub = self._mock_pubsub()
        response = self.client.post('/topics/%s/facts' % (TEST_TOPIC,),
                                    data=dumps(TEST_FACTS[0]))
        self._assertResponsePlain('Should publish fact',
                                  response, 202, 'text/plain', '')
        pubsub.publish.assert_called_once_with(topic=TEST_TOPIC,
                                               fact=TEST_FACTS[0])

    def test_publish_invalid_facts(self):
        response = self.client.post('/topics/%s/facts' % (TEST_TOPIC,),
                                    data='invalid_fact')
        self._assertResponsePlain('Should reject non-JSON fact',
                                  response, 400, 'text/plain', '')
        response = self.client.post('/topics/%s/facts' % (TEST_TOPIC,),
                                    data='["not a dict"]')
        self._assertResponsePlain('Should reject non-dictionary',
                                  response, 400, 'text/plain', '')
        response = self.client.post('/topics/%s/facts' % (TEST_TOPIC,),
                                    data='')
        self._assertResponsePlain('Should reject empty fact',
                                  response, 400, 'text/plain', '')

    def test_get_last_10_facts(self):
        factspace = self._mock_factspace()
        self._mock_pubsub()
        factspace.last_n = Mock(return_value=TEST_FACTS)
        response = self.client.get('/topics/%s/facts' % (TEST_TOPIC,))
        self._assertResponseJSON('Should fetch last 10 facts',
                                 response, 200, TEST_FACTS)
        factspace.last_n.assert_called_with(TEST_TOPIC, 10)

    def test_get_facts_after_id(self):
        factspace = self._mock_factspace()
        self._mock_pubsub()
        factspace.after_id = Mock(return_value=TEST_FACTS)
        url = '/topics/%s/facts?after_id=%d' % (TEST_TOPIC, TEST_ID)
        self._assertResponseJSON('Should get facts after id',
                                 self.client.get(url), 200, TEST_FACTS)
        factspace.after_id.assert_called_with(TEST_TOPIC, TEST_ID)

    def test_get_facts_with_bad_after_id(self):
        url = '/topics/%s/facts?after_id=3.14' % (TEST_TOPIC,)
        self._assertResponsePlain('Should reject non-integer after_id',
                                 self.client.get(url), 400, 'text/plain', '')
        url = '/topics/%s/facts?after_id=invalid' % (TEST_TOPIC,)
        self._assertResponsePlain('Should reject non-integer after_id',
                                 self.client.get(url), 400, 'text/plain', '')
        url = '/topics/%s/facts?after_id=' % (TEST_TOPIC,)
        self._assertResponsePlain('Should reject empty after_id',
                                 self.client.get(url), 400, 'text/plain', '')

    def test_get_fact_from_subscription(self):
        self._mock_factspace()
        pubsub = self._mock_pubsub()
        pubsub.fetch_from_sub = Mock(return_value=TEST_FACTS[0])
        url = '/topics/%s/subscriptions/%s/next' % (TEST_TOPIC, TEST_SUB_ID)
        self._assertResponseJSON('Should get latest fact',
                                 self.client.get(url), 200, TEST_FACTS[0])
        pubsub.fetch_from_sub.assert_called_with(TEST_TOPIC, TEST_SUB_ID, 10)

    def test_get_fact_from_nonexistent_subscription(self):
        self.app.config['ERROR_OUT'] = Devnull()
        self._mock_factspace()
        pubsub = self._mock_pubsub()
        pubsub.fetch_from_sub = Mock(side_effect=PubSubError)
        url = '/topics/%s/subscriptions/invalid/next' % (TEST_TOPIC,)
        self._assertResponsePlain('Should give error for invalid sub id ',
                                 self.client.get(url), 404, 'text/plain', '')

    def test_get_fact_from_subscription_with_default_timeout(self):
        self._mock_factspace()
        pubsub = self._mock_pubsub()
        pubsub.fetch_from_sub = Mock(return_value=None)
        url = '/topics/%s/subscriptions/%s/next' % (TEST_TOPIC, TEST_SUB_ID)
        self._assertResponsePlain('Should time out and return 204',
                                  self.client.get(url), 204, 'text/plain', '')
        pubsub.fetch_from_sub.assert_called_with(TEST_TOPIC, TEST_SUB_ID, 10)

    def test_get_fact_from_subscription_with_specified_timeout(self):
        self._mock_factspace()
        pubsub = self._mock_pubsub()
        pubsub.fetch_from_sub = Mock(return_value=None)
        url = '/topics/%s/subscriptions/%s/next' % (TEST_TOPIC, TEST_SUB_ID)
        response = self.client.get(url, headers={'Patience': '5'})
        self._assertResponsePlain('Should time out and return 204',
                                  response, 204, 'text/plain', '')
        pubsub.fetch_from_sub.assert_called_with(TEST_TOPIC, TEST_SUB_ID, 5)

    def test_get_fact_from_sub_bad_header(self):
        url = '/topics/%s/subscriptions/%s/next' % (TEST_TOPIC, TEST_SUB_ID)
        response = self.client.get(url, headers={'Patience': 'foo'})
        self._assertResponsePlain('Should reject non-integer patience value',
                                  response, 400, 'text/plain', '')
        response = self.client.get(url, headers={'Patience': '3.14'})
        self._assertResponsePlain('Should reject non-integer patience value',
                                  response, 400, 'text/plain', '')
        response = self.client.get(url, headers={'Patience': ''})
        self._assertResponsePlain('Should reject empty patience value',
                                  response, 400, 'text/plain', '')
        response = self.client.get(url, headers={'Patience': '-1'})
        self._assertResponsePlain('Should reject negative patience value',
                                  response, 400, 'text/plain', '')
        response = self.client.get(url, headers={'Patience': '0'})
        self._assertResponsePlain('Should reject patience value of zero',
                                  response, 400, 'text/plain', '')

    def test_subscription(self):
        pubsub = self._mock_pubsub()
        pubsub.subscribe = Mock(return_value='%s.subscription' % (TEST_TOPIC,))
        response = self.client.post('/topics/%s/subscriptions' % (TEST_TOPIC,))
        self._assertResponseJSON('Should return subscription data',
                                 response, 200, TEST_SUB_RESPONSE)
        pubsub.subscribe.assert_called_once_with(topic=TEST_TOPIC)

    def _mock_factspace(self):
        self.app.config['FACTSPACE'] = Mock()
        return self.app.config['FACTSPACE']

    def _mock_pubsub(self):
        self.app.config['PUBSUB'] = Mock()
        return self.app.config['PUBSUB']

    def _assertResponsePlain(self, msg, response, status_code, mimetype, data):
        self._assertResponse(msg, response, status_code, 
                             '%s; charset=utf-8' % (mimetype,), data)

    def _assertResponseJSON(self, msg, response, status_code, data):
        self._assertResponse(msg, response, status_code, 'application/json',
                             data, loads)

    def _assertResponse(self, msg, response, status_code, content_type,
                        data, transformer=lambda x: x):
        self.assertEqual(status_code, response.status_code, msg=msg)        
        self.assertEqual(content_type, response.content_type, msg=msg)
        self.assertEqual(data, transformer(response.data), msg=msg)
        self.assertEqual('no-cache, must-revalidate',
                         response.headers['Cache-control'])
        expires = datetime.strptime(response.headers['Expires'],
                                    '%a, %d %b %Y %H:%M:%S GMT')
        self._assertIsInPast(expires, 'Should expire in the past')

    def _assertIsInPast(self, date, msg):
        self.assertTrue(date < datetime.now(), msg)

class Devnull(object):
    def write(self, _):
        pass
