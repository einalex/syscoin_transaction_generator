import socket
import json

from stg.logger import logger
from stg.scrambler import Scrambler



class Coder(object):

    def encode(self, obj):
        bytes(string, 'utf-8')
        return bytes(json.dumps(obj), 'utf-8')

    def decode(self, message):
        return json.parse(message.decode("utf-8"))



class Communicator(object):

    def __init__(self, hosts, port, key):
        self.connections = {}
        self.coder = Coder()
        self.ip = self._get_ip()
        # connect to satellite systems if we're the hub
        for host in hosts:
            connection = Connection((host, port), key)
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
        plaintext = self.coder.encode(message)
        ciphertext = self.scrambler.encrypt(plaintext)
        for recipient in message["recipients"]:
            self.connections[recipient].send(ciphertext)



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
        self.connection, self.remote_address = self.socket.accept()
        logger.info('Connected to {:}'.format(self.remote_address))
        while True:
            data = self.connection.recv(4096)
            if not data: break
            plain = self.scrambler.decrypt(data)
            print(plain)


    def establish(self):
        logger.debug("Connecting to {:}".format(self.address))
        self.socket.connect(self.address)
        logger.info("Connected to {:}".format(self.address))
        ciphertext = self.scrambler.encrypt('Hello, world')
        self.socket.sendall(ciphertext)


    def close(self):
        self.socket.close()


    def send(self, packet):
        self.socket.send(packet)


    def receive(self):
        return self.socket.receive(self.buffer_size)
