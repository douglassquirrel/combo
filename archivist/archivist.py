#! /usr/bin/env python

from web.factspace import Factspace
from web.pubsub import PubSub

def run(factspace, pubsub):
    pubsub.consume('#', lambda t,f: factspace.add_fact(t, f))

if __name__ == '__main__':
    # set FS_HOST, FS_USER, FS_PASSWORD, FS_DATABASE from env
    fs = Factspace(FS_HOST, FS_USER, FS_PASSWORD, FS_DATABASE)
    # set PS_HOST, PS_PORT, PS_EXCHANGE from env
    ps = PubSub(PS_HOST, PS_PORT, PS_EXCHANGE)
    run(factspace=fs, pubsub=ps)
