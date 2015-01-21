#! /usr/bin/env python

from json import loads
from random import randint
from shutil import copyfileobj
from subprocess import Popen
from sys import argv, exit
from tempfile import mkstemp
from time import sleep
from urllib2 import Request, urlopen

print 'Starting siege driver'
print 'Requires the siege load test program'
print 'See http://www.joedog.org/siege-home/'

def parse_args(args):
    if len(args) < 2:
        print 'Usage: %s [server]' % (args[0],)
        print 'Example: %s localhost:5000' % (args[0],)
        exit(1)
    return args[1]

def get_sub_ids(server):
    return [get_sub_id(server, 'news') for i in range(4)]

def get_sub_id(server, topic):
    url = 'http://%s/topics/%s/subscriptions' % (server, topic)
    return loads(urlopen(Request(url, '')).read())['subscription_id']

def generate_urls_file(server, sub_ids):
    urls_file = mkstemp(suffix='.txt', prefix='combo-siege-urls-')[1]
    with open(urls_file, 'w') as dest, open('urls-template.txt', 'r') as src:
        dest.write('SERVER=%s\n' % (server,))
        for i, sub_id in enumerate(sub_ids):
            dest.write('SUBID%d=%s\n' % (i+1, sub_id))
        copyfileobj(src, dest)
    return urls_file

def start_siege(urls_file):
    print 'Siege starting - Ctrl-C to stop it'
    return Popen(['siege', '-i', '-f', urls_file])

def test_during_siege(server):
    error_count = 0
    try:
        while True:
            print 'Test during siege'
            topic = str(randint(1000, 9999))
            sub_id = get_sub_id(server, topic)
            post_url = 'http://%s/topics/%s/facts' % (server, topic)
            post_data = '{"test": "Under siege!", "topic": %s}' % (topic,)
            response = urlopen(Request(post_url, post_data))
            print 'Topic %s, sub_id %s, post response %d' \
                % (topic, sub_id, response.getcode())
            sleep(1)
            
            facts_url = 'http://%s/topics/%s/facts' % (server, topic)
            response = urlopen(Request(facts_url))
            returned_facts = loads(response.read())
            num_facts = len(returned_facts)
            print 'Fetch resp code %s, facts returned: %d' \
                % (response.getcode(), len(returned_facts))
            if num_facts != 1:
                print '\033[91m' + 'ERROR!!! Wrong number of facts' + '\033[0m'
                error_count += 1
            sleep(1)
    except KeyboardInterrupt:
        print 'Wrong number of facts returned: %d times' % (error_count,)
        raise
                
def run():
    server = parse_args(argv)
    sub_ids = get_sub_ids(server)
    urls_file = generate_urls_file(server, sub_ids)
    start_siege(urls_file)
    test_during_siege(server)
    
run()
