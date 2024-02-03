import socketserver
import socket
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info('oO0OoO0OoO0Oo Nedis Server is starting oO0OoO0OoO0Oo')


from nedis import Nedis
nedis = Nedis()

import atexit
atexit.register(nedis.shutdown)

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.request: socket.socket
        logger.info(f"Connected from {self.client_address[0]}:{self.client_address[1]}")
        while True:
            self.data = self.request.recv(1024)
            if not self.data:
                break
            logger.info(f"Received from {self.client_address[0]}:{self.client_address[1]}: {self.data}")
            # just send back the same data, but upper-cased
            self.request.sendall(nedis.process(self.data).serialize())
        logger.info(f"Disconnected from {self.client_address[0]}:{self.client_address[1]}")

if __name__ == "__main__":
    HOST, PORT = "localhost", 6379
    # Create the server, binding to localhost on HOST PORT
    with socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        logger.info(f'The server is now ready to accept connections on port {PORT}')
        server.serve_forever()