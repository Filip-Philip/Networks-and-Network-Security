"""
Networks and Network Security
Lab 5 - Distributed Sensor Network
NAME(s): Filip Skalka, Mark Jansen
STUDENT ID(s): 14635011,
GROUP NAME:

DESCRIPTION:

"""
import sys
import struct
import socket
from random import randint, gauss
import sensor
from tkinter import TclError
from threading import Thread
from gui import MainWindow
from datetime import datetime, timedelta
import select

# Get random position in NxN grid.
def random_position(n):
    x = randint(0, n)
    y = randint(0, n)
    return (x, y)

class SensorClient(Thread):
    def __init__(self, mcast_addr, sensor_pos, sensor_strength, sensor_value,
                 grid_size, ping_period, window):
        """
        mcast_addr: udp multicast (ip, port) tuple.
        sensor_pos: (x,y) sensor position tuple.
        sensor_strength: initial strength of the sensor ping (radius).
        sensor_value: initial temperature measurement of the sensor.
        grid_size: length of the  of the grid (which is always square).
        ping_period: time in seconds between multicast pings.

        Additional parameters to this method should always have a default
        value!
        """
        super().__init__()

        # Save any parameters which should be accessible later:
        # TODO It's probably a good idea to either save the parameters
        # to this method here, or create a seperate class to hold them.
        self.window = window
        self.strength = sensor_strength
        self.ping_period = ping_period
        self.mcast_addr = mcast_addr
        self.neighbors = []

        # Listen for this socket becoming readable in your select call
        # to allow the main thread to wake the client from being blocked on
        # select. You should ignore the data being written to it.
        self.wake_socket = self.window.wake_thread
        self.read_sockets, self.write_sockets, self.error_sockets, self.socket_list = None, None, None, None

        # Create the multicast listener socket.
        self.mcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                   socket.IPPROTO_UDP)
        # Sets the socket address as reusable so you can run multiple instances
        # of the program on the same machine at the same time.
        self.mcast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Subscribe the socket to multicast messages from the given address.
        mreq = struct.pack('4sl', socket.inet_aton(mcast_addr[0]),
                        socket.INADDR_ANY)
        self.mcast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        if sys.platform == 'win32':  # windows special case
            self.mcast.bind(('localhost', mcast_addr[1]))
        else:  # should work for everything else
            self.mcast.bind(mcast_addr)

        # Create the peer-to-peer socket.
        self.peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                            socket.IPPROTO_UDP)
        # self.peer.
        # Set the socket multicast TTL so it can send multicast messages.
        self.peer.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 5)
        # Bind the socket to a random port.
        if sys.platform == 'win32':  # windows special case
            self.peer.bind(('localhost', socket.INADDR_ANY))
        else:  # should work for everything else
            self.peer.bind(('', socket.INADDR_ANY))

        self.window.writeln('my address is %s:%s' % self.peer.getsockname())
        self.window.writeln(f'my position is (%s, %s)' % sensor_pos)

        self.sensor = sensor.Sensor(mcast_addr, sensor_pos, sensor_strength, sensor_value,
                 grid_size, ping_period, self.peer, self.mcast, window)

        # TODO Implement additional code that should be run only once when starting
        # the client here:
        # tempVal, sourceAddress = self.peer.recvfrom(sensor.message_length)

    def run(self):
        """
        Implement the auto ping and listening for incoming messages here.
        """
        # self.socket_list = [self.wake_socket]
        self.socket_list = [self.mcast]
        last_ping = datetime.now()
        try:
            while not self.window.quit_event.is_set():
                # Implement code that should run continuously here:

                self.read_sockets, self.write_sockets, self.error_sockets = select.select(
                    self.socket_list, self.socket_list, [], 5)
                for read_socket in self.read_sockets:
                    # if read_socket is self.mcast:
                    #     clientsock, clientaddr = read_socket.accept()
                    #     # connect_message = f"{clientaddr} connected with name {name}\n"
                    #     # self.names_to_clients[f"{name}"] = (clientaddr, clientsock)
                    #     # self.clients_to_names[(clientaddr, clientsock)] = f"{name}"
                    #     # name += 1
                    #     self.socket_list.append(clientsock)
                    #     self.read_sockets, self.write_sockets, self.error_sockets = select.select(
                    #         self.socket_list, self.socket_list, [], 5)
                    #     # self.send_to_all(connect_message)
                    # else:
                    # print("got here")
                    message, address = read_socket.recvfrom(500)
                    # print(read_socket)
                    # print(read_socket.getaddrinfo("localhost", 80))
                    message = sensor.message_decode(message)
                    print(str(message) + "\n ----------- sent by -------- " + str(address))
                    if message[0] == sensor.MSG_PING:
                        if self.sensor.get_distance_to(message[2]) <= message[6]:
                            self.peer.sendto(sensor.message_encode(sensor.MSG_PONG, sensor.OP_NOOP, self.sensor.pos,
                                                                    self.sensor.pos), address)
                    elif message[0] == sensor.MSG_PONG:
                        if self.sensor.get_distance_to(message[2]) <= message[6]:
                            self.neighbors.append(message[2])

                    # self.handle_command((read_socket.getpeername(), read_socket), data)

                if self.ping_period != 0 and timedelta(
                        last_ping.second, datetime.now().second).seconds >= self.ping_period:
                    self.neighbors = []
                    # self.peer.sendto(sensor.message_encode(sensor.MSG_PING, sensor.OP_NOOP, self.sensor.pos,
                    #                                        self.sensor.pos), mcast_addr)
                    self.send_multicast()
                    last_ping = datetime.now()
                    # print("lol")
                # pass
        except TclError:
            pass

    def send_multicast(self, ):
        self.peer.sendto(sensor.message_encode(sensor.MSG_PING, sensor.OP_NOOP, self.sensor.pos,
                                               self.sensor.pos), self.mcast_addr)

    def text_entered(self, line):
        """
        Handle new input line here.
        Do not change the name of this method!
        This method is called each time a command is entered in
        the GUI.
        """
        # Implement code that should be run when a line is entered here:
        if line == "properties":
            self.window.writeln(f"{self.sensor.pos};{self.sensor.value};{self.sensor.strength};"
                                f"{self.sensor.mcast_addr[0]}:{self.sensor.mcast_addr[1]}")
        elif line == "ping":
            self.send_multicast()
        elif line == "list":
            for neighbor in self.neighbors:
                self.window.writeln(f"{self.sensor.pos};{self.sensor.get_distance_to(neighbor)}")
        pass


# Program entry point.
# You may add additional commandline arguments, but your program
# should be able to run without specifying them
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--group', help='multicast group', default='224.1.1.1',
                   type=str)
    p.add_argument('--port', help='multicast port', default=50000, type=int)
    p.add_argument('--pos', help='x,y sensor position', type=str)
    p.add_argument('--strength', help='sensor strength', default=50,
                   type=int)
    p.add_argument('--value', help='sensor measurement value (unused this year)', type=float)
    p.add_argument('--grid', help='size of grid', default=100, type=int)
    p.add_argument('--period', help='period between autopings (0=off)',
                   default=10, type=int)
    args = p.parse_args(sys.argv[1:])
    if args.pos:
        pos = tuple(int(n) for n in args.pos.split(',')[:2])
    else:
        pos = random_position(args.grid)
    value = args.value if args.value is not None else gauss(20, 2)
    mcast_addr = (args.group, args.port)

    w = MainWindow()
    sensor_client = SensorClient(mcast_addr, pos, args.strength, value, args.grid, args.period, w)
    w.set_client(sensor_client)
    sensor_client.start()
    w.start()
