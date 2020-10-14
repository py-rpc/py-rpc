from gevent import socket, monkey, spawn


monkey.patch_socket()


class BaseServer:

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def run(self, app):
        raise NotImplemented


class GeventServer(BaseServer):

    def get_server(self):
        self.s = socket.socket()
        self.s.bind((self.host, self.port))
        self.s.listen()

    def run(self, app):
        s = socket.socket()
        s.bind((self.host, self.port))
        s.listen()
        while True:
            cli, addr = s.accept()
            spawn(self.handle_request, cli, app)

    def handle_request(self, conn, app):
        try:
            while True:
                data = conn.recv(app.config.get("MAX_RECV", 4096))
                ret = app.do_call(data)
                if isinstance(ret, str):
                    ret_data = ret.encode("utf-8")
                elif isinstance(ret, bytes):
                    ret_data = ret
                else:
                    app.logger.waring("""
                    OMG! The data of response to client is neither str or bytes, 
                    will return a empty bytes to client.
                    """)
                    ret_data = b""
                conn.send(ret_data)
        except Exception as ex:  # 打印异常
            print(ex)
        finally:
            conn.close()
