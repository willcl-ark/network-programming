from lib import handshake, read_msg, serialize_msg, read_varint, read_address
from io import BytesIO


def read_addr_payload(stream):
    addrs = {}
    length = read_varint(stream)
    addrs['addresses'] = [read_address(stream) for addr in range(length)]
    return addrs


def listener(addresses):
    while True:
        # get next address from addresses and connect
        address = addresses.pop()

        # establish connection
        print(f'Connecting to {address}')
        sock = handshake(address)
        stream = sock.makefile('rb')

        # request peers' peers
        sock.sendall(serialize_msg(b'getaddr'))

        # print every gossip message we receive
        while True:
            msg = read_msg(stream)
            command = msg['command']
            payload_len = len(msg['payload'])
            print(f'Received a "{command}" containing {payload_len} bytes')

            if command == b'ping':
                response = serialize_msg(command=b'pong', payload=msg['payload'])
                sock.sendall(response)
                print("Send pong")

            # specially handle peer lists
            if command == b'addr':
                # TODO: interpret the payload
                payload = read_addr_payload(BytesIO(msg['payload']))
                if len(payload['addresses']) > 1:
                    addresses.extend([
                        (a['ip'], a['port']) for a in payload['addresses']
                    ])
                    break


if __name__ == '__main__':

    remote_addr = [('2.82.223.39', 8333)]
    listener(remote_addr)

