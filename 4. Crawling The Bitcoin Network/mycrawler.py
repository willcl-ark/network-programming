from lib import handshake, read_msg, serialize_msg, read_varint, read_address
from io import BytesIO


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

    def open(self):
        # establish connection
        print(f'Connecting to {self.node.ip}')
        self.sock = handshake(self.node.address)
        self.stream = self.sock.makefile('rb')

        # request peers' peers
        self.sock.sendall(serialize_msg(b'getaddr'))

        # print every gossip message we receive
        while True:
            # Handle next message
            msg = read_msg(self.stream)
            command = msg['command']
            payload_len = len(msg['payload'])
            print(f'Received a "{command}" containing {payload_len} bytes')

            # Respond to "ping"
            if command == b'ping':
                response = serialize_msg(command=b'pong', payload=msg['payload'])
                self.sock.sendall(response)
                print("Send pong")

            # specially handle peer lists
            if command == b'addr':
                # TODO: interpret the payload
                payload = read_addr_payload(BytesIO(msg['payload']))
                if len(payload['addresses']) > 1:
                    self.nodes_discovered = [
                        Node(a['ip'], a['port']) for a in payload['addresses']
                    ]
                    break
        pass

    def close(self):
        pass


class Crawler:

    def __init__(self, nodes):
        self.nodes = nodes

    def crawl(self):
        pass


def crawler(nodes):
    while True:
        # get next address from addresses and connect
        node = nodes.pop()

        try:

            conn = Connection(node)
            conn.open()
        except Exception as e:
            print(f'Error: str({e})')
            continue

        # Handle the results if no exceptions
        nodes.extend(conn.nodes_discovered)
        print(f'{conn.node.ip} report version {conn.peer_version_payload}')


if __name__ == '__main__':

    nodes = [Node('2.82.223.39', 8333)]
    crawler(nodes)

