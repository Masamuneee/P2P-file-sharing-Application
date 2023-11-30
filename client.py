import socket
import os
from threading import Thread
import random
import time
import tqdm

class PeerClient:
    Flag = False
    peer_repo = []
    SERVER_PORT = 7774
    SERVER_HOST = "localhost"
    BLOCK = 128 << 10 # 128KB
    BLOCK1 = 1 << 20 # 1024KB

    def send_requests(msg : str, server_host, server_port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, server_port))
        client_socket.send(msg.encode())
        response = client_socket.recv(1024).decode()
        print(response)
        client_socket.close()
        return response

    def upload():
        upload_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upload_host = socket.gethostbyname(socket.gethostname())
        upload_socket.bind((upload_host, port))
        upload_socket.listen(5)
        while Flag != True:
            (client_socket,client_addr) = upload_socket.accept()
            print('Got connection from', client_addr)
            new_thread = Thread(target=peer_connect, args=(client_socket, ))
            new_thread.start()
        
        upload_socket.close()

    def peer_connect(client_socket):
        reponame = client_socket.recv(1024).decode()
        filename = ""
        for repo in peer_repo:
            if repo['reponame'] == reponame:
                filename = repo['filename']
        file_size = os.path.getsize(filename)
        #Print for another pear
        client_socket.send(("recievied_" + filename).encode())
        client_socket.send(str(file_size).encode())
        with (client_socket, client_socket.makefile('wb') as wfile):
            with open(filename, 'rb') as f1:
                while data := f1.read(BLOCK):
                    wfile.write(data)
            wfile.flush()
            f1.close()
        wfile.close()
        client_socket.close()

    def download(reponame):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upload_host1 = socket.gethostbyname(socket.gethostname())
        msg = "FIND P2P-CI/1.0\nREPONAME:" + reponame
        send_requests(msg, "localhost", SERVER_PORT)
        #####
        client.connect((upload_host1, PeerClient.SERVER_PORT))
        client.send(reponame.encode())
        file_name = client.recv(1024).decode()
        file_size = client.recv(1024).decode()
        print(file_name + " " + file_size)

        progress = tqdm.tqdm(unit='B', unit_scale=True, 
                            unit_divisor=1000, total=int(file_size))
        with client.makefile('rb') as rfile:
            with open(file_name, 'wb') as f:
                remaining = int(file_size)
                while remaining != 0:
                    data = rfile.read(BLOCK1 if remaining > BLOCK1 else remaining)
                    f.write(data)
                    progress.update(len(data))
                    remaining -= len(data)
            f.close()
        rfile.close()
        client.close()
        return {"success": True, "message": f"File '{file_name}' downloaded successfully"}

    def add(host):
        msg = "JOIN P2P-CI/1.0\nHost:"+host+'\n'+"Port:"+str(port)
        send_requests(msg, "localhost", SERVER_PORT)

    def publish(host, title, filename):
        peer_repo.append({"filename" : title, "reponame" : filename})
        msg = "PUBLISH RFC P2P-CI/1.0\nHost:"+ host + '\n'+"Port:"+str(port)+'\n'+"File:"+ title + '\n'+ "Repo:"+ filename 
        send_requests(msg, "localhost", SERVER_PORT)

    def exit(host):
        msg =  "EXIT P2P-CI/1.0\nHost:"+ host + '\n'+"Port:"+str(port)
        send_requests(msg, "localhost", SERVER_PORT)
        Flag = True

    def find(filename):
        print(f"Exist {filename}" if filename in peer_repo else "Not exist")

    def recieve_ping():
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Assign IP address and port number to socket
        serverSocket.bind(("localhost", port))
        serverSocket.settimeout(1)
        while True:
            try:
                rand = random.randint(0, 10)
                time.sleep(1)
                message, address = serverSocket.recvfrom(1024)
                message = message.upper()
                serverSocket.sendto(message, address)
            except:
                pass
