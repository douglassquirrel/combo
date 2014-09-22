A sample client to send and recieve messages on rabbitmq using the 'topic' feature.

##Example
Running the example program should connnnect to a rabbitmq server on localhost

    python main.py

It should send a message to the 'test_topic' every 2s as show by:

    "Sending Message"

and print the following off the topic queue

    [x] 'test_topic':'test'

##Sending from console

	from client import TopicClient
	tc = TopicClient()
	tc.publish_to_topic('hello', 'test_topic')

##Registering callbacks to topic messages

	def callback(ch, method, properties, body):
		print " [x] %r:%r" % (method.routing_key, body,)

	tc = TopicClient()
	tc.subscribe_to_topic(callback, 'test_topic')
	tc.run()

##Config
The few config options there are can be changed in client/config.py