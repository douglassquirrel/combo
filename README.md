alex2
=====
An experimental microservices system - a project of the Microservices Hackathon group in London.

To run tests, execute `nosetests` in the home directory.

To run under gunicorn:

    gunicorn web.combo_server:app --log-file - -w 4 -k gevent