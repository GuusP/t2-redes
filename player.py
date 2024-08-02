import socket
import random
import sys
from enum import Enum
from configuration import *

message_types = ["RECEIVE_CARD", "SEND_CARD", "SEND_BET", "PRINT_LIFE", "PRINT_BETS",
                 "PRINT_RESULTS", "SEND_BAT"]

class Player:
    def __init__(self, id, address, socket, next_player_address):
        self.id = id
        self.address = address
        self.socket = socket
        self.next_player_address = next_player_address
        self.deck = []
        self.dealer = False

def generate_deck():
    cards = [3, 2, 1, 13, 12, 11, 7, 6, 5, 4]
    player_card = []
    for i in range(3):
        player_card.append(random.choice(cards))
        
    return player_card

def interpret_message(message, player: Player, all_addresses: list):
    message_type = message["type"]
    
    match message_type:
        case "RECEIVE_CARD":
            player.deck = message["data"]
            if player.address == message["destination"]:
                print("Player({}): {}".format(player.id, player.deck))
            if player.dealer:
                print("Voltou pro papi")
                next_machine_address = get_next_machine_address(all_addresses.index(message["destination"]), all_addresses)
                if next_machine_address == player.address:
                    return "SEND_CARD", player.next_player_address
                else:
                    return "RECEIVE_CARD", next_machine_address
                
            
    return None, player.next_player_address
            

def generate_message(source, destination, data, message_type, delivered):
    return {
        "source": source,
        "destination": destination,
        "data": data,
        "delivered": delivered,
        "type": message_type
    }



def main():
    config_file_path = "./config.json"

    all_addresses = get_all_addresses(config_file_path)

    id = int(sys.argv[1])
    print(id)
    player = Player(id, all_addresses[id], create_socket(all_addresses[id]), 
                    get_next_machine_address(id, all_addresses))

    first = True
    if player.id == 0:
        player.dealer = True
        
    next_message_type = None
    while True:
        # Proxima mensagem/Proxima maquina
        if player.dealer and first:
            message = generate_message(player.address, player.next_player_address, generate_deck(),
                                            "RECEIVE_CARD", False)
                    
            sent = send_message(message, player.next_player_address, player.socket)
            
            first = False
            
        data, address = receive_message(player.socket)
        if data:
            next_message_type, next_destination = interpret_message(data, player, all_addresses)
            match next_message_type:
                case "RECEIVE_CARD":
                    message = generate_message(player.address, next_destination, generate_deck(),
                                            "RECEIVE_CARD", False)
                    
                    sent = send_message(message, player.next_player_address, player.socket)
                    first = False
                
                case "SEND_CARD":
                    print("Vamos enviar")
                
                case _:
                    print("Nao eh pra mim")
                    sent = send_message(data, player.next_player_address, player.socket)
                
        
            
if __name__ == "__main__":
    main()   
            