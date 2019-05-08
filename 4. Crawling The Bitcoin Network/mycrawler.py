import socket
from io import BytesIO
from time import time

from lib import BitcoinProtocolError, read_address, read_msg, read_varint, read_version_payload, \
    serialize_msg, serialize_version_payload

DNS_SEEDS = [
    'dnsseed.bitcoin.dashjr.org',
    'dnsseed.bluematt.me',
    'seed.bitcoin.sipa.be',
    'seed.bitcoinstats.com',
    'seed.bitcoin.jonasschnelli.ch',
    'seed.btc.petertodd.org',
    'seed.bitcoin.sprovoost.nl',
    'dnsseed.emzy.de',
]


def query_dns_seeds():
    nodes = []
    for seed in DNS_SEEDS:
        try:
            addr_info = socket.getaddrinfo(seed, 8333, 0, socket.SOCK_STREAM)
            addresses = [ai[-1][:2] for ai in addr_info]
            nodes.extend([Node(*addr) for addr in addresses])
        except OSError as e:
            print(f"DNS seed query failed: {str(e)}")
    return nodes


def read_addr_payload(stream):
    addrs = {}
    length = read_varint(stream)
    addrs['addresses'] = [read_address(stream) for addr in range(length)]
    return addrs


class Node:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def __repr__(self):
        return f'Node({self.ip, self.port})'

    @property
    def address(self):
        return self.ip, self.port


class Connection:

    def __init__(self, node, timeout=10):
        self.node = node
        self.sock = None
        self.stream = None
        self.start = None
        self.timeout = timeout

        # Results
        self.peer_version_payload = None
        self.nodes_discovered = []

    def send_version(self):
        payload = serialize_version_payload()
        msg = serialize_msg(command=b"version", payload=payload)
        self.sock.sendall(msg)

    def send_verack(self):
        msg = serialize_msg(command=b"verack")
        self.sock.sendall(msg)

    def send_pong(self, payload):
        response = serialize_msg(command=b'pong', payload=payload)
        self.sock.sendall(response)

    def send_getaddr(self):
        self.sock.sendall(serialize_msg(b'getaddr'))

    def handle_version(self, payload):
        stream = BytesIO(payload)
        self.peer_version_payload = read_version_payload(stream)
        self.send_verack()

    def handle_verack(self, payload):
        # request peers' peers
        self.send_getaddr()

    def handle_ping(self, payload):
        self.send_pong(payload)

    def handle_addr(self, payload):
        # TODO: interpret the payload
        payload = read_addr_payload(BytesIO(payload))
        if len(payload['addresses']) > 1:
            self.nodes_discovered = [
                Node(a['ip'], a['port']) for a in payload['addresses']
            ]

    def handle_msg(self):

        # Handle next message
        msg = read_msg(self.stream)
        command = msg['command'].decode()
        print(f'Received "{command}"')

        method_name = f'handle_{command}'
        if hasattr(self, method_name):
            getattr(self, method_name)(msg['payload'])

    def remain_alive(self):
        timed_out = (time() - self.start) > self.timeout
        return not timed_out and not self.nodes_discovered

    def open(self):
        # Set start time
        self.start = time()

        # Open TCP connection
        print(f'Connecting to {self.node.ip}')
        self.sock = socket.create_connection(self.node.address,
                                             self.timeout)
        self.stream = self.sock.makefile("rb")

        # start version handshake
        self.send_version()

        # handle messages until program exits
        while self.remain_alive():
            self.handle_msg()

    def close(self):
        # clean up socket's file descriptor
        if self.sock:
            self.sock.close()


class Crawler:

    def __init__(self, timeout=10):
        self.nodes = []
        self.timeout = timeout
        self.connections = []

    def seed(self):
        self.nodes.extend(query_dns_seeds())

    def print_report(self):
        print(f'nodes: {len(self.nodes)} | connections: {len(self.connections)}')

    def crawl(self):
        # DNS lookups
        self.seed()

        while True:
            # get next node from addresses and connect
            node = self.nodes.pop()

            try:

                conn = Connection(node, self.timeout)
                conn.open()
            except (OSError, BitcoinProtocolError) as e:
                print(f'Error: str({e})')
                continue
            finally:
                conn.close()

            # Handle the results if no exceptions
            self.nodes.extend(conn.nodes_discovered)
            self.connections.append(conn)
            print(f'{conn.node.ip} report version {conn.peer_version_payload}')
            self.print_report()


if __name__ == '__main__':
    Crawler(timeout=5).crawl()
