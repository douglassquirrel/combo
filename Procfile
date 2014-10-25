reset: python -m web.reset
web: gunicorn web.combo_server:app --log-file - -w 1 
archivist: python -m web.archivist