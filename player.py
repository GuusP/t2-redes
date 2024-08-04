'''TODO:
    - Arrumar prints
    - Encerrar quando acabar a vida
        - tirar a pessoa quando acaba a vida
    - comentarios
    - mover infos pro json
    - adicionar naipes
    - limitar qnt da aposta
    - diminuir a qntd de cartas a cada round
    
'''

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
    UPDATE_GAME_INFO = 6
    SEND_BAT = 7


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
            return send_bet(player, game_info)
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


 
def send_bet(player, game_info):
    message = generate_message(player.address, None, game_info["players_bets"], MessageType.SEND_BET, False)
    send_to_next(player, message)
    
def interpret_send_bet(player: Player, message, game_info):
    if player.dealer == False:
        print("Suas cartas: {}".format(player.deck))
        bet = int(input("Quantas rodadas você irá fazer?"))
        message["data"][player.id] = bet
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
        send_to_next(player, message)
    else:
        if game_info["rounds_played"] == game_info["rounds_to_play"]:
            print("Acabou a rodada") # Atualizar vida, passar para o próximo carteador
            for i in range(len(game_info["player_lives"])):
                if i != player.id:
                    game_info["player_lives"][i] -= abs(game_info["players_bets"][i] - game_info["rounds_won"][i])
                    
            reset_rounds(game_info)
            send_update_game_info(player, game_info)
        else:
            send_card(player)
            
    print("Rounds ganhos nessa rodada: {}".format(game_info["rounds_won"]))
    
def send_update_game_info(player, game_info):
    message = generate_message(player.address, None, game_info, MessageType.UPDATE_GAME_INFO,
                               False)
    
    send_to_next(player, message)
    
def interpret_updade_game_info(player: Player, game_info, message):
    if player.dealer == False:
        game_info["player_lives"] = message["data"]["player_lives"]
        game_info["rounds_won"] = message["data"]["rounds_won"]
        game_info["rounds_played"] =  message["data"]["rounds_played"]
        print("Começando uma nova rodada")
        print("Vidas: {}".format(game_info["player_lives"]))
        send_to_next(player, message)
    else:
        player.dealer = False
        send_bat(player) # recomeça aqui
        
def send_bat(player: Player):
    message = generate_message(player.address, player.next_player_address, None, MessageType.SEND_BAT,
                               False)
    
    send_to_next(player, message)
    
def interpret_send_bat(player: Player, message, game_info):
    destination = tuple(message["destination"])
    
    if player.address == destination:
        player.dealer = True
        game_info["first"] = True
    else:
        send_to_next(player, message)

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
        
        case MessageType.UPDATE_GAME_INFO:
            return interpret_updade_game_info(player, game_info, message)
        
        case MessageType.SEND_BAT:
            return interpret_send_bat(player, message, game_info)


def reset_rounds(game_info):
    for i in range(len(game_info["rounds_won"])):
        game_info["rounds_won"][i] = 0
        
    game_info["rounds_played"] = 0
        

def main():
    config_file_path = "./config.json"
    addresses = get_all_addresses(config_file_path)
    #TODO: passar as infos para o config.json
    game_info = {
        "all_addresses": addresses,
        "player_lives": [12] * len(addresses),
        "players_bets": [0] * len(addresses),
        "rounds_won": [0] * len(addresses),
        "rounds_played": 0,
        "rounds_to_play": 3,
        "first": True
    }
    id = int(sys.argv[1])
    print(id)
    player = Player(id, game_info["all_addresses"][id], create_socket(game_info["all_addresses"][id]),
                    get_next_machine_address(id, game_info["all_addresses"]))

    if player.id == 0:
        player.dealer = True

    next_message_type = None
    while True:
        # Proxima mensagem/Proxima maquina
        if player.dealer and game_info["first"]:
            message = generate_message(player.address, player.next_player_address, generate_deck(game_info),
                                       MessageType.RECEIVE_CARD, False)

            send_message(message, player.next_player_address, player.socket)

            game_info["first"] = False

        data, address = receive_message(player.socket)
        if data:
            interpret_message(data, player, game_info)
            


if __name__ == "__main__":
    main()
