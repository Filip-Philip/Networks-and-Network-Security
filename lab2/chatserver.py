"""
Lab 2 - Multiple Sockets / Chat Room (Server)
NAME: Filip Skalka
STUDENT ID: 14635011
DESCRIPTION:
"""
import socket
import select


class Server:
    def __init__(self, port, cert, key):
        self.server_socket = None
        self.socket_list = None
        self.port = port
        self.cert = cert
        self.key = key
        self.clients_to_names = dict()
        self.names_to_clients = dict()
        self.read_sockets = []
        self.write_sockets = []
        self.error_sockets = []
        self.help = "/nick <new_nick> - changes user's nickname to <new_nick>, \n" \
                    "/say <text> (or alternatively just <text>) - sends <text> to every user, \n" \
                    "/whisper <receiver_nick> <text> - sends <text> only to the " \
                    "specified user <receiver_nick>, \n" \
                    "/list - gets a list of all connected users, \n" \
                    "/help (or alternatively /?) - list of commands and their formats, \n" \
                    "/whois <user_nick> - prints information about <user_nick>, \n" \
                    "/kick <user_nick> - kicks <user_nick> from the chatroom."

    def serve(self):
        """
            Chat server entry point.
            port: The port to listen on.
            cert: The server public certificate.
            key: The server private key.
            """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen(5)

        name = 0

        self.socket_list = [self.server_socket]

        while True:
            self.read_sockets, self.write_sockets, self.error_sockets = select.select(
                self.socket_list, self.socket_list, [], 5)
            for read_socket in self.read_sockets:
                if read_socket is self.server_socket:
                    clientsock, clientaddr = read_socket.accept()
                    connect_message = f"{clientaddr} connected with name {name}\n"
                    self.names_to_clients[f"{name}"] = (clientaddr, clientsock)
                    self.clients_to_names[(clientaddr, clientsock)] = f"{name}"
                    name += 1
                    self.socket_list.append(clientsock)
                    self.read_sockets, self.write_sockets, self.error_sockets = select.select(
                        self.socket_list, self.socket_list, [], 5)
                    self.send_to_all(connect_message)
                else:
                    data = read_socket.recv(1024).decode()
                    if not data:
                        disconnect_message = f"{self.clients_to_names[(read_socket.getpeername(), read_socket)]}" \
                                             f" disconnected\n"
                        self.socket_list.remove(read_socket)
                        self.names_to_clients.pop(self.clients_to_names[(read_socket.getpeername(),
                                                                         read_socket)])
                        self.clients_to_names.pop((read_socket.getpeername(), read_socket))
                        self.send_to_all(disconnect_message)
                    else:
                        self.handle_command((read_socket.getpeername(), read_socket), data)

    def handle_command(self, client, command):
        if command[0] == '/':
            command_type = command.split(" ")[0]
            if command_type == '/nick':
                previous_name = self.clients_to_names[client]
                if command.split(" ")[1][:-1] in self.clients_to_names.values():
                    client[1].send(f"username {command.split(' ')[1][:-1]} "
                                   f"already in use\n".encode())
                else:
                    self.clients_to_names[client] = command.split(" ")[1][:-1]
                    self.names_to_clients.pop(previous_name)
                    self.names_to_clients[self.clients_to_names[client]] = client
                    self.send_to_all(f"user {previous_name} changed name to "
                                     f"{self.clients_to_names[client]}\n")
            elif command_type == '/say':
                self.send_to_all(f"{self.clients_to_names[client]}: {command.split(' ')[1]}")
            elif command_type == '/whois':
                nickname = command.split(" ")[1][:-1]
                message = f"{nickname} has address {self.names_to_clients[nickname][0]}\n"
                client[1].send(message.encode())
            elif command_type == '/kick':
                user_kicked = command.split(" ")[1][:-1]
                self.clients_to_names.pop(self.names_to_clients[user_kicked])
                self.socket_list.remove(self.names_to_clients[user_kicked][1])
                self.names_to_clients.pop(user_kicked)
                message = f"{user_kicked} has been kicked by " \
                          f"{self.clients_to_names[client]}"
                print(message)
            elif command_type[:-1] == '/help' or command_type[:-1] == '/?':
                print(self.help)
            elif command_type[:-1] == '/list':
                list_of_users = ''.join('%s %s\n' % (k, v[0]) for k, v in self.names_to_clients.items())
                client[1].send(list_of_users.encode())
            elif command_type == '/whisper':
                receiver_nick = command.split(" ")[1]
                text = ''.join('%s ' % s for s in command.split(" ")[2:])
                receiver_message = f"{self.clients_to_names[client]} whispers: {text}"
                sender_message = f"whisper to {receiver_nick}: {text}"
                self.names_to_clients[receiver_nick][1].send(receiver_message.encode())
                client[1].send(sender_message.encode())

        else:
            self.send_to_all(f"{self.clients_to_names[client]}: {command}")

    def send_to_all(self, message):
        for write_socket in self.write_sockets:
            write_socket.send(message.encode())


# Command line parser.
if __name__ == '__main__':
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', help='port to listen on', default=12345, type=int)
    p.add_argument('--cert', help='server public cert', default='public_html/cert.pem')
    p.add_argument('--key', help='server private key', default='key.pem')
    args = p.parse_args(sys.argv[1:])
    server = Server(args.port, args.cert, args.key)
    server.serve()
    # serve(args.port, args.cert, args.key)
