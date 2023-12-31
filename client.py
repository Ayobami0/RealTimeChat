import socket
import threading
import json
import argparse

from rich.console import Console

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--address", action="store")
parser.add_argument("-p", "--port", action="store", type=int)

args = parser.parse_args()

console = Console()

class Client:
    def __init__(self):
        self.__CLIENT__ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__USERNAME__ = None
        self.__CON_STATUS__ = False
    
    def connect(self, HOST, PORT):
        console.print(f"[yellow]\[CONNECTING] Connecting server on host {HOST} and port {PORT}")
        try:
            self.__CLIENT__.connect((HOST, PORT))
            console.print(f"[green]\[CONNECTED] Connected to server on host {HOST} and port {PORT}")
            self.__CON_STATUS__ = True
        except:
            console.print(f'[red]\[CONNECTION FAILED] Unable to connect to host {HOST} and port {PORT}')
            exit()

        self.talk_to_server()
        self.send_msg()

    def talk_to_server(self):
        while not self.__USERNAME__:
            username = input("Enter a username: ")
            if username.strip():
                self.__USERNAME__ = username
                self.__CLIENT__.sendall(username.encode('utf=8'))
                break
            else:
                console.print('[red]\[ERROR] username cannot be empty')
        
        threading.Thread(target=self.listen_for_msg, ).start()
        self.send_msg()

    def listen_for_msg(self):
        try:
            while True:
                response = json.loads(self.__CLIENT__.recv(1024).decode())

                if not response:
                    console.print("[red]\[ERROR] Disconnected from the server.")
                    self.stop_client()
                    break

                username = response['username']
                message = response['message']
                timestamp = response['timestamp']

                if username == self.__USERNAME__:
                    justify = 'right'
                    username = 'you'
                else:
                    justify='left'
                console.print(
                    f"[blue bold]{username}[/][blue]: {message}",
                     justify=justify)
        except (socket.error, json.JSONDecodeError):
            console.print("[red]\[ERROR] Disconnected from the server.")
            self.stop_client()
    
    def send_msg(self):
        try:
            while True:
                message = input("")
                print("\033[A                             \033[A")
                if message == "":
                    console.print("[red]\[ERROR] Message cannot be empty")
                else:
                    if message == "/exit":
                        self.stop_client()
                        break
                    self.__CLIENT__.sendall(
                        json.dumps(
                            {'username': self.__USERNAME__, 'message': message}
                            ).encode('utf-8'))
        except (EOFError, KeyboardInterrupt):
            # Handles user pressing Ctrl+C or closing the client window
            self.stop_client()


    def stop_client(self):
        self.__CLIENT__.close()
        console.print("[yellow]Disconnected from the server.")
        exit()


if __name__ == '__main__':
    if args.address is None or args.port is None:
        console.print("[red]\[ERROR] Both the address and the port are required")
        exit()
    Client().connect(PORT=args.port, HOST=args.address)
    # Client().connect('0.tcp.eu.ngrok.io', 12436)    