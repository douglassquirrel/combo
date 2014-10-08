from pika import BlockingConnection, ConnectionParameters

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

