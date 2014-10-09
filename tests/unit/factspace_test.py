#! /usr/bin/env python

from mock import Mock
from psycopg2 import connect
from sys import exit
from traceback import print_exc
from unittest import TestCase
from web.factspace import Factspace
from web.sql import run_sql

HOST = 'localhost'
USER = 'combo'
PASSWORD = 'combo'
DATABASE = 'combo'

DROP_TABLE_SQL = 'DROP TABLE IF EXISTS facts'

CHECK_TABLE_SQL = '''
SELECT COUNT(1) FROM information_schema.tables WHERE table_name = 'facts';
'''

class FactspaceTest(TestCase):
    def setUp(self):
        try:
            self.conn = connect(host=HOST, user=USER, password=PASSWORD,
                                database=DATABASE)
            run_sql(self.conn, DROP_TABLE_SQL, results=False)
        except Exception as e:
            print 'Exception: %s' % e.message
            print_exc()
            print ('Expect Postgres on %s with user %s, password %s, ' \
                + 'database %s') % (HOST, USER, PASSWORD, DATABASE)
            exit(1)

    def tearDown(self):
        self.conn.close()

    def test_create_table_on_construction(self):
        self.assertFalse(self._facts_table_exists(),
                         'Should be no facts table on startup')
        factspace = Factspace(HOST, USER, PASSWORD, DATABASE)
        self.assertTrue(self._facts_table_exists(),
                        'facts table should be created on construction')

    def _facts_table_exists(self):
        return run_sql(self.conn, CHECK_TABLE_SQL)[0][0] > 0
