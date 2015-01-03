#! /usr/bin/env python

# Requires the siege load test program
# See http://www.joedog.org/siege-home/

from shutil import copyfileobj
from subprocess import call
from sys import argv, exit
from tempfile import mkstemp

if len(argv) < 2:
    print 'Usage: %s [server]' % (argv[0],)
    print 'Example: %s localhost:5000' % (argv[0],)
    exit(1)
server = argv[1]

urls_file = mkstemp(suffix='.txt', prefix='combo-siege-urls-')[1]
with open(urls_file, 'w') as dest, open('urls-template.txt', 'r') as src:
    dest.write('SERVER=%s\n' % (server,))
    copyfileobj(src, dest)

call(['siege', '-i', '-f', urls_file])
