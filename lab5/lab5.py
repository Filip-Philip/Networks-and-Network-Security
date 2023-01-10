"""
Networks and Network Security
Lab 5 - Distributed Sensor Network
NAME(s): Filip Skalka, Mark Jansen
STUDENT ID(s): 14635011, 13385569
GROUP NAME: intelligent cow of vitality

DESCRIPTION:
This programme allows the user to set up a virtual distributed sensor network.
A user can choose the number of nodes in a network, strength of sensors and other parameters
through the command line arguments. A user can interact with the programme using a GUI or
through the command line window. Some options are only available through the command line.
The nodes of the networks ping each other to preserve a view of its neighbours. There are
other commands that perform more complicated operations on the network all based on the
echo algorithm. A user can learn the size of the network, its highest degree or even the
shortest path in terms of the number of hops to a given node.

Note: Some of the lines in the code could not possibly comply with the flake8/pep8 standard.
It either gave us a pep8 warning for the visual indent or the length of the line.
Since the we could not do anything about it, we ask for your flexibility.

"""
import sys
import struct
import socket
from random import randint, gauss
import sensor
from tkinter import TclError
from threading import Thread
from gui import MainWindow
from datetime import datetime
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
        self.neighbors = dict()
        self.addresses = []
        self.parent = dict()
        self.waves = dict()
        self.wave_id = 0
        self.wave_size = dict()
        self.paths = dict()
        self.received = dict()
        self.minimum_hops_path = dict()
        self.target = dict()
        self.parents = dict()
        self.highest_degree = dict()

        # Listen for this socket becoming readable in your select call
        # to allow the main thread to wake the client from being blocked on
        # select. You should ignore the data being written to it.
        self.wake_socket = self.window.wake_thread
        self.read_sockets, self.write_sockets = None, None
        self.error_sockets, self.socket_list = None, None

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
        self.window.writeln('my position is (%s, %s)' % sensor_pos)

        self.sensor = sensor.Sensor(mcast_addr, sensor_pos, sensor_strength, sensor_value,
                                    grid_size, ping_period, self.peer, self.mcast, window)

        # TODO Implement additional code that should be run only once when starting
        # the client here:

    def run(self):
        """
        Implement the auto ping and listening for incoming messages here.
        """
        # self.socket_list = [self.wake_socket]
        self.socket_list = [self.mcast, self.peer]
        last_ping = datetime.now()
        try:
            while not self.window.quit_event.is_set():
                # Implement code that should run continuously here:

                self.read_sockets, self.write_sockets, self.error_sockets = select.select(
                    self.socket_list, self.socket_list, [], 5)
                for read_socket in self.read_sockets:
                    message, address = read_socket.recvfrom(5000)
                    message = sensor.message_decode(message)
                    if message[0] == sensor.MSG_PONG:
                        if 0 < self.sensor.get_distance_to(message[2]) <= self.sensor.strength:
                            self.neighbors[message[2]] = address
                    elif message[0] == sensor.MSG_PING:
                        if 0 < self.sensor.get_distance_to(message[2]) <= self.sensor.strength:
                            self.peer.sendto(sensor.message_encode(sensor.MSG_PONG, 0,
                                             self.sensor.pos, self.sensor.pos,
                                             strength=self.strength), address)
                    elif message[0] == sensor.MSG_ECHO and message[5] != sensor.OP_DEGREE:
                        self.echo(message, address)

                    elif message[0] == sensor.MSG_ECHO and message[5] == sensor.OP_DEGREE:
                        self.echo_degree(message, address)

                    elif message[0] == sensor.MSG_ECHO_REPLY and message[5] != sensor.OP_DEGREE:
                        self.echo_reply(message)

                    elif message[0] == sensor.MSG_ECHO_REPLY and message[5] == sensor.OP_DEGREE:
                        self.echo_degree_reply(message)

                if self.ping_period != 0 and (datetime.now() - last_ping).total_seconds() >= self.ping_period:
                    self.neighbors = dict()
                    self.send_multicast(self.sensor.pos)
                    last_ping = datetime.now()

        except TclError:
            pass

    def send_degr_echo(self, type, option):
        """
        Send as initiator a message of type ECHO with option highest degree to neighbors.

        type: Type of message to be send as integer value.
        otion: opcode of the type message as integer value.

        side-effect: Neighbors in vacinity get receive UDP packet including a message.
        """
        self.highest_degree[(self.sensor.pos, self.wave_id)] = (self.sensor.pos, len(self.neighbors))
        self.waves[(self.sensor.pos, self.wave_id)] = []
        for coordinates, address in self.neighbors.items():
            self.waves[(self.sensor.pos, self.wave_id)].append(coordinates)
            message = sensor.message_encode(type, self.wave_id, self.sensor.pos,
                                            self.sensor.pos, self.sensor.pos,
                                            option, self.sensor.strength, 0)
            self.peer.sendto(message, address)
        self.wave_id = self.wave_id + 1

    def echo_degree(self, message, address):
        """
        Responds with an ECHO Reply or ECHO Message depending on
        the amount of neighbors the node contains.

        message: The message received and sent by neighbor.
        address: IP address and port of sender as a tuple.

        side-effect: If neighbors > 1, then send echo to it's neighbors
                     else send ECHO Reply to parent.
        """
        initiator, sequence_nr, sender = message[2], message[1], message[3]
        if not (initiator, sequence_nr) in self.parent.keys() and initiator != self.sensor.pos:
            self.highest_degree[(initiator, sequence_nr)] = (self.sensor.pos, len(self.neighbors))
            self.parent[(initiator, sequence_nr)] = (sender, address)
            self.waves[(initiator, sequence_nr)] = []
            len_neighbors = len(self.neighbors)
            if len_neighbors > 1:
                for (coordinates, address) in self.neighbors.items():
                    if (coordinates != sender):
                        self.waves[(initiator, sequence_nr)].append(coordinates)
                        message = sensor.message_encode(sensor.MSG_ECHO, sequence_nr,
                                                        initiator, self.sensor.pos,
                                                        self.sensor.pos, sensor.OP_DEGREE,
                                                        self.sensor.strength, 0)
                        self.peer.sendto(message, address)
            if len_neighbors == 1:
                message = sensor.message_encode(sensor.MSG_ECHO_REPLY, sequence_nr,
                                                initiator, self.sensor.pos,
                                                self.sensor.pos, sensor.OP_DEGREE,
                                                self.sensor.strength, 1)
                self.peer.sendto(message, address)
        else:
            message = sensor.message_encode(sensor.MSG_ECHO_REPLY,
                                            sequence_nr, initiator, self.sensor.pos,
                                            self.sensor.pos, sensor.OP_DEGREE,
                                            self.sensor.strength, 0)
            self.peer.sendto(message, address)

    def echo_degree_reply(self, message):
        initiator, sequence_nr, sender = message[2], message[1], message[3]
        if len(self.waves[(initiator, sequence_nr)]) > 0:
            if sender in self.waves[(initiator, sequence_nr)]:
                payload = message[7]
                self.waves[(initiator, sequence_nr)].remove(sender)
                if payload > self.highest_degree[(initiator, sequence_nr)][1]:
                    self.highest_degree[(initiator, sequence_nr)] = (message[4], payload)
            if len(self.waves[(initiator, sequence_nr)]) == 0:
                if self.sensor.pos == initiator:
                    if len(self.neighbors) > self.highest_degree[initiator, sequence_nr][1]:
                        self.window.writeln(f"Highest degree: {len(self.neighbors)}, node {self.sensor.pos}")
                    else:
                        self.window.writeln(
                            f"Highest degree: {self.highest_degree[(initiator, sequence_nr)][1]}, node {self.highest_degree[(initiator, sequence_nr)][0]}")

                elif len(self.neighbors) > self.highest_degree[(initiator, sequence_nr)][1]:
                    message = sensor.message_encode(sensor.MSG_ECHO_REPLY, sequence_nr,
                                                    initiator, self.sensor.pos,
                                                    self.sensor.pos, sensor.OP_DEGREE,
                                                    self.sensor.strength,
                                                    len(self.neighbors))
                    self.peer.sendto(message, self.parent[(initiator, sequence_nr)][1])
                else:
                    message = sensor.message_encode(sensor.MSG_ECHO_REPLY, sequence_nr,
                                                    initiator, self.sensor.pos,
                                                    self.highest_degree[(initiator, sequence_nr)][0],
                                                    sensor.OP_DEGREE,
                                                    self.sensor.strength,
                                                    self.highest_degree[(initiator, sequence_nr)][1])
                    self.peer.sendto(message, self.parent[(initiator, sequence_nr)][1])

    def echo(self, message, address):
        if not (message[2], message[1]) in self.waves.keys() and message[2] != self.sensor.pos:
            self.parent[(message[2], message[1])] = (message[3], address)
            self.parents[(message[2], message[1])] = [(message[3], address)]
            self.waves[(message[2], message[1])] = []
            self.minimum_hops_path[message[4]] = None
            if message[4] == self.sensor.pos and message[5] == sensor.OP_PATH:
                self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                       self.sensor.pos, operation=int(message[5]),
                                                       target=self.sensor.pos, payload=0),
                                 self.parent[(message[2], message[1])][1])
                self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                       self.sensor.pos, operation=sensor.OP_DONE_SENDING,
                                                       target=message[4]),
                                 self.parent[(message[2], message[1])][1])

            elif len(self.neighbors) > 1:
                self.wave_size[(message[2], message[1])] = 0
                self.parent[(message[2], message[1])] = (message[3], address)
                for coordinates, addr in self.neighbors.items():
                    if coordinates != self.parent[(message[2], message[1])][0]:
                        self.paths[(message[2], message[1], coordinates)] = []
                        self.waves[(message[2], message[1])].append(coordinates)
                        self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO, message[1], message[2],
                                                               self.sensor.pos, operation=message[5],
                                                               target=message[4]), addr)
            elif len(self.neighbors) == 1:
                self.parent[(message[2], message[1])] = (message[3], address)
                if message[5] == sensor.OP_SIZE:
                    self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                           self.sensor.pos, operation=message[5],
                                                           payload=1),
                                     self.parent[(message[2], message[1])][1])
                elif message[5] == sensor.OP_PATH:
                    self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                           self.sensor.pos, operation=sensor.OP_PATH,
                                                           target=(-1, -1)), address)
                    self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                           self.sensor.pos, operation=sensor.OP_DONE_SENDING,
                                                           target=message[4]),
                                     self.parent[(message[2], message[1])][1])
                else:
                    self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                           self.sensor.pos, operation=message[5]),
                                                           self.parent[(message[2], message[1])][1])

        elif (message[2], message[1]) in self.waves.keys() and message[2] != self.sensor.pos:
            if message[5] == sensor.OP_SIZE:
                self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                       self.sensor.pos, operation=int(message[5]),
                                                       payload=0), address)
            elif message[5] == sensor.OP_PATH:
                self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                       self.sensor.pos, operation=sensor.OP_PATH,
                                                       target=(-1, -1)), address)
                self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                       self.sensor.pos, operation=sensor.OP_DONE_SENDING,
                                                       target=message[4]), address)
            elif message[5] == sensor.OP_PATH_STRENGTH:
                self.parents[(message[2], message[1])] = [(message[3], address)]
            else:
                self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1],
                                                       message[2],
                                                       self.sensor.pos,
                                                       operation=int(message[5])), address)

    def echo_reply(self, message):
        if message[3] in self.waves[(message[2], message[1])] and message[5] != sensor.OP_PATH \
                and message[5] != sensor.OP_PATH_STRENGTH:
            self.waves[(message[2], message[1])].remove(message[3])

        if message[5] == sensor.OP_SIZE:
            self.wave_size[(message[2], message[1])] += int(message[7])

        elif message[5] == sensor.OP_PATH or message[5] == sensor.OP_PATH_STRENGTH:
            if message[4] != (-1, -1):
                self.paths[(message[2], message[1], message[3])].append((message[4], message[7]))

        elif message[5] == sensor.OP_DONE_SENDING:
            if self.paths[(message[2], message[1], message[3])]:
                self.paths[(message[2], message[1], message[3])].sort(key=lambda x: x[1])

        if not self.waves[(message[2], message[1])]:
            if message[2] != self.sensor.pos:
                if message[5] != sensor.OP_PATH:
                    self.window.writeln(f"({message[1]}, {message[2]}): Received from all neighbours.")
                if message[5] == sensor.OP_SIZE:
                    self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                           self.sensor.pos, operation=int(message[5]),
                                                           payload=self.wave_size[(message[2], message[1])] + 1),
                                                           self.parent[(message[2], message[1])][1])
                elif message[5] == sensor.OP_NOOP:
                    self.peer.sendto(
                        sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                              self.sensor.pos, operation=int(message[5])),
                        self.parent[(message[2], message[1])][1])
                elif message[5] == sensor.OP_PATH_STRENGTH:
                    for neighbor, address in self.parents[(message[2], message[1])]:
                        for node, index, strength in self.paths[(message[2], message[1], neighbor)]:
                            self.peer.sendto(
                                sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1],
                                                      message[2],
                                                      self.sensor.pos,
                                                      operation=int(message[5]),
                                                      target=node, payload=index,
                                                      strength=strength), address)

                        self.peer.sendto(
                            sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1],
                                                  message[2],
                                                  self.sensor.pos,
                                                  operation=sensor.OP_DONE_SENDING,
                                                  target=message[4]),
                            address)
                elif message[5] == sensor.OP_DONE_SENDING:
                    for path in [y for x, y in self.paths.items() if x[0] == message[2] and x[1] == message[1] and y]:
                        if self.minimum_hops_path[message[4]] is None or\
                                len(self.minimum_hops_path[message[4]]) > len(path):
                            self.minimum_hops_path[message[4]] = [node for node, index in path]
                    if not self.minimum_hops_path[message[4]]:
                        self.minimum_hops_path[message[4]] = [(-1, -1)]
                    else:
                        self.minimum_hops_path[message[4]] = [self.sensor.pos] + \
                                                    self.minimum_hops_path[message[4]]
                    for index, node in enumerate(self.minimum_hops_path[message[4]]):
                        self.peer.sendto(
                            sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                                  self.sensor.pos, operation=sensor.OP_PATH,
                                                  target=node, payload=float(index)),
                            self.parent[(message[2], message[1])][1])
                    self.peer.sendto(
                        sensor.message_encode(sensor.MSG_ECHO_REPLY, message[1], message[2],
                                              self.sensor.pos, operation=sensor.OP_DONE_SENDING,
                                              target=message[4]),
                        self.parent[(message[2], message[1])][1])
            else:
                if message[5] != sensor.OP_PATH:
                    self.window.writeln("The wave sequence_number has decided.")
                if message[5] == sensor.OP_SIZE:
                    self.window.writeln(f"size={self.wave_size[(message[2], message[1])] + 1}")
                elif message[5] == sensor.OP_DONE_SENDING:
                    for path in [y for x, y in self.paths.items() if x[0] == message[2] and x[1] == message[1] and y]:
                        if self.minimum_hops_path[message[4]] is None or len(self.minimum_hops_path[message[4]]) > len(path):
                            self.minimum_hops_path[message[4]] = [node for node, index in path]

                    if not self.minimum_hops_path[message[4]]:
                        self.window.writeln(f"There is no path from {self.sensor.pos} to {self.target[message[1]]}")
                    else:
                        for counter, node in enumerate(self.minimum_hops_path[message[4]]):
                            self.window.writeln(f"{counter + 1}. {node}")
                        message_hops = f"Minimum number of hops = {len(self.minimum_hops_path[message[4]]) - 1}"
                        self.window.writeln(message_hops)

    def compute_size(self):
        self.send_echo(sensor.OP_SIZE)

    def send_echo(self, option, target=(0, 0)):
        self.waves[(self.sensor.pos, self.wave_id)] = []
        if option == sensor.OP_SIZE:
            self.wave_size[(self.sensor.pos, self.wave_id)] = 0
        elif option == sensor.OP_PATH:
            self.target[self.wave_id] = target
            self.minimum_hops_path[target] = None
        for coordinates, address in self.neighbors.items():
            self.paths[(self.sensor.pos, self.wave_id, coordinates)] = []
            self.waves[(self.sensor.pos, self.wave_id)].append(coordinates)
            # self.received[(self.sensor.pos, self.wave_id, coordinates)] = False
            self.peer.sendto(sensor.message_encode(sensor.MSG_ECHO, self.wave_id,
                                                   self.sensor.pos,
                                                   self.sensor.pos,
                                                   operation=option,
                                                   target=target), address)
        self.wave_id += 1

    def send_multicast(self, initiator):
        self.peer.sendto(sensor.message_encode(sensor.MSG_PING, 0, initiator,
                                               self.sensor.pos, strength=self.strength),
                                               self.mcast_addr)

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
            self.send_multicast(self.sensor.pos)
        elif line == "list":
            sorted_neighbors = sorted(self.neighbors,
                                    key=lambda x: self.sensor.get_distance_to(x), reverse=True)
            for neighbor in sorted_neighbors:
                self.window.writeln(f"{neighbor};{self.sensor.get_distance_to(neighbor)}")
        elif (len(line.split(" ")) == 2 and line.split(" ")[0] == "strength"
              and line.split(" ")[1].isnumeric()):
            self.strength = int(line.split(" ")[1])
            self.sensor.strength = self.strength
        elif len(line.split(" ")) == 3 and line.split(" ")[0] == "move" and \
                line.split(" ")[1].isnumeric() and line.split(" ")[2].isnumeric():
            x = int(line.split(" ")[1])
            y = int(line.split(" ")[2])
            self.sensor.pos = (x, y)
        elif line == "echo":
            self.send_echo(sensor.OP_NOOP)
        elif line == "size":
            self.compute_size()
        elif len(line.split(" ")) == 3 and line.split(" ")[0] == "route_hops" and \
                line.split(" ")[1].isnumeric() and line.split(" ")[2].isnumeric():
            x = int(line.split(" ")[1])
            y = int(line.split(" ")[2])
            self.send_echo(sensor.OP_PATH, (x, y))
        elif line == "highest_degree":
            self.send_degr_echo(sensor.MSG_ECHO, sensor.OP_DEGREE)
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
