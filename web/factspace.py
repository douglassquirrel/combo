from json import dumps
from sql import connect, run_sql

CHECK_FACTS_TABLE_SQL = '''
SELECT COUNT(1) FROM information_schema.tables WHERE table_name = 'facts';
'''
GET_TOPICS_SQL = 'SELECT DISTINCT topic FROM facts'
GET_LAST_N_FACTS_SQL = '''
    SELECT id, ts, topic, content
    FROM (SELECT id, ROUND(EXTRACT(epoch FROM ts))::int AS ts, topic, content
          FROM facts WHERE topic LIKE %%s ORDER BY id DESC LIMIT %s) t
    ORDER BY id ASC
'''
GET_AFTER_ID_FACTS_SQL = '''
    SELECT id, ROUND(EXTRACT(epoch FROM ts))::int AS ts, topic, content
          FROM facts WHERE topic LIKE %s AND id > %s ORDER BY id ASC
'''
INSERT_FACT_SQL = '''
    INSERT INTO facts (topic, ts, content) VALUES (%s, now(), %s);
'''

class Factspace:
    def __init__(self, url):
        self.url = url
        conn = connect(self.url)
        result = run_sql(conn, CHECK_FACTS_TABLE_SQL, results=True)[0][0]
        if result != 1:
            raise MissingTableError('Facts table not present.')
        conn.close()

    def list_topics(self):
        conn = connect(self.url)
        result = run_sql(conn, GET_TOPICS_SQL, results=True)
        ret_val = map(lambda x: x[0], result)
        conn.close()
        return ret_val

    def last_n(self, topic, number):
        conn = connect(self.url)
        topic = self._translate_wildcards(topic)
        result = run_sql(conn, GET_LAST_N_FACTS_SQL % (number,),
                         results=True, parameters=[topic])
        ret_val = map(self._format_fact, result)
        conn.close()
        return ret_val

    def after_id(self, topic, id):
        conn = connect(self.url)
        topic = self._translate_wildcards(topic)
        result = run_sql(conn, GET_AFTER_ID_FACTS_SQL,
                         results=True, parameters=[topic, id])
        ret_val = map(self._format_fact, result)
        conn.close()
        return ret_val

    def add_fact(self, topic, fact):
        conn = connect(self.url)
        run_sql(conn, INSERT_FACT_SQL, results=False,
                parameters=[topic, dumps(fact)])
        conn.close()
        return

    def _format_fact(self, returned_fact):
        fact = dict(returned_fact[3])
        fact['combo_id'] = returned_fact[0]
        fact['combo_timestamp'] = returned_fact[1]
        fact['combo_topic'] = returned_fact[2]
        return fact

    def _translate_wildcards(self, s):
        return s.replace('#', '%')

class MissingTableError(Exception):
    pass
