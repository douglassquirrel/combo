#! /usr/bin/env python

from os import chdir
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import TCPServer

PORT = 8000

chdir('html')

httpd = TCPServer(("", PORT), SimpleHTTPRequestHandler)
httpd.serve_forever()

