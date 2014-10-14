#! /usr/bin/env python

from httplib import HTTPConnection
from json import dumps
from sys import argv
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

    def _check_response(self, resp, expected_status, expected_content_type):
        self.assertEqual(expected_status, resp.status)
        actual_content_type = resp.getheader('Content-Type')
        self.assertEqual(expected_content_type, actual_content_type)        

    def _new_unique_topic(self):
        return uuid1()

if __name__ == '__main__':
    main(argv=['http_test.py'])
