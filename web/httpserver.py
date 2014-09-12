from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from pika import BlockingConnection, ConnectionParameters

WEB_HOST_NAME = 'localhost' # 
PORT_NUMBER = 8080 
RABBIT_HOST = '54.72.124.130'
RABBIT_PORT = 5672

class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Publish the given fact."""
        content_len = int(self.headers.getheader('content-length', 0))
        fact = self.rfile.read(content_len)
        topic = self.path.split('/')[2]

        connection = BlockingConnection(ConnectionParameters(host=RABBIT_HOST,
                                                             port=RABBIT_PORT))
        channel = connection.channel()
        channel.basic_publish(exchange='',
                              routing_key=topic,
                              body=fact)
        connection.close()

        self.send_response(202)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

if __name__ == '__main__':
    httpd = HTTPServer((WEB_HOST_NAME, PORT_NUMBER), MyHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
