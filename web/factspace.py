from psycopg2 import connect
from sql import run_sql

CREATE_FACTS_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS facts (id serial primary key,
                                      topic character varying(255),
                                      ts timestamp without time zone,
                                      content json);
'''

class Factspace:
    def __init__(self, host, user, password, database):
        self.conn = connect(host=host, user=user, password=password,
                            database=database)
        run_sql(self.conn, CREATE_FACTS_TABLE_SQL)
