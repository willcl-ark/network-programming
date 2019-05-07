from io import BytesIO
from time import time

from lib import BitcoinProtocolError, handshake, read_address, read_msg, read_varint, serialize_msg


def read_addr_payload(stream):
    addrs = {}
    length = read_varint(stream)
    addrs['addresses'] = [read_address(stream) for addr in range(length)]
    return addrs


class Node:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    @property
    def address(self):
        return self.ip, self.port


class Connection:

    def __init__(self, node):
        self.node = node
        self.sock = None
        self.stream = None
        self.start = None

        # Results
        self.peer_version_payload = None
        self.nodes_discovered = []

    def handle_ping(self, payload):
        response = serialize_msg(command=b'pong', payload=payload)
        self.sock.sendall(response)

    def handle_addr(self, payload):
        # TODO: interpret the payload
        payload = read_addr_payload(BytesIO('payload'))
        if len(payload['addresses']) > 1:
            self.nodes_discovered = [
                Node(a['ip'], a['port']) for a in payload['addresses']
            ]

    def handle_msg(self):

        # Handle next message
        msg = read_msg(self.stream)
        command = msg['command'].decode()
        payload = msg['payload']
        payload_len = len(msg['payload'])
        print(f'Received a "{command}" containing {payload_len} bytes')

        method_name = f'handle_{command}'

        # Respond to "ping"
        if command == b'ping':
            self.handle_ping(payload_len)

        # specially handle peer lists
        if command == b'addr':
            self.handle_addr(payload)

    def remain_alive(self):
        return not self.nodes_discovered

    def open(self):
        # Set start time
        self.start = time()

        # Open TCP connection
        print(f'Connecting to {self.node.ip}')
        self.sock = handshake(self.node.address)
        self.stream = self.sock.makefile('rb')

        # request peers' peers
        self.sock.sendall(serialize_msg(b'getaddr'))

        # handle messages until program exits
        while self.remain_alive():
            self.handle_msg()

    def close(self):
        # clean up socket's file descriptor
        if self.sock:
            self.sock.close()


class Crawler:

    def __init__(self, nodes):
        self.nodes = nodes

    def crawl(self):

        while True:
            # get next address from addresses and connect
            node = self.nodes.pop()

            try:

                conn = Connection(node)
                conn.open()
            except (OSError, BitcoinProtocolError) as e:
                print(f'Error: str({e})')
                continue
            finally:
                conn.close()

            # Handle the results if no exceptions
            self.nodes.extend(conn.nodes_discovered)
            print(f'{conn.node.ip} report version {conn.peer_version_payload}')


if __name__ == '__main__':
    nodes = [Node('2.82.223.39', 8333),
             Node('172.105.219.38', 8333),
             Node('34.222.156.12', 8333)]
    Crawler(nodes).crawl()
