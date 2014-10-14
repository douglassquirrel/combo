#! /usr/bin/env python

from httplib import HTTPConnection
from sys import argv
from unittest import main, TestCase

class HTTPTest(TestCase):
    def setUp(self):
        url, port = argv[1], int(argv[2])
        print 'Server expected on host %s, port %d' % (url, port)
        self.conn = HTTPConnection(url, port)

    def test_home(self):
        self.conn.request('GET', '/')
        response = self.conn.getresponse()
        self.assertEqual(200, response.status)
        content_type = response.getheader('Content-Type')
        self.assertEqual('text/html; charset=utf-8', content_type)
       
    

if __name__ == '__main__':
    main(argv=['http_test.py'])
