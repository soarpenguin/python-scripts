import logging
import sys
import SocketServer

logging.basicConfig(
        level = logging.DEBUG,
        format = '%(name)s: %(message)s',
    )

class EchoRequestHandler(SocketServer.BaseRequestHandler):

    def __init__ (self, request, client_address, server):
        self.logger = logging.getLogger('EchoRequestHandler')
        self.logger.debug('__init__')
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def setup(self):
        self.logger.debug('setup')
        return SocketServer.BaseRequestHandler.setup(self)

    def handle(self):
        self.logger.debug('handle')

        data = self.request.recv(1024)
        self.logger.debug('recv()->"%s"', data)
        self.request.send(data)

    def finish(self):
        self.logger.debug('finish')
        return SocketServer.BaseRequestHandler.finish(self)

class EchoServer(SocketServer.TCPServer):

    def __init__(self, server_address,
            handle_class = EchoRequestHandler,):
        self.logger = logging.getLogger('EchoServer')
        self.logger.debug('__init__')
        SocketServer.TCPServer.__init__(self, server_address, handle_class)
        return

    def server_activate(self):
        self.logger.debug('server_activate')
        SocketServer.TCPServer.server_activate(self)
        return

    def serve_forever(self, poll_interval = 0.5):
        self.logger.debug('waiting for request')
        self.logger.info('Handling requests, press <Ctrl-C> to quit')
        SocketServer.TCPServer.serve_forever(self, poll_interval)
        return

    def handle_request(self):
        self.logger.debug('handle_request')
        return SocketServer.TCPServer.handle_request(self)

    def verify_request(self, request, client_address):
        self.logger.debug('verify_request(%s, %s)',
                request, client_address)
        return SocketServer.TCPServer.verify_request(self, request, client_address)

    def process_request(self, request, client_address):
        self.logger.debug('process_request(%s, %s)', request, client_address)
        return SocketServer.TCPServer.process_request(self, request, client_address)

    def server_close(self):
        self.logger.debug('server_close')
        return SocketServer.TCPServer.server_close(self)

    def finish_request(self, request, client_address):
        self.logger.debug('finish_request(%s, %s)', request, client_address)
        return SocketServer.TCPServer.finish_request(self, request, client_address)

    def close_request(self, request_address):
        self.logger.debug('close_request(%s)', request_address)
        return SocketServer.TCPServer.close_request(self, request_address)

    def shutdown(self):
        self.logger.debug('shutdown')
        return SocketServer.TCPServer.shutdown(self)

if __name__ == '__main__':
    import socket
    import threading

    address = ('localhost', 0)
    server = EchoServer(address, EchoRequestHandler)
    ip, port = server.server_address

    t = threading.Thread(target = server.serve_forever)
    t.setDaemon(True)
    t.start()

    logger = logging.getLogger('client')
    logging.info('Server on %s:%s', ip, port)

    logger.debug('creating socket')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.debug('connecting to server')
    s.connect((ip, port))

    message = 'Hello world'
    logger.debug('sending data: "%s"', message)
    len_sent = s.send(message)

    logger.debug('waiting for response')
    response = s.recv(len_sent)
    logger.debug('response from server: "%s"', response)

    server.shutdown()
    s.close()
    logger.debug('done')
    server.socket.close()

