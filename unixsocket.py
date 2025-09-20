import socket
import os
import json

def start_server(server_id, callback):
    server_path = f"/tmp/{server_id}"

    if os.path.exists(server_path):
        os.remove(server_path)    
    print(f"Server started as {server_id}")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(server_path)
    server.listen(1)

    try:
        while True:
            conn, _ = server.accept()
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                #response = data.decode()
                response = callback(json.loads(data.decode()))
                conn.sendall(json.dumps(response).encode())
            conn.close()
    finally:
        print("Server closed")
        server.close()
        os.remove(server_path)

def send_message(server_id, message):
    message = json.dumps(message)
    
    server_path = f"/tmp/{server_id}"
    if not os.path.exists(server_path):
        return False, "Server does not exists", server_path
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(server_path)

    try:
        client.sendall(message.encode())
        data = client.recv(1024).decode()
        return json.loads(data)
    finally:
        client.close()
