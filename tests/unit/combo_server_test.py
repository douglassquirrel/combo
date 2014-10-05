#! /usr/bin/env python  

from web import combo_server
from unittest import TestCase

class ComboServerTest(TestCase):

    def setUp(self):
        combo_server.app.testing = True
        self.client = combo_server.app.test_client()

    def tearDown(self):
        pass

    def test_root(self):
        response = self.client.get('/')
        self.assertEqual(200, response.status_code, 200)
        self.assertEqual('text/html; charset=utf-8', response.content_type)
        self.assertIn('Welcome', response.data)
