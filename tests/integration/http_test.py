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

class HTTPTest(TestCase):
    def setUp(self):
        url, port = argv[1], int(argv[2])
        self.conn = HTTPConnection(url, port)

    def test_home(self):
        self.conn.request('GET', '/')
        response = self.conn.getresponse()
        self._check_response(response, 200, 'text/html; charset=utf-8')
       
    def test_publish_valid_fact(self):
        topic = self._new_unique_topic()
        self.conn.request('POST', 'topics/%s/facts' % (topic,),
                          dumps(FACTS[0]))
        response = self.conn.getresponse()
        self._check_response(response, 202, 'text/plain; charset=utf-8')

    def test_publish_and_retrieve(self):
        topic = self._new_unique_topic()
        self.conn.request('POST', 'topics/%s/facts' % (topic,),
                          dumps(FACTS[0]))
        response = self.conn.getresponse()
        self.assertEqual(202, response.status)
        response.read()
        sleep(0.1)
        self.conn.request('GET', 'topics/%s/facts' % (topic,))
        response = self.conn.getresponse()
        self._check_response(response, 200, 'application/json')
        returned_facts = loads(response.read())
        self.assertEqual(1, len(returned_facts))
        raw_fact = self._check_and_extract(returned_facts[0])
        self.assertEqual(FACTS[0], raw_fact)

    def _check_response(self, resp, expected_status, expected_content_type):
        self.assertEqual(expected_status, resp.status)
        actual_content_type = resp.getheader('Content-Type')
        self.assertEqual(expected_content_type, actual_content_type)        

    def _check_and_extract(self, returned_fact):
        self.assertIn('combo_id', returned_fact)
        self.assertIn('combo_timestamp', returned_fact)
        raw_fact = dict(returned_fact)
        del raw_fact['combo_id']
        del raw_fact['combo_timestamp']
        return raw_fact

    def _new_unique_topic(self):
        return uuid1()

if __name__ == '__main__':
    main(argv=['http_test.py'])
