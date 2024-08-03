import socket
import random
import sys
from enum import Enum
from configuration import *

message_types = ["RECEIVE_CARD", "SEND_CARD", "SEND_BET", "PRINT_LIFE", "PRINT_BETS",
                 "PRINT_RESULTS", "SEND_BAT"]

class MessageType(Enum):
    RESEND_MESSAGE = 0
    RECEIVE_CARD = 1
    SEND_CARD = 2
    SEND_BET = 3
    PRINT_LIFE = 4
    PRINT_BETS = 5
    PRINT_RESULTS = 6
    SEND_BAT = 7

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
    message["destination"] = tuple(message["destination"])
    message["source"] = tuple(message["source"])
    message_type = MessageType[message["type"]]

    
    match message_type:
        case MessageType.RECEIVE_CARD:
            player.deck = message["data"]
            if player.address == message["destination"]:
                print("Player({}): {}".format(player.id, player.deck))
            else:
                print("Nao eh pra mim")
            if player.dealer:
                print("Voltou pro papi")
                next_machine_address = get_next_machine_address(all_addresses.index(message["destination"]), all_addresses)
                if next_machine_address == player.address:
                    return MessageType.SEND_CARD, player.next_player_address
                else:
                    return MessageType.RECEIVE_CARD, next_machine_address
                
            
    return MessageType.RESEND_MESSAGE, player.next_player_address
            

def generate_message(source: tuple[str, int], destination: tuple[str, int], data, message_type: MessageType, delivered: bool, sequency: int):
    if sequency == 15:
        sequency = 1
    return {
        "source": source,
        "destination": destination,
        "data": data,
        "delivered": delivered,
        "type": message_type.name,
        "sequency": sequency
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
    last_received_message = None
    last_sent_message = 0
    while True:
        # Proxima mensagem/Proxima maquina
        if player.dealer and first:
            message = generate_message(player.address, player.next_player_address, generate_deck(),
                                            MessageType.RECEIVE_CARD, False, last_sent_message)
                    
            sent = send_message(message, player.next_player_address, player.socket)
            
            first = False
            
        data, address = receive_message(player.socket)
        if data:
            sequency = data["sequency"]
            print("Sequencia: " + str(sequency))
            print("last: " + str(last_received_message))
            if sequency != last_received_message:
                next_message_type, next_destination = interpret_message(data, player, all_addresses)
                last_received_message = sequency
                match next_message_type:
                    case MessageType.RECEIVE_CARD:
                        message = generate_message(player.address, next_destination, generate_deck(),
                                                MessageType.RECEIVE_CARD, False, sequency + 1)
                        
                        sent = send_message(message, player.next_player_address, player.socket)
                        first = False
                    
                    case MessageType.SEND_CARD:
                        print("Vamos enviar")
                    
                    case MessageType.RESEND_MESSAGE:
                        sent = send_message(data, player.next_player_address, player.socket)
                        
        
        
                
         
            
if __name__ == "__main__":
    main()   
            