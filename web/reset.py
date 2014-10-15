from env_urls import factspace_url
from sql import connect, run_sql

DROP_FACTS_TABLE_SQL = '''
    DROP TABLE IF EXISTS facts
'''
CREATE_FACTS_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS facts (id serial primary key,
                                      topic character varying(255),
                                      ts timestamp without time zone,
                                      content json);
'''

def recreate_facts_table(conn):
    run_sql(conn, DROP_FACTS_TABLE_SQL, results=False)
    run_sql(conn, CREATE_FACTS_TABLE_SQL, results=False)

if __name__ == '__main__':
    recreate_facts_table(connect(factspace_url))

