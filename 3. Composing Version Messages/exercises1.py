import time
import socket
from random import randint
from lib import compute_checksum

ZERO = b'\x00'
IPV4_PREFIX = b"\x00" * 10 + b"\x00" * 2
dummy_address = {
    "services": 0,
    "ip": '0.0.0.0',
    "port": 8333
}

def ip_to_bytes(ip):
    if ":" in ip:
        return socket.inet_pton(socket.AF_INET6, ip)
    else:
        return IPV4_PREFIX + socket.inet_pton(socket.AF_INET, ip)

def serialize_address(address, has_timestamp):
    result = b""
    if has_timestamp:
        result += int_to_little_endian(address['timestamp'], 8)
    result += int_to_little_endian(address['services'], 8)
    result += ip_to_bytes(address['ip'])
    result += int_to_big_endian(address['port'], 2)
    return result

def int_to_little_endian(integer, length):
    return integer.to_bytes(length, 'little')

def int_to_big_endian(integer, length):
    return integer.to_bytes(length, 'big')
    
key_to_multiplier = {
    'NODE_NETWORK': 2**0,
    'NODE_GETUTXO': 2**1,
    'NODE_BLOOM': 2**2,
    'NODE_WITNESS': 2**3,
    'NODE_NETWORK_LIMITED': 2**10,
    }
    
def services_dict_to_int(services_dict):
    result = 0
    for key, value in services_dict.items():
        if value == True:
            try:
                result += key_to_multiplier[key]
            except KeyError:
                print(f"Skipped key {key} as not found in key_to_multiplier dict.")
    return result

def bool_to_bytes(bool):
    if bool == True:
        return int_to_little_endian(1, 1)
    elif bool == False:
        return int_to_little_endian(0, 1)
    
def serialize_varint(i):
    raise NotImplementedError()
    
def serialize_varstr(bytes):
    raise NotImplementedError()
    
# Try implementing yourself here:
# def compute_checksum(bytes):
#     raise NotImplementedError()
    
def serialize_version_payload(
        version=70015, services_dict={}, timestamp=None,
        receiver_address=dummy_address,
        sender_address=dummy_address,
        nonce=None, user_agent=b'/buidl-army/',
        start_height=0, relay=True):
    if timestamp is None:
        timestamp = int(time.time())
    if nonce is None:
        nonce = randint(0, 2**64)
    # message starts empty, we add to it for every field
    msg = b''
    # version
    msg += int_to_little_endian(version, 4)
    # services
    msg += int_to_little_endian(services_dict_to_int(services_dict), 8)
    # timestamp
    msg += int_to_little_endian(timestamp, 8)
    # receiver address
    msg += ZERO * 26
    # sender address
    msg += ZERO * 26
    # nonce
    msg += int_to_little_endian(nonce, 8)
    # user agent
    msg += ZERO * 1 # zero byte signifies an empty varstr
    # start height
    msg += int_to_little_endian(start_height, 4)
    # relay
    msg += bool_to_bytes(relay)
    return msg 

def serialize_message(command, payload):
    result = b'magic bytes'
    result += b'command bytes'
    result += b'payload length bytes'
    result += b'checksum bytes'
    result += b'payload bytes'
    return result

def handshake(address):
    sock = socket.create_connection(address, timeout=1)
    stream = sock.makefile("rb")

    # Step 1: our version message
    sock.sendall("OUR VERSION MESSAGE")
    print("Sent version")

    # Step 2: their version message
    peer_version = "READ THEIR VERSION MESSAGE HERE"
    print("Version: ")
    print(peer_version)

    # Step 3: their version message
    peer_verack = "READ THEIR VERACK MESSAGE HERE"
    print("Verack: ", peer_verack)

    # Step 4: our verack
    sock.sendall("OUR VERACK HERE")
    print("Sent verack")

    return sock, stream