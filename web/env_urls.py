from os import environ

local_factspace_url = 'postgres://combo:combo@localhost/combo'
heroku_factspace_url_var = 'DATABASE_URL'
factspace_url = environ.get(heroku_factspace_url_var, local_factspace_url)

local_pubsub_url = 'amqp://guest:guest@localhost:5672'
heroku_pubsub_url_var = 'RABBITMQ_BIGWIG_URL'
pubsub_url = environ.get(heroku_pubsub_url_var, local_pubsub_url)
