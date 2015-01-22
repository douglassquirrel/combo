reset: python -m web.reset
web: gunicorn web.combo_server:app --log-file - -w 4 -k sync
archivist: python -m web.archivist