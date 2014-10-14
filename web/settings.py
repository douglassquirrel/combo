from os.path import dirname, join as pathjoin
from web.factspace import Factspace
from web.pubsub import PubSub

with open(pathjoin(dirname(__file__), 'home.html')) as f:
    HOME_HTML = f.read()
CHARSET = 'utf-8'
FACTSPACE = Factspace('postgres://combo:combo@localhost/combo')
PUBSUB = PubSub('amqp://guest:guest@localhost:5672', 'combo')
