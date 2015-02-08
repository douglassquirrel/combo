#! /usr/bin/env python

def run(factspace, pubsub):
    pubsub.consume('#', lambda t,f: factspace.add_fact(t, f))

if __name__ == '__main__':
    from settings import FACTSPACE, PUBSUB
    run(factspace=FACTSPACE, pubsub=PUBSUB)
