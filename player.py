import socket
import random
import sys
from enum import Enum
from configuration import *
import copy

# Tipos de mensagem
class MessageType(Enum):
    RECEIVE_CARD = 1
    SEND_CARD = 2
    SEND_BET = 3
    UPDATE_POINTS = 4
    UPDATE_GAME_INFO = 5
    SEND_BAT = 6

# Tipo de destinatário
class DeliverType(Enum):
    UNI = 0, # Uma única máquina
    BROAD = 1 # Todas do anel

# Representa um jogador
class Player:
    def __init__(self, id, address, socket, next_player_address):
        self.id = id
        self.address = address
        self.socket = socket
        self.next_player_address = next_player_address
        self.deck = []
        self.dealer = False # Se é carteador/Se tem o bastão

# Informações gerais sobre o jogo
class GameInfo:
    def __init__(self, addresses, default_life, rounds_to_play=3 ):
        self.all_addresses = addresses
        self.player_lives = [default_life] * len(addresses)
        self.players_bets = [0] * len(addresses)
        self.rounds_won = [0] * len(addresses)
        self.rounds_played = 0
        self.rounds_to_play = rounds_to_play
        self.first = True # Se é a primeira rodada
        self.players_alive = [x for x in range(len(addresses))]
        self.player_count = len(addresses)
        self.default_life = default_life # Vida inicial de cada jogador

# Gera o baralho de um jogador
def generate_deck(game_info: GameInfo):
    card_sequence = [3, 2, 1, "K", "J", "Q", 7, 6, 5, 4]
    card_naipes = ["Paus", "Copas", "Espadas", "Ouros"]
    player_card = []
    for i in range(game_info.rounds_to_play):
        # Escolhe um número e um naipe aleatório para cada carta do baralho
        card = { 
            "number": random.choice(card_sequence),
            "naipe": random.choice(card_naipes)
        }
        player_card.append(card)

    return player_card

# Gera a mensagem
def generate_message(source: tuple[str, int], destination: tuple[str, int], data, message_type: MessageType, deliver_type: DeliverType):
    return {
        "source": source,
        "destination": destination,
        "data": data,
        "delivered_uni": False,
        "delivered_broad": [],
        "type": message_type.name,
        "deliver_type": deliver_type.name
    }

# Reenvia a última mensagem enviada    
def resend_message(player, message):
    message["delivered_uni"] = False
    message["delivered_broad"] = []
    send_to_next(player, message)

# Arruma os dados que foram convertidos ao enviar quando recebe
def convert_message(message):
    new_message = copy.deepcopy(message)
    new_message["destination"] = tuple(new_message["destination"])
    new_message["source"] = tuple(new_message["source"])
    
    return new_message

# Reseta o GameInfo para começar um novo round 
def reset_rounds(game_info: GameInfo):
    for i in range(len(game_info.rounds_won)):
        game_info.rounds_won[i] = 0
        
    game_info.rounds_played = 0

# Os métodos abaixo geram e enviam uma mensagem de seu tipo    
def send_receive_card(player, destination, game_info: GameInfo):
    message = generate_message(player.address, destination, generate_deck(game_info),
                                MessageType.RECEIVE_CARD, DeliverType.UNI)

    send_message(message, player.next_player_address, player.socket)
    
def send_card(player, game_info: GameInfo):
    message = generate_message(player.address, None, [None] * game_info.player_count, MessageType.SEND_CARD, DeliverType.BROAD)
    send_to_next(player, message)
    
def send_to_next(player, message):
    send_message(message, player.next_player_address, player.socket)

def send_bet(player, game_info: GameInfo):
    message = generate_message(player.address, None, game_info.players_bets, MessageType.SEND_BET, DeliverType.BROAD)
    send_to_next(player, message)
    
def send_update_points(player: Player, game_info: GameInfo):
    message = generate_message(player.address, None, game_info.rounds_won, MessageType.UPDATE_POINTS,
                               DeliverType.BROAD)
    
    send_to_next(player, message)

def send_update_game_info(player, game_info: GameInfo):
    message = generate_message(player.address, None, game_info.__dict__, MessageType.UPDATE_GAME_INFO,
                               DeliverType.BROAD)
    
    send_to_next(player, message)
    
def send_bat(player: Player):
    message = generate_message(player.address, player.next_player_address, None, MessageType.SEND_BAT,
                               DeliverType.UNI)
    
    send_to_next(player, message)

# Lógica ao receber uma mensagem do tipo receive_card (recebe o baralho para a rodada)
def interpret_receive_card(message, player: Player, all_addresses: list, game_info: GameInfo):
    converted_message = convert_message(message)
    if player.address == converted_message["destination"]:
        
        message["delivered_uni"] = True
        if game_info.player_lives[player.id] > 0: # Se o jogador ainda tiver vida, ele recebe seu baralho
            player.deck = message["data"]
            print("Recebi minhas cartas: {}".format(player.deck))

    # Se a mensagem voltou para o carteador, envia as cartas do próximo jogador a receber. Se todos receberam, define suas próprias cartas
    if player.dealer:
        next_machine_address = get_next_machine_address(all_addresses.index(converted_message["destination"]), all_addresses)
        if next_machine_address == player.address:
            print("Cartas entregues")
            if game_info.player_lives[player.id] > 0:
                player.deck = generate_deck(game_info)
                print("Recebi minhas cartas: {}".format(player.deck))
            return send_bet(player, game_info) # Carteador envia a mensagem para coletar as apostas dos jogadores
        else:
            return send_receive_card(player, next_machine_address, game_info) # Envia as cartas do próximo jogador a receber

    return send_to_next(player, message) # Se não for o carteador, só passa a mensagem para a próxima máquina

# Lógica ao receber uma mensagem do tipo send_bet
def interpret_send_bet(player: Player, message, game_info: GameInfo):
    if game_info.player_lives[player.id] > 0: # Se o jogador tiver vida, pega a aposta dele
        continue_loop = True
        while continue_loop:
            bet = int(input("Quantas rodadas você irá fazer?"))
            if bet <= game_info.rounds_to_play:
                message["data"][player.id] = bet
                continue_loop = False
            else:
                print("Valor invalido")
        
    if player.dealer == False: # Se não for o carteador, passa a mensagem para frente
        message["delivered_broad"].append(True)
        send_to_next(player, message)
    else:
        game_info.players_bets = message["data"]
        print("Apostas: {}".format(game_info.players_bets))
        send_card(player, game_info) # Se for o carteador, manda a mensagem para coletar qual carta cada máquina irá jogar
        
# Lógica ao receber uma mensagem do tipo send_card        
def interpret_send_card(player: Player, message, game_info: GameInfo):
    card_sequence = [3, 2, 1, "K", "J", "Q", 7, 6, 5, 4]
    card_naipes = ["Paus", "Copas", "Espadas", "Ouros"]
    cards_played = copy.deepcopy(message["data"])
    print("Cartas jogadas: {}".format(cards_played))
    if game_info.player_lives[player.id] > 0: # Se o jogador ainda tiver vida, coloca qual carta quer jogar na mensagem
        print("Suas cartas: {}".format(player.deck))
        continue_loop = True
        while continue_loop:
            card = input("Qual carta você quer jogar? ")
            if card != "J" and card != "Q" and card != "K":
                card = int(card)
            if 0 <= card < len(player.deck):
                message["data"][player.id] = player.deck[card]
                del player.deck[card]
                continue_loop = False    
            else:
                print("Você não tem essa carta")
    else:
        message["data"][player.id] = None
    
    
     
    if  player.dealer == False: 
        message["delivered_broad"].append(True)
        send_to_next(player, message) # Se não for o carteador, passa a mensagem para a próxima máquina
        return
    else: # Se for o carteador, computa qual jogador venceu
        biggest_card_position = 0
        for i in range(0, len(message["data"])):
            if message["data"][i] != None:
                if message["data"][biggest_card_position] == None:
                    biggest_card_position = i
                else: 
                    if card_sequence.index(message["data"][i]["number"]) < card_sequence.index(message["data"][biggest_card_position]["number"]):
                        biggest_card_position = i
                    elif card_sequence.index(message["data"][i]["number"]) == card_sequence.index(message["data"][biggest_card_position]["number"]):
                        if card_naipes.index(message["data"][i]["naipe"]) < card_naipes.index(message["data"][biggest_card_position]["naipe"]):
                            biggest_card_position = i
                
            
        print("Quem ganhou essa rodada foi o jogador {}".format(biggest_card_position))
        # Atualiza a pontuação após acabar um round
        game_info.rounds_won[biggest_card_position] += 1
        game_info.rounds_played += 1
        
        send_update_points(player, game_info) # Envia mensagem de atualização de pontuação para todas as máquinas
    
# Lógica ao receber mensagem do tipo update_points    
def interpret_update_points(player: Player, message, game_info: GameInfo):
    game_info.rounds_won = message["data"] # Atualiza as pontuações
    print("Rounds ganhos nessa rodada: {}".format(game_info.rounds_won))
    if player.dealer == False:
        message["delivered_broad"].append(True)
        send_to_next(player, message) # se não for o carteador, manda para a próxima máquina
    else:
        if game_info.rounds_played == game_info.rounds_to_play: # Se acabou a rodada
            print("Acabou a rodada")
            for i in range(len(game_info.player_lives)): # Atualiza a vida de cada jogador
                if game_info.player_lives[i] > 0:
                    game_info.player_lives[i] -= abs(game_info.players_bets[i] - game_info.rounds_won[i])
                
                if game_info.player_lives[i] <= 0:
                    game_info.players_alive[i] = None
                    
            reset_rounds(game_info) # Prepara o game_info para começar uma nova rodada
            send_update_game_info(player, game_info) # Envia o game_info atualizado para as máquinas no anel
        else:
            send_card(player, game_info)  # Se a rodada ainda não acabou, pede para os jogadores enviarem outra carta
            
    
# Lógica para atualizar o gafe_info    
def interpret_update_game_info(player: Player, game_info: GameInfo, message):
    alives = [x for x in message["data"]['players_alive'] if x != None]
    game_info.rounds_won = message["data"]["rounds_won"]
    game_info.rounds_played =  message["data"]["rounds_played"]
    
    if len(alives) == 1: # Se só tem um jogador vivo, ele venceu e começa outra partida
        print("O vencedor da partida é o jogador {}".format(alives[0]))
        print("Começando uma nova PARTIDA")
        game_info.players_alive = [x for x in range(game_info.player_count)]
        game_info.player_lives = [game_info.default_life] * game_info.player_count
    elif len(alives) == 0: # Se não tem nenhum jogador vivo, da empate e começa outra partida
        print("Empate")
        print("Começando uma nova PARTIDA")
        game_info.players_alive = [x for x in range(game_info.player_count)]
        game_info.player_lives = [game_info.default_life] * game_info.player_count
        
    else: # Se tem mais de um jogador vivo, começa outra rodada
        game_info.player_lives = message["data"]["player_lives"]
        print("Começando uma nova rodada")
        if game_info.player_lives[player.id] <= 0:
            print("Você não tem mais vida")
       
    print("Vidas: {}".format(game_info.player_lives))     
    if player.dealer == False:
        message["delivered_broad"].append(True)
        send_to_next(player, message)
    else:
        player.dealer = False
        send_bat(player) # Se for o carteador/quem ta com o bastão, manda mensagem para passar o bastão para a próxima máquina
    
def interpret_send_bat(player: Player, message, game_info: GameInfo):
    destination = tuple(message["destination"])
    
    if player.address == destination: # Se for a próxima máquina a receber o bastão, recebe o bastão
        message["delivered_uni"] = True
        player.dealer = True
        game_info.first = True
    else:
        send_to_next(player, message)
        
    
        
# define qual método de interpretação da mensagem chamar dependendo do tipo da mensagem
def interpret_message(message, player: Player, game_info: GameInfo):
    message_type = MessageType[message["type"]]
    match message_type:
        case MessageType.RECEIVE_CARD:
            return interpret_receive_card(message, player, game_info.all_addresses, game_info)
        
        case MessageType.SEND_BET:
            return interpret_send_bet(player, message, game_info)
        
        case MessageType.SEND_CARD:
            return interpret_send_card(player, message, game_info)
        
        case MessageType.UPDATE_POINTS:
            return interpret_update_points(player, message, game_info)
        
        case MessageType.UPDATE_GAME_INFO:
            return interpret_update_game_info(player, game_info, message)
        
        case MessageType.SEND_BAT:
            return interpret_send_bat(player, message, game_info)

def main():
    config_file_path = "./config.json" # arquivo de configuração
    config_file = get_config_file(config_file_path)
    addresses = get_all_addresses(config_file_path)
    game_info = GameInfo(addresses, config_file["player_lives"], config_file["rounds_to_play"])
    
    id = int(sys.argv[1]) # le qual jogador é
    print(f"Jogador {id}")
    
    player = Player(id, game_info.all_addresses[id], create_socket(game_info.all_addresses[id]),
                    get_next_machine_address(id, game_info.all_addresses))

    if player.id == 0: # se for a máquina 0, recebe o bastão/vira o carteador
        player.dealer = True
        
    while True:
        if player.dealer and game_info.first: # se for a primeira rodada da máquina como carteador, envia as cartas para as máquinas no anel
            message = generate_message(player.address, player.next_player_address, generate_deck(game_info),
                                       MessageType.RECEIVE_CARD, DeliverType.UNI)

            send_message(message, player.next_player_address, player.socket)
            game_info.first = False

        data, address = receive_message(player.socket) # recebe a mensagem
        if data:
            if player.dealer == True: # se for o carteador verifica se a mensagem chegou sem erro. se chegou sem erro, interpreta a mensagem, se não, envia de novo.
                if data["deliver_type"] == "BROAD": 
                    if len(data["delivered_broad"]) == game_info.player_count - 1:
                        interpret_message(data, player, game_info)
                    else:
                        resend_message(player, data)
                else:
                    if data["delivered_uni"] == True:
                        interpret_message(data, player, game_info)
            else:
                interpret_message(data, player, game_info)
            
if __name__ == "__main__":
    main()
