"""
Lab 2 - Multiple Sockets / Chat Room (Client)
NAME:
STUDENT ID:
DESCRIPTION:
"""

from threading import Thread
from gui import MainWindow
import select
import socket


class ChatClient(Thread):

    def __init__(self, port, cert, ip, window):
        """
        port: port to connect to.
        cert: public certificate (task 3)
        ip: IP to bind to (task 3)
        """
        super().__init__()

        # Save any parameters which should be accessible later:
        self.window = window
        self.port = port
        self.cert = cert
        self.ip = ip

        # Listen for this socket becoming readable in your select call
        # to allow the main thread to wake the client from being blocked on
        # select. You should ignore the data being written to it.
        self.wake_socket = self.window.wake_thread
        # Implement code that should be run only once when starting
        # the client here:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((socket.gethostbyname(socket.gethostname()), self.port))

    def run(self):
        """
        Implement listening for incoming messages here.
        """

        while not self.window.quit_event.is_set():
            read_sockets, write_sockets, error_sockets = select.select([self.wake_socket, socket.gethostbyname(
                socket.gethostname())], [], [])
            # Implement code that should run continuously here:
            for read_socket in read_sockets:
                data = read_socket.recv(1024).decode()
                self.window.write(data)

    def text_entered(self, line):
        """
        Handle new input line here.
        Do not change the name of this method!
        This method is called each time a message is sent in
        the GUI.
        """

        # Implement code that should be run when a line is entered here:
        self.client.send(line.encode())
        self.window.write(line.encode())

        # pass


# Command line argument parser.
if __name__ == '__main__':
    import sys
    import argparse
    p = argparse.ArgumentParser()

    # Make sure to use these arguments when setting up your socket!
    p.add_argument('--port', help='port to connect to',
                   default=12345, type=int)
    p.add_argument('--cert', help='server public cert', default='cert.pem', type=str)
    p.add_argument('--ip', help='IP to bind to', default='127.0.0.1', type=str)
    args = p.parse_args(sys.argv[1:])

    w = MainWindow()
    client = ChatClient(args.port, args.cert, args.ip, w)
    w.set_client(client)
    client.start()
    w.start()
