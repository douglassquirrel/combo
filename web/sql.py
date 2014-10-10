from traceback import print_exc

def run_sql(conn, sql, results, parameters=None):
    cursor = conn.cursor()
    try:
        if parameters is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, parameters)
        conn.commit()
        if results is True:
            return cursor.fetchall()
        else:
            return None
    except Exception as e:
        print 'Exception: %s' % e.message
        print_exc()
        return []
    finally:
        cursor.close()
