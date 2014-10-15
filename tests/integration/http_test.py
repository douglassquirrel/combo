#! /usr/bin/env python

from httplib import HTTPConnection
from json import dumps, loads
from sys import argv
from time import sleep
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
        url, port = argv[1], int(argv[2])
        self.conn = HTTPConnection(url, port)

    def test_home(self):
        self._visit(verb='GET', path='/',
                    exp_status=200, exp_content_type=HTML_CONTENT_TYPE)
       
    def test_publish_valid_fact(self):
        topic = self._new_unique_topic()
        self._visit(verb='POST', path='topics/%s/facts' % (topic,),
                    exp_status=202, exp_content_type=TEXT_CONTENT_TYPE,
                    content=dumps(FACTS[0]))

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

    def _visit(self, verb, path, exp_status, exp_content_type, content=None):
        if content is not None:
            self.conn.request(verb, path, content)
        else:
            self.conn.request(verb, path)
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
        self.assertIn('combo_id', returned_fact)
        self.assertIn('combo_timestamp', returned_fact)
        raw_fact = dict(returned_fact)
        del raw_fact['combo_id']
        del raw_fact['combo_timestamp']
        return raw_fact

    def _new_unique_topic(self):
        return str(uuid1())

if __name__ == '__main__':
    main(argv=['http_test.py'])
