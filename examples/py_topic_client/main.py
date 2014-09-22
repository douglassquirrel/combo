from client.client import TopicClient
from time import sleep
from multiprocessing import Process


def callback(ch, method, properties, body):
    print " [x] %r:%r" % (method.routing_key, body,)


def example_send(send_func):
    try:
        while True:
            print "Sending Message"
            send_func('test', 'test_topic')
            sleep(2)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':

    print "Starting"

    processes = []

    tc = TopicClient()
    tc.subscribe_to_topic(callback, 'test_topic')

    p1 = Process(target=tc.run, args=())
    p1.start()
    processes.append(p1)

    p2 = Process(target=example_send, args=(tc.publish_to_topic,))
    p2.start()
    processes.append(p2)

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print "Keyboard interrupt in main"
    finally:
        print "Cleaning up Main"
