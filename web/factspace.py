from json import dumps
from sql import connect, run_sql

CHECK_FACTS_TABLE_SQL = '''
SELECT COUNT(1) FROM information_schema.tables WHERE table_name = 'facts';
'''
GET_TOPICS_SQL = 'SELECT DISTINCT topic FROM facts'
GET_LAST_N_FACTS_SQL = '''
    SELECT id, ts, topic, content
    FROM (SELECT id, ROUND(EXTRACT(epoch FROM ts))::int AS ts, topic, content
          FROM facts WHERE topic = %%s ORDER BY id DESC LIMIT %s) t
    ORDER BY id ASC
'''
GET_AFTER_ID_FACTS_SQL = '''
    SELECT id, ROUND(EXTRACT(epoch FROM ts))::int AS ts, topic, content
          FROM facts WHERE topic = %s AND id > %s ORDER BY id ASC
'''
INSERT_FACT_SQL = '''
    INSERT INTO facts (topic, ts, content) VALUES (%s, now(), %s);
'''

class Factspace:
    def __init__(self, url):
        self.conn = connect(url)
        result = run_sql(self.conn, CHECK_FACTS_TABLE_SQL, results=True)[0][0]
        if result != 1:
            raise MissingTableError('Facts table not present.')

    def list_topics(self):
        result = run_sql(self.conn, GET_TOPICS_SQL, results=True)
        return map(lambda x: x[0], result)

    def last_n(self, topic, number):
        result = run_sql(self.conn, GET_LAST_N_FACTS_SQL % (number,),
                         results=True, parameters=[topic])
        return map(self._format_fact, result)

    def after_id(self, topic, id):
        result = run_sql(self.conn, GET_AFTER_ID_FACTS_SQL,
                         results=True, parameters=[topic, id])
        return map(self._format_fact, result)

    def add_fact(self, topic, fact):
        run_sql(self.conn, INSERT_FACT_SQL, results=False,
                parameters=[topic, dumps(fact)])

    def _format_fact(self, returned_fact):
        fact = dict(returned_fact[3])
        fact['combo_id'] = returned_fact[0]
        fact['combo_timestamp'] = returned_fact[1]
        fact['combo_topic'] = returned_fact[2]
        return fact

class MissingTableError(Exception):
    pass
