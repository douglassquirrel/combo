#! /usr/bin/env python

# Requires the siege load test program
# See http://www.joedog.org/siege-home/

from json import loads
from shutil import copyfileobj
from subprocess import call
from sys import argv, exit
from tempfile import mkstemp
from urllib2 import Request, urlopen

def parse_args(args):
    if len(args) < 2:
        print 'Usage: %s [server]' % (args[0],)
        print 'Example: %s localhost:5000' % (args[0],)
        exit(1)
    return args[1]

def get_sub_ids(server):
    return [get_sub_id(server) for i in range(4)]

def get_sub_id(server):
    request = Request('http://%s/topics/news/subscriptions' % (server,), '')
    return loads(urlopen(request).read())['subscription_id']

def generate_urls_file(server, sub_ids):
    urls_file = mkstemp(suffix='.txt', prefix='combo-siege-urls-')[1]
    with open(urls_file, 'w') as dest, open('urls-template.txt', 'r') as src:
        dest.write('SERVER=%s\n' % (server,))
        for i, sub_id in enumerate(sub_ids):
            dest.write('SUBID%d=%s\n' % (i+1, sub_id))
        copyfileobj(src, dest)
    return urls_file

def run():
    server = parse_args(argv)
    sub_ids = get_sub_ids(server)
    urls_file = generate_urls_file(server, sub_ids)
    call(['siege', '-i', '-f', urls_file])

run()