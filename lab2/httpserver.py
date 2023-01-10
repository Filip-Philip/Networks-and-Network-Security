"""
Lab 2 - Single Socket / HTTP Server
NAME: Filip Skalka
STUDENT ID: 14635011
DESCRIPTION:
"""

import socket
from datetime import datetime
import os
import subprocess
import copy

# This is just an example of how you could implement the server. You may change
# this however you wish.
# For example, you could do a really nice object oriented version if you like.


def normalize_line_endings(s):
    r'''Convert string containing various line endings like \n, \r or \r\n,
    to uniform \n.'''

    return ''.join((line + '\n') for line in s.splitlines())


def serve(port, public_html, cgibin):
    """
    The entry point of the HTTP server.
    port: The port to listen on.
    public_html: The directory where all static files are stored.
    cgibin: The directory where all CGI scripts are stored.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', port))
    server_socket.listen(5)

    page_counter = 0
    while True:
        client_connection, client_address = server_socket.accept()
        request = normalize_line_endings(client_connection.recv(1024).decode())
        request_head, request_body = request.split('\n\n', 2)
        request_head = request_head.splitlines()
        request_headline = request_head[0]

        request_headers = dict(x.split(': ', 1) for x in request_head[1:])
        request_method, request_content_whole, request_proto = request_headline.split(' ', 3)
        content_type_requested = request_headers['Accept'][8:].split('/')[0]
        date = datetime.now()
        if request_method != 'GET':
            # date = datetime.now()
            date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S CET')
            error_response = "HTTP/1.1 501 NOT IMPLEMENTED"
            client_connection.send(error_response.encode())
            error_headers = {
                'Content-Type': 'None; encoding=utf8',
                'Content-Length': 0,
                'Connection': 'close',
                'Date': date,
                'Server': 'Python Custom Server',
            }
            error_headers_raw = ''.join('%s: %s\n' % (k, v) for k, v in error_headers.items())
            client_connection.send(error_headers_raw.encode())
        else:
            content_requested_split = request_content_whole.split('?')
            if len(content_requested_split) == 1:
                request_uri = content_requested_split[0]
                query_string = ''
            else:
                request_uri, query_string = content_requested_split

            if request_uri == '/':
                request_uri = '/index.html'
                cookie_header = request_headers.get('Cookie', '')
                # print("this is req: " + request_headers.get('Cookie', ''))
                if cookie_header == '':
                    page_counter = 1
                else:
                    cookies = [x.split('=') for x in cookie_header.split(';')]
                    for cookie in cookies:
                        # print(cookie)
                        if cookie[0] == "page-counter":
                            page_counter = int(cookie[1]) + 1
                            # print(page_counter)

            elif request_uri[:8] == '/cgi-bin':
                if request_uri == "/cgi-bin/dig.py":
                    domain = query_string.split('&')[0]
                    process = subprocess.Popen(['python3', f'{request_uri[1:]}', f'{domain}'],
                                               stdout=subprocess.PIPE)
                    output = process.stdout.read()
                else:
                    cookie_header = request_headers.get('Cookie', '')
                    env = {"DOCUMENT_ROOT": public_html,
                           "REQUEST_METHOD": request_method,
                           "REQUEST_URI": request_uri,
                           "QUERY_STRING": query_string,
                           "PATH": os.environ["PATH"],
                           "REQUEST_ADDR": request_headers.get('Host').split(':')[0],
                           "COOKIES": cookie_header}
                    process = subprocess.Popen(['python3', f'{request_uri[1:]}'],
                                               stdout=subprocess.PIPE, env=env)
                    output = process.stdout.read()

                hd = 'HTTP/1.1 200 OK'

                response_headers = {
                    'Content-Type': f'{request_uri}?{query_string}; encoding=utf8',
                    'Content-Length': len(output),
                    'Connection': 'close',
                    'Date': date,
                    'Server': 'Python Custom Server',
                }

                client_connection.send(hd.encode())
                response_headers_raw = ''.join('%s: %s\n' % (k, v)
                                               for k, v in response_headers.items())
                client_connection.send(response_headers_raw.encode())
                client_connection.send('\n'.encode())
                client_connection.send(output)
                client_connection.close()
                continue

            content_extension = request_uri.split('.')[1]
            try:
                fin = open(f'{public_html}{request_uri}', 'rb')
                response_body_raw = fin.read()
                fin.close()
            except OSError:
                # date = datetime.now()
                date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S CET')
                error_response = "HTTP/1.1 404 NOT FOUND"
                client_connection.send(error_response.encode())
                error_headers = {
                    'Content-Type': f'{content_type_requested}/{content_extension}; '
                                    f'encoding=utf8',
                    'Content-Length': 0,
                    'Connection': 'close',
                    'Date': date,
                    'Server': 'Python Custom Server',
                }
                error_headers_raw = ''.join('%s: %s\n' % (k, v)
                                            for k, v in error_headers.items())
                client_connection.send(error_headers_raw.encode())
                client_connection.close()
                continue

            # date = datetime.now()
            exp_date = datetime.utcnow().strftime('%a, %d %b %(Y+1) %H:%M:%S CET')

            response_headers = {
                'Content-Type': f'{content_type_requested}/{content_extension}; '
                                f'encoding=utf8',
                'Content-Length': len(response_body_raw),
                'Connection': 'close',
                'Date': date,
                'Server': 'Python Custom Server',
                'Set-Cookie': f'page-counter={page_counter}; '
                              # f'Expires={date.replace(year=date.year + 1)}'
                              f'Expires={exp_date}'
                }

            response_headers_raw = ''.join('%s: %s\n' % (k, v)
                                           for k, v in response_headers.items())
            print(response_headers_raw)
            response_proto = 'HTTP/1.1'
            response_status = '200'
            response_status_text = 'OK'

            client_connection.send(('%s %s %s' % (response_proto, response_status,
                                                  response_status_text)).encode())
            client_connection.send(response_headers_raw.encode())
            client_connection.send('\n'.encode())
            client_connection.send(response_body_raw)

            client_connection.close()
    pass


# This the entry point of the script.
# Do not change this part.
if __name__ == '__main__':
    import os
    import sys
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', help='port to bind to', default=8080, type=int)
    p.add_argument('--public_html', help='home directory',
                   default='./public_html')
    p.add_argument('--cgibin', help='cgi-bin directory', default='./cgi-bin')
    args = p.parse_args(sys.argv[1:])
    public_html = os.path.abspath(args.public_html)
    cgibin = os.path.abspath(args.cgibin)
    serve(args.port, public_html, cgibin)
