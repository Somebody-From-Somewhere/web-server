import socket
import sys
import json
import pandas as pd
from email.parser import Parser
from urllib.error import HTTPError

MAX_LINE = 64*1024
MAX_HEADERS = 100



class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.bode = body

class Request:
    def __init__(self, method, target, version, headers, read_file):
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self. read_file = read_file

    @property
    def path(self):
        return self.url.path


class HTTPServer:
    def __init__(self, host_name, server_port, server_name):
        self._host = host_name
        self._port = server_port
        self._srv_name = server_name


    def srv_run(self):
        srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            srv_socket.bind((self._host, self._port))
            srv_socket.listen()
            while True:
                connection, _ = srv_socket.accept()
                try:
                    self.srv_client(connection)
                except Exception as e:
                    print('Server failed', e)
        finally:
            srv_socket.close()

    def srv_client(self, connection):
        try:
            request = self.parse_request(connection)
            response = self.handle_request(request)
            self.send_response(connection, response)
        except ConnectionResetError:
            connection = None
        except Exception as e:
            self.send_error(connection, e)

        if connection:
            connection.close()

    def parse_request(self, connection):
        read_file = connection.makefile('rb')
        method, target, ver = self.parse_request_line(read_file)
        headers = self.parse_headers(read_file)
        host = headers.get('Host')
        if not host:
            raise HTTPError(400, 'Bad request', 'Host header is missing')
        if host not in (self._srv_name, f'{self._srv_name}:{self._port}'):
            raise HTTPError(404, 'Not found')
        return Request(method, target, ver, headers, read_file)

    def parse_request_line(self, read_file):
        raw = read_file.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
            raise HTTPError(400, 'Bad request', 'Request line is too long')

        req_line = str(raw, 'iso-8859-1')
        words = req_line.split()
        if len(words) != 3:
            raise HTTPError(400, 'Bad request', 'Not enough arguments')

        method, target, ver = words
        if ver != 'HTTP/1.1':
            raise HTTPError(505, 'HTTP version not supported')
        return method, target, ver

    def parse_headers(self, read_file):
        headers = []
        while True:
            line = read_file.readline(MAX_LINE + 1)
            if len(line) > MAX_LINE:
                raise HTTPError(494, 'Request header too large')

            if line in (b'\r\n', b'\n', b''):
                break

            headers.append(line)
            if len(headers) > MAX_HEADERS:
                raise HTTPError(494, 'Too many headers')

        string_headers = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(string_headers)

    def handle_request(self, request):
        if request.method == 'GET':
            if request.target.startswith('/card/'):
                card_number = request.target[len('/card/'):]
                if card_number.isdigit():
                    card_number_len = len(card_number)
                    if (card_number_len >= 16) & (card_number_len <= 20):
                        return self.handle_get_bank_info(request, card_number)
            raise HTTPError(404, 'Not found')

    def handle_get_bank_info(self, request, card_number):
        bank_name = str(binlist_data[binlist_data.bin == int(card_number[:6])]['issuer'].values[0])
        content_type = 'application/json; charset=utf-8'
        body = json.dumps(bank_name)
        body = body.encode('utf-8')
        headers = [('Content-Type', content_type), ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)

    @staticmethod
    def send_response(connection, response):
        write_file = connection.makefile('wb')
        status_line = f'HTTP/1.1 {response.status} {response.reason}\r\n'
        write_file.write(status_line.encode('iso-8859-1'))

        if response.headers:
            for (key, value) in response.headers:
                header_line = f'{key}: {value}\r\n'
                write_file.write(header_line.encode('iso-8859-1'))
        write_file.write(b'\r\n')
        if response.bode:
            write_file.write(response.bode)

        write_file.flush()
        write_file.close()

    def send_error(self, connection, error):
        try:
            status = error.status
            reason = error.reason
            body = (error.body or error.reason).encode('utf-8')
        except:
            status = 500
            reason = b'Internal server errors'
            body = b'Error'
        response = Response(status, reason, [('Content-Length', len(body))], body)
        self.send_response(connection, response)


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    srv_name = sys.argv[3]
    try:
        binlist_data = pd.read_csv('binlist-data.csv')
        srv = HTTPServer(host, port, srv_name)
        try:
            srv.srv_run()
        except KeyboardInterrupt:
            pass

    except KeyboardInterrupt:
        pass


