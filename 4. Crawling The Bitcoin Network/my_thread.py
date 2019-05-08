import random
import threading
import time


def connect(node):
    print(f'Connecting to {node}')
    seconds = random.random()
    time.sleep(seconds)
    print(f'Connection to {node} took {seconds}')


class Connection:

    def __init__(self, node):
        self.node = node

    def open(self):
        connect(self.node)


class ConnectionWorker(threading.Thread):

    def __init__(self, node):
        super().__init__()
        self.node = node

    def run(self):
        Connection(self.node).open()


for node in range(10):
    # connect(node)

    thread = ConnectionWorker(node)
    thread.start()
