from pika import BlockingConnection, ConnectionParameters
from web.spinner import spin

class PubSub:
    def __init__(self, host, port, exchange):
        self.conn = BlockingConnection(ConnectionParameters(host=host,
                                                            port=port))
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange=exchange, type='topic')
        self.exchange = exchange

    def publish(self, topic, fact):
        self.channel.basic_publish(exchange=self.exchange,
                                   routing_key=topic,
                                   body=fact)

    def subscribe(self, topic):
        queue = self.channel.queue_declare(exclusive=False).method.queue
        self.channel.queue_bind(exchange=self.exchange, queue=queue,
                                routing_key=topic)
        return queue

    def fetch_from_sub(self, topic, queue, spin=spin):
        return spin(lambda: self._check_queue(queue), 10)

    def _check_queue(self, queue):
        return self.channel.basic_get(queue=queue, no_ack=True)[2]
