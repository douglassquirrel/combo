reset: python -m web.reset
web: gunicorn web.combo_server:app --log-file - -w 4 -k eventlets 
archivist: python -m web.archivist