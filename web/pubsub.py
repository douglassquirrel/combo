from json import dumps, loads
from pika import BlockingConnection, URLParameters
from spinner import spin

class PubSub:
    def __init__(self, url, exchange):
        self.conn = BlockingConnection(URLParameters(url))
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange=exchange, type='topic')
        self.exchange = exchange

    def publish(self, topic, fact):
        self.channel.basic_publish(exchange=self.exchange,
                                   routing_key=topic,
                                   body=dumps(fact))

    def subscribe(self, topic):
        queue = self.channel.queue_declare(exclusive=False).method.queue
        self.channel.queue_bind(exchange=self.exchange, queue=queue,
                                routing_key=topic)
        return queue

    def fetch_from_sub(self, topic, queue, timeout, spin=spin):
        result = spin(lambda: self._check_queue(queue), timeout)
        return self._safe_loads(result)

    def consume(self, topic, consumer):
        def rabbit_consumer(channel, method, properties, body):
            consumer(method.routing_key, loads(body))
        queue = self.subscribe(topic)
        self.channel.basic_consume(rabbit_consumer, queue=queue, no_ack=True)
        self.channel.start_consuming()

    def _check_queue(self, queue):
        return self.channel.basic_get(queue=queue, no_ack=True)[2]

    def _safe_loads(self, value):
        if value is None:
            return None
        else:
            return loads(value)
