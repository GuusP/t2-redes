import json
import socket

                    
def get_next_machine_address(id: int, machine_address) -> int:
    if id + 1 == len(machine_address):
        return machine_address[0]
    else:
        return machine_address[id + 1]
    
        
def get_all_addresses(config_file_path):
    with open(config_file_path) as config_file:
        machine_port = json.load(config_file)["player_ports"]
        return [("localhost", x) for x in machine_port]
    
def create_socket(machine_address) -> socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(machine_address)

    return sock

def send_message(message, destination_address, sock: socket):
    message = json.dumps(message).encode('utf-8')
    sent = sock.sendto(message, destination_address)
    
def receive_message(sock: socket):
    data, address = sock.recvfrom(4096)
    data = json.loads(data.decode('utf-8'))
    data["destination"] = tuple(data["destination"])
    data["source"] = tuple(data["source"])
    return data, address





