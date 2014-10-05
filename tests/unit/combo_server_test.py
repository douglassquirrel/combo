#! /usr/bin/env python  

from web import combo_server
from unittest import TestCase

TEST_HOME_PAGE = 'test home page'

class ComboServerTest(TestCase):
    def setUp(self):
        self.app = combo_server.app
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        pass

    def test_home(self):
        self.app.config['HOME_HTML'] = TEST_HOME_PAGE
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response.content_type)
        self.assertEqual(TEST_HOME_PAGE, response.data)
