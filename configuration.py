import json
import socket

def get_next_machine_address(id: int, machine_address) -> int:
    if id + 1 == len(machine_address):
        return machine_address[0]
    else:
        return machine_address[id + 1]

def get_all_addresses(config_file_path):
    with open(config_file_path) as config_file:
        config_data = json.load(config_file)
        machine_port = config_data["player_ports"]
        ip = config_data["ip"]
        return [(ip, x) for x in machine_port]

def create_socket(machine_address) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(machine_address)
    return sock

def send_message(message, destination_address, sock: socket.socket):
    message = json.dumps(message).encode('utf-8')
    sock.sendto(message, destination_address)

def receive_message(sock: socket.socket):
    data, address = sock.recvfrom(4096)
    data = json.loads(data.decode('utf-8'))
    return data, address

def get_rounds_to_play(config_file_path):
    with open(config_file_path) as config_file:
        config_data = json.load(config_file)
        return config_data["rounds_to_play"]

def get_player_lives(config_file_path):
    with open(config_file_path) as config_file:
        config_data = json.load(config_file)
        return config_data["player_lives"]

def get_config_file(config_file_path):
    with open(config_file_path) as config_file:
        config_data = json.load(config_file)
        return config_data
