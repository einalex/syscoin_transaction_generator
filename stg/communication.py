import socket
import json
from concurrent.futures import ThreadPoolExecutor

from stg.logger import logger
from stg.scrambler import Scrambler
from stg.messages import createMessage

class Coder(object):

    def encode(self, obj):
        return bytes(json.dumps(obj), 'utf-8')

    def decode(self, message):
        return json.loads(message)


class Communicator(object):

    def __init__(self, hosts, port, key):
        self.connections = {}
        self.connection_list = []
        self.coder = Coder()
        self.ip = self._get_ip()
        # connect to satellite systems if we're the hub
        for host in hosts:
            connection = Connection((host, port), key)
            self.connection_list.append(connection)
            self.connections[host] = connection
            connection.establish()

        # wait for connection from the hub if we're a satellite system
        if not hosts:
            connection = Connection((self.ip, port), key)
            self.connections[self.ip] = connection
            connection.anticipate()

    def _get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def send(self, message):
        paket = self.coder.encode(message)
        for recipient in message["recipients"]:
            self.connections[recipient].send(paket)

    def _receive(self, connection):
        paket = connection.receive()
        return self.coder.decode(paket)

    def receive(self):
        with ThreadPoolExecutor(max_workers=len(self.connections)) as executor:
            futures = [executor.submit(self._receive, connection)
                       for recipient, connection in self.connections.items()]
            messages = [f.result() for f in futures]
        return messages

    def create_single_message(self, typ, connection, payload):
        return createMessage([connection.address[0]], typ, payload)

    def create_message(self, typ, payload):
        return createMessage(list(self.connections.keys()), typ, payload)


class Connection(object):

    def __init__(self, address, key, buffer_size=4096, timeout=4):
        self.scrambler = Scrambler(key)
        self.address = address
        self.buffer_size = buffer_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.socket.settimeout(timeout)

    def anticipate(self):
        self.socket.bind(self.address)
        self.socket.listen(1)
        self.socket, self.remote_address = self.socket.accept()
        logger.info('Connected to {:}'.format(self.remote_address))

    def establish(self):
        logger.debug("Connecting to {:}".format(self.address))
        self.socket.connect(self.address)
        logger.info("Connected to {:}".format(self.address))

    def close(self):
        self.socket.close()

    def send(self, packet):
        # self.socket.send(packet)
        ciphertext = self.scrambler.encrypt(packet)
        self.socket.sendall(ciphertext)

    def receive(self):
        # return self.socket.recv(self.buffer_size)
        while True:
            ciphertext = self.socket.recv(self.buffer_size)
            if not ciphertext:
                break
            packet = self.scrambler.decrypt(ciphertext)
            return packet
