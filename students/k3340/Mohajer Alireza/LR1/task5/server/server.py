import socket
import traceback
from email.parser import Parser

MAX_SIZE = 65535


class Request:
    def __init__(self, method, target, params, version, headers, body):
        self.method = method
        self.target = target
        self.params = params
        self.version = version
        self.headers = headers
        self.body = body


class Response:
    def __init__(self, status, reason, headers=None, body=None):
        self.status = status
        self.reason = reason
        self.headers = headers or b""
        self.body = body or b""


class MyHTTPServer:
    def __init__(self, host, port, coding="utf-8"):
        self.host = host
        self.port = port
        self.coding = coding

    def serve_forever(self):
        sock = socket.socket()
        sock.bind((self.host, self.port))
        sock.listen(5)
        print(f"Сервер запущен на {self.host}:{self.port}")

        while True:
            conn, addr = sock.accept()
            self.serve_client(conn, addr)

    def serve_client(self, conn, addr):
        print(f"Подключился клиент {addr}")
        conn.settimeout(5)

        try:
            request = self.parse_request(conn)
            response = self.handle_request(request)
        except Exception:
            traceback.print_exc()
            response = Response(400, "Bad Request")
        finally:
            self.send_response(conn, response)
            conn.close()

    def parse_request(self, conn) -> Request:
        # читаем заголовки
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = conn.recv(1024)
            # print(chunk)
            if not chunk:
                break
            data += chunk

        if not data:
            raise ValueError("empty request")

        header_data, _, body_data = data.partition(b"\r\n\r\n")
        header_text = header_data.decode(self.coding, errors="replace")

        # первая строка запроса
        lines = header_text.split("\r\n")
        req_line = lines[0]
        method, url, version = req_line.split(" ")

        # остальные строки → заголовки
        headers = Parser().parsestr("\r\n".join(lines[1:]))

        # параметры в URL
        if "?" in url:
            target, params_str = url.split("?", 1)
        else:
            target, params_str = url, ""
        params = self.parse_params_string(params_str)

        # тело запроса (если есть)
        body = {}
        if headers.get("Content-Length"):
            length = int(headers["Content-Length"])
            # дочитываем если пришло меньше чем нужно
            while len(body_data) < length:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                body_data += chunk
            body = self.parse_params_string(
                body_data.decode(self.coding, errors="replace")
            )

        return Request(method, target, params, version, headers, body)

    def parse_params_string(self, s: str) -> dict:
        result = {}
        if not s:
            return result
        for pair in s.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                result[key] = value.replace("+", " ")
        return result

    def handle_request(self, request: Request) -> Response:
        if request.method == "GET":
            with open(
                "task5/server/template_grades.html", "r", encoding=self.coding
            ) as f:
                template = f.read()

            try:
                with open("task5/server/grades.txt", "r", encoding=self.coding) as f:
                    rows = f.readlines()
            except FileNotFoundError:
                rows = []

            discipline = request.params.get("discipline")
            if discipline:
                rows = [r for r in rows if discipline in r]

            body = template.replace("{{rows}}", "".join(rows)).encode(self.coding)
            headers = (
                f"Content-Length: {len(body)}\r\nContent-Type: text/html\r\n".encode(
                    self.coding
                )
            )
            return Response(200, "OK", headers, body)

        elif request.method == "POST":
            discipline = request.body.get("discipline")
            mark = request.body.get("mark")
            if not discipline or not mark:
                return Response(400, "Bad Request")

            try:
                with open("task5/server/grades.txt", "r", encoding=self.coding) as f:
                    rows = f.readlines()
            except FileNotFoundError:
                rows = []

            updated = False
            new_rows = []
            for row in rows:
                if f"<td>{discipline}</td>" in row:
                    new_rows.append(f"<tr><td>{discipline}</td><td>{mark}</td></tr>\n")
                    updated = True
                else:
                    new_rows.append(row)

            if not updated:
                new_rows.append(f"<tr><td>{discipline}</td><td>{mark}</td></tr>\n")

            with open("task5/server/grades.txt", "w", encoding=self.coding) as f:
                f.writelines(new_rows)

            if updated:
                return Response(200, "Updated")
            else:
                return Response(201, "Created")

        else:
            return Response(405, "Method Not Allowed")

    def send_response(self, conn, response: Response):
        res_line = f"HTTP/1.1 {response.status} {response.reason}\r\n".encode(
            self.coding
        )
        conn.sendall(res_line)

        headers_text = response.headers.decode(self.coding, errors="ignore")

        if "Content-Type" not in headers_text:
            headers_text += f"Content-Type: text/html; charset={self.coding}\r\n"
        else:
            if "charset=" not in headers_text.lower():
                headers_text = headers_text.replace(
                    "Content-Type: text/html",
                    f"Content-Type: text/html; charset={self.coding}",
                )

        if "Content-Length" not in headers_text:
            headers_text += f"Content-Length: {len(response.body)}\r\n"

        conn.sendall(headers_text.encode(self.coding))
        conn.sendall(b"\r\n")

        if response.body:
            conn.sendall(response.body)


if __name__ == "__main__":
    server = MyHTTPServer("localhost", 14905)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Сервер остановлен")
