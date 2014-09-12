#! /usr/bin/env python   

from psycopg2 import connect
from sys import argv

POSTGRES_HOST = argv[1]
POSTGRES_DATABASE = 'micro'
POSTGRES_USER = 'microservices'
POSTGRES_PASSWORD = 'microservices'

conn = connect(host=POSTGRES_HOST, database=POSTGRES_DATABASE,
               user=POSTGRES_USER, password=POSTGRES_PASSWORD)
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM facts;")
    print cursor.fetchall()

except Exception as e:
    print e.message
finally:
    cursor.close()
    conn.close()
