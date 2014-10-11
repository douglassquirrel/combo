#! /usr/bin/env python

from web.pubsub import PubSub

def archive():
    pass

def run(pubsub):
    pubsub.consume('#', archive)

if __name__ == '__main__':
    # set PS_HOST, PS_PORT, PS_EXCHANGE from env
    ps = PubSub(PS_HOST, PS_PORT, PS_EXCHANGE)
