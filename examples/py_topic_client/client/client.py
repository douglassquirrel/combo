from pika import BlockingConnection, ConnectionParameters

from config import config


class TopicClient(object):

    host = config['RABBIT_HOST']
    port = config['RABBIT_PORT']
    exchange = config['EXCHANGE']

    def __init__(self):

        self.conn = BlockingConnection(ConnectionParameters(
            host=self.host, port=self.port))

        self.channel = self.conn.channel()
        self.channel.exchange_declare(
            exchange=self.exchange, type='topic')

    def subscribe_to_topic(self, callback, topic):
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        self.channel.queue_bind(
            exchange=self.exchange, queue=queue_name,
            routing_key=topic)
        self.channel.basic_consume(
            callback, queue=queue_name, no_ack=True)

    def publish_to_topic(self, message, topic):
        self.channel.basic_publish(
            exchange=self.exchange, routing_key=topic, body=message)

    def run(self):
        print "Start something"
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print "Closing"
            self.channel.stop_consuming()
            self.conn.close()
