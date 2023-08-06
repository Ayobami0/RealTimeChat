import socket
import threading
import json
from datetime import datetime

from rich.console import Console

console = Console()
class Server:
    def __init__(self, host: str='127.0.0.1', port: int=1234):
        self.__HOST__ = host
        self.__PORT__ = port
        self.__CONNECTION_LIMIT__ = 10

        self.__SERVER__ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__is_running__ = True
        self.__exit_event__ = threading.Event()
        
        self.__ACTIVE_CLIENTS__: dict[str, socket.socket] = {}
        self.__SERVER_NAME__ = "SERVER"

    def stop(self):
        self.__exit_event__.set()
        self.__is_running__ = False

        for client in self.__ACTIVE_CLIENTS__.values():
            client.close()
    
    def start(self):
        # IPV4 address
        try:
            self.__SERVER__.bind((self.__HOST__, self.__PORT__))
            console.print(f"[yellow]\[STARTING] Starting server on {self.__HOST__} and {self.__PORT__}")
        except:
            console.print(f"[red]\[CONNECTION FAILED] Unable to bind to host {self.__HOST__} and port {self.__PORT__}")
            console.print_exception(show_locals=True)
            exit(1)
        
        self.__SERVER__.listen(self.__CONNECTION_LIMIT__)

        while self.__is_running__:
            client, address = self.__SERVER__.accept()

            console.print(f"[green]\[CONNECTED] Successfully connected to client {address}")

            threading.Thread(target=self.client_handler, args=(client,)).start()

        self.__SERVER__.close()
        for client in self.__ACTIVE_CLIENTS__.values():
            client.close()

    def listen(self, client: socket.socket):
        """
        Listens for message from client.
        The messages are in json format
        """

        while not self.__exit_event__.is_set():
            try:
                response: dict = json.loads(client.recv(1024).decode('utf-8'))
            except (socket.error, json.JSONDecodeError):
                # Client disconnected or error in data received, handle disconnection
                self.handle_disconnection(client)
                break
            if response:
                username = response['username']

                if (username in self.__ACTIVE_CLIENTS__.keys()):
                    message = response['message']
                    
                    timestamp = str(datetime.now())
                    response['timestamp'] = timestamp

                    
                    self.send_message_to_all_client(response)
                else:
                    console.print(f"[red]\[ERROR] User with username {username} is not active")
                    console.print_exception()


    def client_handler(self, client: socket.socket):
        while not self.__exit_event__.is_set():
            username = client.recv(1024).decode('utf-8')

            if username:
                if (username in self.__ACTIVE_CLIENTS__.keys()):
                    console.print(f"[red]\[ERROR] User with username {username} is already active")
                    continue
                self.__ACTIVE_CLIENTS__[username] = client
                console.print(f"[green]\[USER CONNECTED] User with username {username} is active")
                self.send_message_to_all_client(response={
                    'message': f'User {username} has joined',
                    'username': self.__SERVER_NAME__,
                    'timestamp': str(datetime.now())
                    }
                )
                break
        
        threading.Thread(target=self.listen, args=(client,)).start()

    def handle_disconnection(self, client: socket.socket):
        for username, active_client in list(self.__ACTIVE_CLIENTS__.items()):
            if active_client == client:
                console.print(f"[yellow]\[DISCONNECTED] User with username {username} has disconnected")
                del self.__ACTIVE_CLIENTS__[username]

                # Inform other clients about the disconnection
                self.send_message_to_all_client({
                    'message': f'User {username} has left',
                    'username': self.__SERVER_NAME__,
                    'timestamp': str(datetime.now())
                })
                break

    def send_message_to_client(self, response: dict, client: socket.socket):
        client.sendall(json.dumps(response).encode('utf-8'))

    def send_message_to_all_client(self, response: dict):
        for client in self.__ACTIVE_CLIENTS__.values():
            self.send_message_to_client(response, client)


if __name__ == '__main__':
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        # Handle Ctrl+C to stop the server gracefully
        server.stop()
        console.print("[yellow]Server stopped!")