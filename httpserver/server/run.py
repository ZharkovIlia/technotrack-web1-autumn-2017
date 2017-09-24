# -*- coding: utf-8 -*-
import socket
import os.path
import pathlib
import functools

realPathToResources = pathlib.Path(os.path.dirname(__file__)) / "../files/"
requestedPathToResources = b'/media'


def get_response(request):
    request_lines = request.split(sep = b'\r\n')
    GET_statement_parts = request_lines[0].split(sep = b' ')
    if len(GET_statement_parts) != 3 or GET_statement_parts[0] != b'GET':
        return get_bad_request()

    try:
        request_header_end = request_lines.index(b'')
        request_header_map = dict(tuple(entry.split(sep = b': ', maxsplit = 1))\
                                  for entry in request_lines[1:request_header_end])

    except ValueError:
        return get_bad_request()

    return get_page_with_resources(GET_statement_parts[1], request_header_map)


def get_page_not_found():
    return b'HTTP/1.1 404 Not Found\r\n\r\n404 Not Found'


def get_bad_request():
    return b'HTTP/1.1 400 Bad Request\r\n\r\n400 Bad Request'


def get_page_with_resources(request_resource, request_header_map):
    if request_resource == b'/':
        response = b'HTTP/1.1 200 Ok\r\n\r\nHello mister!\r\n' + \
            b'You are ' + request_header_map.get(b'User-Agent', b'Anonymous')
    elif request_resource.startswith(requestedPathToResources):
        relative_path = request_resource[len(requestedPathToResources):]
        if len(relative_path) > 0 and relative_path[0:1] == b'/':
            relative_path = relative_path[1:]

        resource = (realPathToResources / relative_path.decode()).resolve()
        if resource.is_dir():
            response = functools.reduce(lambda prev, next: prev + b'\r\n' + next.name.encode(), \
                                        resource.iterdir(), b'')

            if response == b'':
                response = b'directory is empty'

            response = b'HTTP/1.1 200 Ok\r\n\r\n' + response
        elif resource.is_file():
            try:
                f = resource.open(mode = "rb")
                response = f.read()
            except OSError:
                response = get_page_not_found()
            else:
                f.close()
                response = b'HTTP/1.1 200 Ok\r\n\r\n' + response

        else:
            response = get_page_not_found()

    else:
        response = get_page_not_found()

    return response


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Assigns address, consisted of two items: ip-address and port, to
# a socket 'server_socket'
server_socket.bind(('localhost', 8000))

# After execution of listen() server_socket becomes able to
# accept connection requests via accept() (see below)
server_socket.listen(0)

print('Started')

while True:
    try:
        (client_socket, address) = server_socket.accept()

        # Prints address of a socket, which is returned by accept()
        # and is used to send/receive data on the connection
        print('Got new client', client_socket.getsockname())

        # Receiving request (generally data) from the other end of connection
        request_string = client_socket.recv(2048)

        # Sending server response to the other end of connection
        client_socket.send(get_response(request_string))
        client_socket.close()

    # if we interrupt execution (for example, blocking accept() ) via Ctrl-C from terminal,
    # the code below is executed
    except KeyboardInterrupt:
        print('Stopped')

        # As we are in endless cycle and are leaving it via exit()
        # this is the only way to close connection and release associated memory.
        server_socket.close()
        exit()
