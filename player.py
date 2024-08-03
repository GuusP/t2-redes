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
    UPDATE_LIFE = 4
    UPDATE_POINTS = 5


class Player:
    def __init__(self, id, address, socket, next_player_address):
        self.id = id
        self.address = address
        self.socket = socket
        self.next_player_address = next_player_address
        self.deck = []
        self.dealer = False


def generate_deck(game_info):
    card_sequence = [3, 2, 1, "K", "J", "Q", 7, 6, 5, 4]
    player_card = []
    for i in range(game_info["rounds_to_play"]):
        player_card.append(random.choice(card_sequence))

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
    

def interpret_receive_card(message, player: Player, all_addresses: list, game_info):
    converted_message = convert_message(message)
    if player.address == converted_message["destination"]:
        player.deck = message["data"]
        converted_message["delivered"] = True
    else:
        print("Nao eh pra mim")
    if player.dealer:
        print("Voltou pro papi")
        next_machine_address = get_next_machine_address(all_addresses.index(converted_message["destination"]), all_addresses)
        if next_machine_address == player.address:
            return send_bet(player)
        else:
            return send_receive_card(player, next_machine_address, game_info)

    return send_to_next(player, message)

def send_receive_card(player, destination, game_info):
    message = generate_message(player.address, destination, generate_deck(game_info),
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
    
def interpret_send_bet(player: Player, message, game_info):
    if player.dealer == False:
        print("Suas cartas: {}".format(player.deck))
        bet = int(input("Quantas rodadas você irá fazer?"))
        message["data"].append(bet)
        send_to_next(player, message)
    else:
        game_info["players_bets"] = message["data"]
        print("Apostas: {}".format(game_info["players_bets"]))
        send_card(player)
        
        
def interpret_send_card(player: Player, message, game_info):
    card_sequence = [3, 2, 1, "K", "J", "Q", 7, 6, 5, 4]
    cards_played = message["data"]
    print("Cartas jogadas: {}".format(cards_played))
    if  player.dealer == False:
        print("Suas cartas: {}".format(player.deck))
        continue_loop = True
        while continue_loop:
            card = input("Qual carta você quer jogar?")
            if card != "J" and card != "Q" and card != "K":
                card = int(card)
            if card in player.deck:
                message["data"].append(card)
                player.deck.remove(card)
                continue_loop = False
                send_to_next(player, message)    
            else:
                print("Você não tem essa carta")
    else:
        biggest_card_position = 0
        for i in range(1, len(cards_played)):
            if card_sequence.index(cards_played[i]) < card_sequence.index(cards_played[biggest_card_position]):
                biggest_card_position = i
                
        if biggest_card_position >= player.id:
            biggest_card_position += 1
            
        print("Quem ganhou essa rodada foi o jogador {}".format(biggest_card_position))
        game_info["rounds_won"][biggest_card_position] += 1
        game_info["rounds_played"] += 1
        
        send_update_points(player, game_info)
        
def send_update_points(player: Player, game_info):
    message = generate_message(player.address, None, game_info["rounds_won"], MessageType.UPDATE_POINTS,
                               False)
    
    send_to_next(player, message)
    
def interpret_update_points(player: Player, message, game_info):
    if player.dealer == False:
        game_info["rounds_won"] = message["data"]
        print("Rounds ganhos nessa rodada: {}".format(game_info["rounds_won"]))
        send_to_next(player, message)
        return
    
    if game_info["rounds_played"] == game_info["rounds_to_play"]:
        print("Acabou a rodada") # Atualizar vida, passar para o próximo carteador
    else:
        send_card(player)
    


def interpret_message(message, player: Player, game_info: dict):
    message_type = MessageType[message["type"]]
    match message_type:
        case MessageType.RECEIVE_CARD:
            return interpret_receive_card(message, player, game_info["all_addresses"], game_info)
        
        case MessageType.SEND_BET:
            return interpret_send_bet(player, message, game_info)
        
        case MessageType.SEND_CARD:
            return interpret_send_card(player, message, game_info)
        
        case MessageType.UPDATE_POINTS:
            return interpret_update_points(player, message, game_info)




def main():
    config_file_path = "./config.json"
    addresses = get_all_addresses(config_file_path)
    game_info = {
        "all_addresses": addresses,
        "player_lives": [12, 12, 12, 12],
        "players_bets": [0] * len(addresses),
        "rounds_won": [0] * len(addresses),
        "rounds_played": 0,
        "rounds_to_play": 3
    }
    id = int(sys.argv[1])
    print(id)
    player = Player(id, game_info["all_addresses"][id], create_socket(game_info["all_addresses"][id]),
                    get_next_machine_address(id, game_info["all_addresses"]))

    first = True
    if player.id == 0:
        player.dealer = True

    next_message_type = None
    while True:
        # Proxima mensagem/Proxima maquina
        if player.dealer and first:
            message = generate_message(player.address, player.next_player_address, generate_deck(game_info),
                                       MessageType.RECEIVE_CARD, False)

            send_message(message, player.next_player_address, player.socket)

            first = False

        data, address = receive_message(player.socket)
        if data:
            interpret_message(data, player, game_info)
            


if __name__ == "__main__":
    main()
