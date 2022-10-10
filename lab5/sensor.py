"""
Networks and Network Security
Lab 5 - Distributed Sensor Network

NAME(s): Filip Skalka, Mark Jansen
STUDENT ID(s): 14635011,
GROUP NAME:

DESCRIPTION: Definitions and message format
"""
import struct
from math import sqrt

# These are the message types.
MSG_PING = 0  # Multicast ping.
MSG_PONG = 1  # Unicast pong.
MSG_ECHO = 2  # Unicast echo.
MSG_ECHO_REPLY = 3  # Unicast echo reply.
# TODO: You may define your own message types if needed.

# These are the echo operations.
OP_NOOP = 0  # Do nothing.
OP_SIZE = 1  # Compute the size of network.
OP_UPDATE = 2  # Force update the network.
OP_DEGREE = 3 # Find the largest degree
# TODO: You may define your own echo operations if needed.

# This is used to pack message fields into a binary format.
message_format = struct.Struct('!iiiiiiiiiif')

# Length of a message in bytes.
message_length = message_format.size


class Sensor:
    """
    Container for parameters set by the command line or GUI.
    You can either use this class as is, or extend it to implement
    the assignment commands.
    """
    def __init__(self, mcast_addr, sensor_pos, sensor_strength,
                 sensor_value, grid_size, ping_period, peer, mcast, window):
        self.window = window

        # Define method to run when variable is changed in GUI:
        self.window._x.linked = self.update
        self.window._y.linked = self.update
        self.window._strength.linked = self.update
        self.window._period.linked = self.update
        self.window._value.linked = self.update
        
        # Define parameters we care about:
        self.mcast_addr = mcast_addr
        self.peer = peer
        self.mcast = mcast
        self.strength = sensor_strength
        self.pos = sensor_pos
        self.value = sensor_value
        self.grid_size = grid_size
        self.ping_period = ping_period

    @property
    def strength(self):
        return self.window._strength.get()

    @strength.setter
    def strength(self, value):
        self.window._strength.set(value)

    @property
    def pos(self):
        return (self.window._x.get(), self.window._y.get())

    @pos.setter
    def pos(self, value):
        x, y = value
        self.window._x.set(x)
        self.window._y.set(y)
        self.update_title()

    @property
    def value(self):
        return self.window._value.get()

    @value.setter
    def value(self, value):
        self.window._value.set(value)

    @property
    def ping_period(self):
        return self.window._period.get()

    @ping_period.setter
    def ping_period(self, value):
        self.window._period.set(value)

    def update(self):
        self.update_title()

        # TODO Code here will run when a parameter is changed in the GUI

    def update_title(self):
        x, y = self.pos
        ip, port = self.peer.getsockname()
        self.window._master.title(f"Sensor Client ({x}, {y}) {ip}:{port} {self.strength}")

    # TODO Add any additonal methods here
    def get_distance_to(self, position):
        return sqrt((self.pos[0] - position[0])**2 + (self.pos[1] - position[1])**2)


def message_encode(type, sequence, initiator, neighbor, target=(0, 0),
                   operation=0, strength=0, payload=0):
    """
    Encodes message fields into a binary format.
    type: The message type.
    sequence: The wave sequence number.
    initiator: An (x, y) tuple that contains the initiator's position.
    neighbor: An (x, y) tuple that contains the neighbor's position.
    operation: The echo operation.
    strength: The strength of initiator
    payload: Echo operation data (a number and a decaying rate).
    Returns: A binary string in which all parameters are packed.
    """
    ix, iy = initiator
    nx, ny = neighbor
    tx, ty = target
    return message_format.pack(type, sequence, ix, iy, nx, ny, tx, ty,
                               operation, strength, payload)


def message_decode(buffer):
    """
    Decodes a binary message string to Python objects.
    buffer: The binary string to decode.
    Returns: A tuple containing all the unpacked message fields.
    """
    type, sequence, ix, iy, nx, ny, tx, ty, operation, strength, payload = \
        message_format.unpack(buffer)
    return (type, sequence, (ix, iy), (nx, ny), (tx, ty), operation, strength,
            payload)
