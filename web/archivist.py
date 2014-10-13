#! /usr/bin/env python

from factspace import Factspace
from pubsub import PubSub

def run(factspace, pubsub):
    pubsub.consume('#', lambda t,f: factspace.add_fact(t, f))

if __name__ == '__main__':
    # set FS_URL, PS_URL from env
    fs = Factspace(FS_URL)
    ps = PubSub(PS_URL)
    run(factspace=fs, pubsub=ps)
