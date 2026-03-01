import socket
import threading
import sys

HOST = "web-production-1466.up.railway.app"
PORT = 8291

def receive(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\nConnection closed.")
                break
            sys.stdout.write(data.decode())
            sys.stdout.flush()
        except:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    threading.Thread(target=receive, args=(sock,), daemon=True).start()

    while True:
        try:
            message = sys.stdin.readline()
            if not message:
                break
            sock.sendall(message.encode())
        except:
            break

    sock.close()

if __name__ == "__main__":
    main()