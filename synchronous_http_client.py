import socket
from urllib.parse import urlparse

CHUNK_SIZE = 1024
HTTP_VERSION = 1.0
CRLF = "\r\n\r\n"


def receive_all(sock):
    chunks = []
    while True:
        chunk = sock.recv(CHUNK_SIZE)
        if chunk:
            chunks.append(chunk)
        else:
            break

    return ''.join(i.decode() for i in chunks)


def get(url):
    url = urlparse(url)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        host, port = url.netloc.split(':')
    except ValueError:
        host = url.netloc
        port = 80
    else:
        port = int(port)
    sock.connect((host, port))
    msg = 'GET {0} HTTP/{1} {2}'
    sock.sendall(msg.format(url.path or '/', HTTP_VERSION, CRLF).encode())
    response = receive_all(sock)
    sock.close()
    return response


if __name__ == '__main__':
    print(get('http://127.0.0.1:8000/'))
