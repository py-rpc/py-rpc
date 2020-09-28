import socket

if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 5000))
    while True:
        msg = bytes(input(">>:"), encoding="utf8")  # 转成bytes类型
        if not msg: continue  # 输入为空 跳出循环又从第1行开始循环
        s.sendall(msg)
