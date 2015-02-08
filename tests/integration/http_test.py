#! /usr/bin/env python

from datetime import datetime
from httplib import HTTPConnection
from json import dumps, loads
from sys import argv
from threading import Thread
from time import sleep, time as now
from unittest import main, TestCase
from uuid import uuid1

FACTS = [{"headline": "Aliens Land", "body": "They just arriv--AAGH!"},
         {"headline": "Moon Eaten", "body": "It's just gone!"},
         {"headline": "Bananas Banned", "body": "Bad for teeth."}]
HTML_CONTENT_TYPE = 'text/html; charset=utf-8'
TEXT_CONTENT_TYPE = 'text/plain; charset=utf-8'
JSON_CONTENT_TYPE = 'application/json'

class HTTPTest(TestCase):
    def setUp(self):
        self.url, self.port = argv[1], int(argv[2])
        self.conn = HTTPConnection(self.url, self.port)

    def test_home(self):
        self._visit(verb='GET', path='/',
                    exp_status=200, exp_content_type=HTML_CONTENT_TYPE)
       
    def test_publish_valid_fact(self):
        topic = self._new_unique_topic()
        self._visit(verb='POST', path='topics/%s/facts' % (topic,),
                    exp_status=202, exp_content_type=TEXT_CONTENT_TYPE,
                    content=dumps(FACTS[0]))

    def test_publish_invalid_fact(self):
        topic = self._new_unique_topic()
        self._visit(verb='POST', path='topics/%s/facts' % (topic,),
                    exp_status=400, exp_content_type=TEXT_CONTENT_TYPE,
                    content='invalid fact')

    def test_retrieve_fact(self):
        topic = self._new_unique_topic()
        self._publish_fact(topic, FACTS[0])
        sleep(0.1)
        response = self._visit(verb='GET', path='topics/%s/facts' % (topic,),
                               exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        returned_facts = loads(response.read())
        self.assertEqual(1, len(returned_facts))
        raw_fact = self._check_and_extract(returned_facts[0])
        self.assertEqual(FACTS[0], raw_fact)

    def test_retrieve_facts_after_id(self):
        topic = self._new_unique_topic()
        map(lambda f: self._publish_fact(topic, f), FACTS)
        sleep(0.1)
        response = self._visit(verb='GET', path='topics/%s/facts' % (topic,),
                               exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        all_ids = self._extract_fact_ids(response)
        first_id = min(all_ids)

        path = 'topics/%s/facts?after_id=%d' % (topic, first_id)
        response = self._visit(verb='GET', path=path, exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        returned_ids = self._extract_fact_ids(response)
        self.assertEqual(all_ids[1:], returned_ids)
        
    def test_subscribe_and_retrieve(self):
        topic = self._new_unique_topic()
        response = self._visit(verb='POST',
                               path='topics/%s/subscriptions' % (topic,),
                               exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        sub_id = loads(response.read())['subscription_id']

        self._publish_fact(topic, FACTS[0])
        path = '/topics/%s/subscriptions/%s/next' % (topic, sub_id)
        response = self._visit(verb='GET', path=path, exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        self.assertEqual(FACTS[0], loads(response.read()))
        self._assertHeadersPreventCaching(dict(response.getheaders()))
        
    def test_subscribe_and_timeout(self):
        topic = self._new_unique_topic()
        response = self._visit(verb='POST',
                               path='topics/%s/subscriptions' % (topic,),
                               exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        sub_id = loads(response.read())['subscription_id']

        path = '/topics/%s/subscriptions/%s/next' % (topic, sub_id)
        start = now()
        response = self._visit(verb='GET', path=path, 
                               headers={'Patience': '1'},
                               exp_status=204,
                               exp_content_type=TEXT_CONTENT_TYPE)
        response.read()
        duration = now() - start
        self.assertTrue(duration < 2,
                        'Should wait only as specified in Patience header')

    def test_nonexistent_subscription_id(self):
        topic = self._new_unique_topic()
        path = '/topics/%s/subscriptions/nonexistent/next' % (topic,)
        response = self._visit(verb='GET', path=path, 
                               exp_status=404,
                               exp_content_type=TEXT_CONTENT_TYPE)
        response.read()

    def test_retrieve_topics(self):
        topic1 = self._new_unique_topic()
        self._publish_fact(topic1, FACTS[0])
        topic2 = self._new_unique_topic()
        self._publish_fact(topic2, FACTS[1])
        sleep(0.1)
        response = self._visit(verb='GET', path='topics', exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        topics = map(lambda x: x['topic_name'], loads(response.read()))
        self.assertIn(topic1, topics)
        self.assertIn(topic2, topics)

    def test_simultaneous_requests(self):
        topic = self._new_unique_topic()
        response = self._visit(verb='POST',
                               path='topics/%s/subscriptions' % (topic,),
                               exp_status=200,
                               exp_content_type=JSON_CONTENT_TYPE)
        sub_id = loads(response.read())['subscription_id']

        thread = Thread(target=self._wait_on_sub, args=(topic, sub_id))
        thread.daemon = True
        thread.start()
        sleep(0.5)
        conn = HTTPConnection(self.url, self.port)
        conn.request('GET', 'topics', '', {})
        conn.getresponse().read()
        self.assertTrue(thread.is_alive(),
                        msg='Should run two queries at once')
        thread.join()

    def _wait_on_sub(self, topic, sub_id):
        conn = HTTPConnection(self.url, self.port)
        path = '/topics/%s/subscriptions/%s/next' % (topic, sub_id)
        conn.request('GET', path, '', {'Patience': '2'})
        conn.getresponse().read()

    def _extract_fact_ids(self, response):
        return map(lambda f: f['combo_id'], loads(response.read()))

    def _visit(self, verb, path,
               exp_status, exp_content_type,
               headers={}, content=''):
        self.conn.request(verb, path, content, headers)
        response = self.conn.getresponse()
        self.assertEqual(exp_status, response.status)
        actual_content_type = response.getheader('Content-Type')
        self.assertEqual(exp_content_type, actual_content_type)        
        return response

    def _publish_fact(self, topic, fact):
        response = self._visit(verb='POST',
                               path='topics/%s/facts' % (topic,),
                               exp_status=202,
                               exp_content_type=TEXT_CONTENT_TYPE,
                               content=dumps(fact))
        response.read()

    def _check_and_extract(self, returned_fact):
        raw_fact = dict(returned_fact)
        for key in ['combo_id', 'combo_timestamp', 'combo_topic']:
            self.assertIn(key, returned_fact)
            del raw_fact[key]
        return raw_fact

    def _new_unique_topic(self):
        return str(uuid1())

    def _assertHeadersPreventCaching(self, headers):
        self.assertEqual('no-cache, must-revalidate',
                         headers['cache-control'])
        expires = datetime.strptime(headers['expires'],
                                    '%a, %d %b %Y %H:%M:%S GMT')
        self._assertIsInPast(expires, 'Should expire in the past')

    def _assertIsInPast(self, date, msg):
        self.assertTrue(date < datetime.now(), msg)

if __name__ == '__main__':
    main(argv=['http_test.py'])
