import socket
import random
import sys
from enum import Enum
from configuration import *
import copy

class MessageType(Enum):
    SEND_TO_NEXT = 0
    RECEIVE_CARD = 1
    SEND_CARD = 2
    SEND_BET = 3
    PRINT_LIFE = 4
    PRINT_BETS = 5
    PRINT_RESULTS = 6


class Player:
    def __init__(self, id, address, socket, next_player_address):
        self.id = id
        self.address = address
        self.socket = socket
        self.next_player_address = next_player_address
        self.deck = []
        self.dealer = False
        self.player_bets = []


def generate_deck():
    cards = [3, 2, 1, 13, 12, 11, 7, 6, 5, 4]
    player_card = []
    for i in range(3):
        player_card.append(random.choice(cards))

    return player_card

def generate_message(source: tuple[str, int], destination: tuple[str, int], data, message_type: MessageType, delivered: bool):
    return {
        "source": source,
        "destination": destination,
        "data": data,
        "delivered": delivered,
        "type": message_type.name,
    }

def convert_message(message):
    new_message = copy.deepcopy(message)
    new_message["destination"] = tuple(new_message["destination"])
    new_message["source"] = tuple(new_message["source"])
    
    return new_message
    

def interpret_receive_card(message, player: Player, all_addresses: list):
    converted_message = convert_message(message)
    if player.address == converted_message["destination"]:
        player.deck = message["data"]
        print("Player({}): {}".format(player.id, player.deck))
        converted_message["delivered"] = True
    else:
        print("Nao eh pra mim")
    if player.dealer:
        print("Voltou pro papi")
        next_machine_address = get_next_machine_address(all_addresses.index(converted_message["destination"]), all_addresses)
        if next_machine_address == player.address:
            return send_bet(player)
        else:
            return send_receive_card(player, next_machine_address)

    return send_to_next(player, message)

def send_receive_card(player, destination):
    message = generate_message(player.address, destination, generate_deck(),
                                MessageType.RECEIVE_CARD, False)

    send_message(message, player.next_player_address, player.socket)
    
def send_card(player):
    message = generate_message(player.address, None, [], MessageType.SEND_CARD, False)
    send_to_next(player, message)
    

    
def send_to_next(player, message):
    send_message(message, player.next_player_address, player.socket)


 
def send_bet(player):
    message = generate_message(player.address, None, [], MessageType.SEND_BET, False)
    send_to_next(player, message)
    
def interpret_send_bet(player: Player, message):
    if player.dealer == False:
        bet = int(input("Quantas rodadas você irá fazer?"))
        message["data"].append(bet)
        send_to_next(player, message)
    else:
        player.player_bets = message["data"]
        print("Apostas: {}".format(player.player_bets))
        send_card(player)
        
        
def interpret_send_card(player: Player, message):
    print("Cartas jogadas: {}".format(message["data"]))
    if  player.dealer == False:
        print("Suas cartas: {}".format(player.deck))
        card = int(input("Qual carta você quer jogar?"))
        continue_loop = True
        while continue_loop:
            if card in player.deck:
                message["data"].append(card)
                player.deck.remove(card)
                continue_loop = False
                send_to_next(player, message)    
            else:
                card = int(input("Você não tem essa carta. Qual carta você quer jogar?"))


def interpret_message(message, player: Player, all_addresses: list):
    message_type = MessageType[message["type"]]
    match message_type:
        case MessageType.RECEIVE_CARD:
            return interpret_receive_card(message, player, all_addresses)
        
        case MessageType.SEND_BET:
            return interpret_send_bet(player, message)
        
        case MessageType.SEND_CARD:
            return interpret_send_card(player, message)




def main():
    config_file_path = "./config.json"
    bets = []
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
                                       MessageType.RECEIVE_CARD, False)

            send_message(message, player.next_player_address, player.socket)

            first = False

        data, address = receive_message(player.socket)
        if data:
            interpret_message(data, player, all_addresses)
            


if __name__ == "__main__":
    main()
