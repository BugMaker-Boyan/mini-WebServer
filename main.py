import socket
import threading
import framework
import logging
import sys

# 在程序入口模块配置logging日志，然后在适当的位置打日志
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s-%(filename)s[lineno:%(lineno)s]-%(levelname)s-%(message)s",
                    filename="log.txt",
                    filemode="a")


class HttpWebServer(object):
    def __init__(self, port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(("", port))
        self.tcp_socket.listen(128)

    def run(self):
        while True:
            client, ip_port = self.tcp_socket.accept()
            sub_task = threading.Thread(target=self.solve, args=(client,), daemon=True)
            sub_task.start()

    @staticmethod
    def solve(client):
        recv_data = client.recv(4096)
        if len(recv_data) == 0:
            client.close()
            return

        recv_content = recv_data.decode("utf-8")
        recv_list = recv_content.split(" ", maxsplit=2)
        request_path = recv_list[1]
        if request_path == '/':
            request_path = '/index.html'

        if request_path.endswith(".html"):
            """动态资源请求"""
            logging.info("动态资源请求地址：" + request_path)
            # 动态资源请求交给web框架处理
            # 准备好给web框架的信息(用字典保存)
            env = {
                "request_path": request_path,
                # 额外的参数可以在env这个字典里继续添加
            }
            status, headers, response_body = framework.handle_request(env)
            # print(status, headers, response_body)

            response_line = "HTTP/1.1 " + status + "\r\n"
            response_header = ""
            for header in headers:
                # header 是一个包含key和value的元组，所以这里可以直接拿来用
                response_header += "%s: %s\r\n" % header

            response_data = (response_line + response_header + "\r\n" + response_body).encode('utf-8')

            client.send(response_data)
            client.close()

        else:
            """静态资源请求"""
            logging.info("静态资源请求地址：" + request_path)
            try:
                with open("static" + request_path, 'rb') as file:
                    file_data = file.read()
            except FileNotFoundError as error:
                # 404 Not Found
                response_line = "HTTP/1.1 404 Not Found\r\n"
                response_header = "Server: PWS/1.0\r\n"
                with open("static/error.html", 'rb') as file:
                    file_data = file.read()
                response_body = file_data

                response = (response_line + response_header + "\r\n").encode('utf-8') + response_body
                client.send(response)
            else:
                response_line = "HTTP/1.1 200 OK\r\n"
                response_header = "Server: PWS/1.0\r\n"
                response_body = file_data

                response = (response_line + response_header + "\r\n").encode('utf-8') + response_body
                client.send(response)
            finally:
                client.close()


def main():
    args = sys.argv
    if len(args) != 2:
        print("执行的命令格式如下： python3 xxx.py port(数字)")
        logging.warning("终端启动程序参数个数不等于2")
        return

    if not args[1].isdigit():
        print("执行的命令格式如下： python3 xxx.py port(数字)")
        logging.warning("终端启动程序端口参数非数字类型")
        return

    port = int(args[1])
    server = HttpWebServer(port)
    server.run()


if __name__ == '__main__':
    main()
