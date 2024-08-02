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

def generate_deck():
    cards = [3, 2, 1, 13, 12, 11, 7, 6, 5, 4]
    player_card = []
    for i in range(3):
        player_card.append(random.choice(cards))
        
    return player_card

def interpret_message(message, player: Player):
    message_type = message["type"]
    
    match message_type:
        case "RECEIVE_CARD":
            player.deck = message["data"]
            print("Player({}): {}".format(player.id, player.deck))
            

def generate_message(source, destination, data, message_type, delivered):
    return {
        "source": source,
        "destination": destination,
        "data": data,
        "delivered": delivered,
        "type": message_type
    }



def main():
    carteador = False
    config_file_path = "./config.json"

    all_addresses = get_all_addresses(config_file_path)

    id = int(sys.argv[1])
    player = Player(id, all_addresses[id], create_socket(all_addresses[id]), 
                    get_next_machine_address(id, all_addresses))

    first = True
    if player.id == 0:
        carteador = True
        
    next_message_type = None
    while True:
        # Proxima mensagem/Proxima maquina
        if carteador and first:
            next_message_type = "RECEIVE_CARD"
            message = generate_message(player.address, player.next_player_address, generate_deck(),
                                    "RECEIVE_CARD", False)
            
            sent = send_message(message, player.next_player_address, player.socket)
            first = False
        
        
            
        data, address = receive_message(player.socket)
        if data:
            print("Source: {}".format(data["source"]))
            if tuple(data['destination']) == player.address:
                interpret_message(data, player)
                send_message(data, player.next_player_address, player.socket)
                    # manda pro próximo
            elif tuple(data["source"]) == player.address:
                print("Voltou pro papi")
                    # Interpreta
                        # Tira a mensagem
                            # Nova mensagem
            else:
                print("Nao eh pra mim")
                if not carteador: send_message(data, player.next_player_address, player.socket)
            
if __name__ == "__main__":
    main()   
            