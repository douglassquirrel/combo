from psycopg2 import connect
from sql import run_sql

CREATE_FACTS_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS facts (id serial primary key,
                                      topic character varying(255),
                                      ts timestamp without time zone,
                                      content json);
'''
GET_LAST_N_FACTS_SQL = '''
    SELECT id, ts, content
    FROM (SELECT id, ROUND(EXTRACT(epoch FROM ts))::int AS ts, content
          FROM facts WHERE topic = %%s ORDER BY id DESC LIMIT %s) t
    ORDER BY id ASC
'''
GET_AFTER_ID_FACTS_SQL = '''
    SELECT id, ROUND(EXTRACT(epoch FROM ts))::int AS ts, content
          FROM facts WHERE topic = %s AND id > %s ORDER BY id ASC
'''

class Factspace:
    def __init__(self, host, user, password, database):
        self.conn = connect(host=host, user=user, password=password,
                            database=database)
        run_sql(self.conn, CREATE_FACTS_TABLE_SQL, results=False)

    def last_n(self, topic, number):
        result = run_sql(self.conn, GET_LAST_N_FACTS_SQL % (number,),
                         results=True, parameters=[topic])
        return map(self._format_fact, result)

    def after_id(self, topic, id):
        result = run_sql(self.conn, GET_AFTER_ID_FACTS_SQL,
                         results=True, parameters=[topic, id])
        return map(self._format_fact, result)

    def _format_fact(self, returned_fact):
        fact = dict(returned_fact[2])
        fact['combo_id'] = returned_fact[0]
        fact['combo_timestamp'] = returned_fact[1]
        return fact
