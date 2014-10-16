#! /usr/bin/env python

from web.reset import recreate_facts_table
from json import dumps
from mock import Mock
from sys import exit
from traceback import print_exc
from unittest import TestCase
from web.sql import connect, run_sql
from web.factspace import Factspace, MissingTableError

PG_URL = 'postgres://combo:combo@localhost/combo'

TOPIC = 'news'
FACTS = [{"headline": "Aliens Land", "body": "They just arriv--AAGH!"},
         {"headline": "Moon Eaten", "body": "It's just gone!"},
         {"headline": "Bananas Banned", "body": "Bad for teeth."}]

DROP_TABLE_SQL = 'DROP TABLE IF EXISTS facts'

CHECK_TABLE_SQL = '''
SELECT COUNT(1) FROM information_schema.tables WHERE table_name = 'facts';
'''

INSERT_FACT_SQL = '''
INSERT INTO facts (topic, ts, content) VALUES (%s, now(), %s);
'''

GET_FACTS_SQL = 'SELECT id, ts, topic, content FROM facts'

class FactspaceTest(TestCase):
    def setUp(self):
        try:
            self.conn = connect(PG_URL)
            recreate_facts_table(self.conn)
        except Exception as e:
            print 'Exception: %s' % e.message
            print_exc()
            print ('Expect Postgres on %s ' % (PG_URL,))
            exit(1)

    def tearDown(self):
        self.conn.close()

    def test_fail_on_construction_if_no_table(self):
        run_sql(self.conn, DROP_TABLE_SQL, results=False)
        self.assertFalse(self._facts_table_exists(),
                         'Should be no facts table after drop')
        try:
            factspace = Factspace(PG_URL)
            self.fail('Should fail when no facts table')
        except MissingTableError:
            pass #expected

    def test_last_n(self):
        factspace = Factspace(PG_URL)
        self._add_facts(TOPIC, FACTS)
        raw_facts = map(self._check_and_extract, factspace.last_n(TOPIC, 2))
        self.assertEqual(FACTS[-2:], raw_facts)

    def test_after_id(self):
        factspace = Factspace(PG_URL)
        self._add_facts(TOPIC, FACTS)
        raw_facts = map(self._check_and_extract, factspace.after_id(TOPIC, 1))
        self.assertEqual(FACTS[-2:], raw_facts)

    def test_wildcard_topic(self):
        factspace = Factspace(PG_URL)
        self._add_facts('wild.card', FACTS[0:1])
        self._add_facts('wild.thing', FACTS[1:])
        raw_facts = map(self._check_and_extract,
                        factspace.last_n('wild.#', 10))
        self.assertEqual(FACTS, raw_facts)
        raw_facts = map(self._check_and_extract,
                        factspace.after_id('wild.#', 0))
        self.assertEqual(FACTS, raw_facts)

    def test_list_topics(self):
        factspace = Factspace(PG_URL)
        self._add_facts('news', FACTS)
        self._add_facts('views',
                        {"headline": "Outlaw Black", "body": "Too dark"})
        self.assertItemsEqual(['news', 'views'], factspace.list_topics())

    def test_add_fact(self):
        factspace = Factspace(PG_URL)
        factspace.add_fact('news', FACTS[0])
        results = run_sql(self.conn, GET_FACTS_SQL, results=True)
        self.assertEqual(1, len(results))
        self.assertEqual(4, len(results[0]))
        id, ts, topic, fact = results[0]
        self.assertEqual('news', topic)
        self.assertEqual(FACTS[0], fact)

    def _check_and_extract(self, returned_fact):
        raw_fact = dict(returned_fact)
        for key in ['combo_id', 'combo_timestamp', 'combo_topic']:
            self.assertIn(key, returned_fact)
            del raw_fact[key]
        return raw_fact

    def _facts_table_exists(self):
        return run_sql(self.conn, CHECK_TABLE_SQL, results=True)[0][0] > 0

    def _add_facts(self, topic, facts):
        for fact in facts:
            run_sql(self.conn, INSERT_FACT_SQL, results=False,
                    parameters=[topic, dumps(fact)])
