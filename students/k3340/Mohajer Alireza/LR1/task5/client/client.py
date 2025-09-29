import socket


def send_request(request_bytes):
    conn = socket.socket()
    conn.connect(("127.0.0.1", 14905))
    conn.send(request_bytes)
    response = conn.recv(4096)
    print(response.decode("utf-8", errors="ignore"))
    conn.close()


GET = b"GET /?discipline=TEST HTTP/1.1\r\nHost: localhost\r\n\r\n"
POST = b"POST / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 23\r\n\r\ndiscipline=physic&mark=70"


send_request(POST)
# send_request(GET)
