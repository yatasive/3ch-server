import socket
import threading
import hashlib
import random
import os

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8291))

# ===== PASSWORD HASHING =====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

USERS = {
    "rogue": hash_password("1"),
    "darkhood": hash_password("secret"),
    "redco4": hash_password("mypassword")
}

# ===== GLOBALS =====
clients = {}          # socket -> username
user_colors = {}      # username -> color
user_room = {}        # username -> room
rooms = {"#general": []}

COLORS = [
    "\033[31m", "\033[32m", "\033[33m",
    "\033[34m", "\033[35m", "\033[36m"
]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print(f"Server running on {HOST}:{PORT}")

# ===== UTIL =====
def send_line(sock, msg):
    try:
        sock.sendall((msg + "\n").encode())
    except:
        remove_client(sock)

def broadcast_room(room, message, exclude=None):
    for client in rooms.get(room, []):
        if client != exclude:
            send_line(client, message)

def remove_client(sock):
    if sock in clients:
        username = clients[sock]
        room = user_room.get(username)

        if room and sock in rooms.get(room, []):
            rooms[room].remove(sock)

        del clients[sock]
        user_colors.pop(username, None)
        user_room.pop(username, None)

        broadcast_room(room, f"{username} left the room.")

    try:
        sock.close()
    except:
        pass

# ===== CLIENT HANDLER =====
def handle_client(sock):
    try:
        send_line(sock, "\033[32m==========================================")
        send_line(sock, "        3-CH PRIVATE IRC NETWORK")
        send_line(sock, "==========================================")
        send_line(sock, "\033[0m")

        sock.sendall(b"Username: ")
        username = sock.recv(1024).decode().strip()

        sock.sendall(b"Password: ")
        password = sock.recv(1024).decode().strip()

        if username not in USERS or USERS[username] != hash_password(password):
            send_line(sock, "Login failed.")
            sock.close()
            return

        clients[sock] = username
        user_colors[username] = random.choice(COLORS)
        user_room[username] = "#general"
        rooms["#general"].append(sock)

        send_line(sock, "Login successful.")
        send_line(sock, "Type normally to chat.")
        send_line(sock, "Commands:")
        send_line(sock, "/create #room")
        send_line(sock, "/join #room")
        send_line(sock, "/msg user message")
        send_line(sock, "")

        broadcast_room("#general", f"{username} joined #general", sock)

        while True:
            data = sock.recv(1024)
            if not data:
                break

            text = data.decode().strip()
            if not text:
                continue

            # ===== CREATE ROOM =====
            if text.startswith("/create "):
                new_room = text.split(" ", 1)[1]

                if new_room in rooms:
                    send_line(sock, "Room already exists.")
                else:
                    rooms[new_room] = []
                    send_line(sock, f"Room {new_room} created.")
                continue

            # ===== JOIN ROOM =====
            if text.startswith("/join "):
                new_room = text.split(" ", 1)[1]

                if new_room not in rooms:
                    send_line(sock, "Room does not exist.")
                    continue

                old_room = user_room[username]
                rooms[old_room].remove(sock)

                rooms[new_room].append(sock)
                user_room[username] = new_room

                send_line(sock, f"You joined {new_room}")
                continue

            # ===== PRIVATE MESSAGE =====
            if text.startswith("/msg "):
                parts = text.split(" ", 2)
                if len(parts) < 3:
                    send_line(sock, "Usage: /msg user message")
                    continue

                target_user = parts[1]
                private_msg = parts[2]

                for client, user in clients.items():
                    if user == target_user:
                        send_line(client, f"(DM) [{username}]: {private_msg}")
                        send_line(sock, f"(DM to {target_user}): {private_msg}")
                        break
                else:
                    send_line(sock, "User not found.")
                continue

            # ===== NORMAL CHAT =====
            room = user_room[username]
            color = user_colors[username]
            formatted = f"{color}[{username}]\033[0m: {text}"

            broadcast_room(room, formatted, sock)

    except:
        pass

    remove_client(sock)

# ===== START SERVER =====
while True:
    client_socket, addr = server.accept()
    print(f"Connection from {addr}")
    threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()