#!/usr/bin/env python3
"""
Batalha de Dados - versão com suporte a rede TCP/UDP e IPv4/IPv6
"""

import random
import os
import sys
import time
import colorama
import socket
import threading
import json
import ipaddress

colorama.init()

# ---------- Constantes de Rede ----------
DEFAULT_PORT = 12345
BUFFER_SIZE = 1024

# ---------- Utilitários ----------
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def slowprint(text, delay=0.008):
    for c in text:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    print()

# ANSI colors (com suporte colorama no Windows)
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAG = '\033[95m'
    CYAN = '\033[96m'
    GREY = '\033[90m'

def color(text, col):
    return f"{col}{text}{C.RESET}"

# ---------- Game Data ----------
CHARACTERS = {
    'Guerreiro': {'hp': 28, 'atk': 5, 'def': 2, 'desc': 'Equilibrado: dano e defesa.'},
    'Mago':      {'hp': 20, 'atk': 7, 'def': 1, 'desc': 'Alto dano, vida baixa.'},
    'Guardião':  {'hp': 34, 'atk': 4, 'def': 4, 'desc': 'Alta vida e defesa.'},
}

DICE_TYPES = {
    'd6': 6,
    'd8': 8,
    'd10': 10
}

# ---------- Rede Simples ----------
class SimpleNetwork:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.is_tcp = True
        self.peer_addr = None
        
    def is_ipv6_address(self, addr):
        try:
            ip = ipaddress.ip_address(addr)
            return ip.version == 6
        except:
            return False
    
    def create_server(self, host, port, use_tcp=True):
        self.is_tcp = use_tcp
        try:
            # Escolher família de endereços (IPv4 ou IPv6)
            if self.is_ipv6_address(host):
                family = socket.AF_INET6
            else:
                family = socket.AF_INET
                
            # Criar socket
            if use_tcp:
                self.socket = socket.socket(family, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                self.socket = socket.socket(family, socket.SOCK_DGRAM)
                
            self.socket.bind((host, port))
            
            if use_tcp:
                self.socket.listen(1)
                print(color(f"Servidor TCP criado em {host}:{port}", C.GREEN))
            else:
                print(color(f"Servidor UDP criado em {host}:{port}", C.GREEN))
                
            return True
        except Exception as e:
            print(color(f"Erro ao criar servidor: {e}", C.RED))
            return False
    
    def wait_connection(self):
        try:
            if self.is_tcp:
                print(color("Aguardando conexão TCP...", C.YELLOW))
                client_sock, addr = self.socket.accept()
                self.socket = client_sock  # Trocar pelo socket do cliente
                self.peer_addr = addr
                print(color(f"Cliente conectado: {addr[0]}:{addr[1]}", C.GREEN))
            else:
                print(color("Aguardando primeira mensagem UDP...", C.YELLOW))
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                self.peer_addr = addr
                print(color(f"Cliente UDP: {addr[0]}:{addr[1]}", C.GREEN))
                # Retornar primeira mensagem
                return data.decode('utf-8')
                
            self.connected = True
            return True
        except Exception as e:
            print(color(f"Erro na conexão: {e}", C.RED))
            return False
    
    def connect_to_server(self, host, port, use_tcp=True):
        self.is_tcp = use_tcp
        try:
            # Escolher família de endereços
            if self.is_ipv6_address(host):
                family = socket.AF_INET6
            else:
                family = socket.AF_INET
                
            if use_tcp:
                self.socket = socket.socket(family, socket.SOCK_STREAM)
                self.socket.connect((host, port))
                print(color(f"Conectado via TCP: {host}:{port}", C.GREEN))
            else:
                self.socket = socket.socket(family, socket.SOCK_DGRAM)
                self.peer_addr = (host, port)
                print(color(f"Conectado via UDP: {host}:{port}", C.GREEN))
                
            self.connected = True
            return True
        except Exception as e:
            print(color(f"Erro na conexão: {e}", C.RED))
            return False
    
    def send_message(self, message):
        if not self.connected:
            return False
        try:
            data = message.encode('utf-8')
            if self.is_tcp:
                self.socket.send(data)
            else:
                self.socket.sendto(data, self.peer_addr)
            return True
        except Exception as e:
            print(color(f"Erro ao enviar: {e}", C.RED))
            return False
    
    def receive_message(self):
        if not self.connected:
            return None
        try:
            if self.is_tcp:
                data = self.socket.recv(BUFFER_SIZE)
                return data.decode('utf-8')
            else:
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                return data.decode('utf-8')
        except Exception as e:
            print(color(f"Erro ao receber: {e}", C.RED))
            return None
    
    def close(self):
        if self.socket:
            self.socket.close()
        self.connected = False

# ---------- Player Class ----------
class Combatant:
    def __init__(self, name, kind, is_cpu=False):
        self.name = name
        self.kind = kind
        base = CHARACTERS[kind]
        self.max_hp = base['hp']
        self.hp = base['hp']
        self.atk = base['atk']
        self.defense = base['def']
        self.is_cpu = is_cpu
        self.items = {'cura': 2, 'fury': 1}
        self.buff_turns = 0
        self.debuff_turns = 0

    def alive(self):
        return self.hp > 0

    def heal(self, v):
        old = self.hp
        self.hp = min(self.max_hp, self.hp + v)
        return self.hp - old

    def take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)

    def reset_round(self):
        self.hp = self.max_hp
        self.buff_turns = 0
        self.debuff_turns = 0

# ---------- Mecânicas ----------
def roll_die(sides):
    return random.randint(1, sides)

def attack_roll(attacker, defender, dice='d6'):
    sides = DICE_TYPES.get(dice, 6)
    roll = roll_die(sides)
    crit = roll == sides
    base = attacker.atk + roll - defender.defense
    if base < 0:
        base = 0
    multiplier = 1.0
    if attacker.buff_turns > 0:
        multiplier += 0.5
    if defender.debuff_turns > 0:
        multiplier -= 0.25
    damage = int(base * multiplier)
    if crit:
        damage = int(damage * 1.5) + 1
    return roll, crit, damage

# ---------- Display ----------
def header():
    clear()
    print(color(r"""
  ____        _   _ _       _   _        ____        _     
 |  _ \      | | (_) |     | | | |      |  _ \      | |    
 | |_) | __ _| |_ _| | ___ | |_| | ___  | |_) | __ _| |__  
 |  _ < / _` | __| | |/ _ \|  _  |/ _ \ |  _ < / _` | '_ \ 
 | |_) | (_| | |_| | | (_) | | | |  __/ | |_) | (_| | |_) |
 |____/ \__,_|\__|_|_|\___/|_| |_|\___/ |____/ \__,_|_.__/ 
    """, C.CYAN))
    print(color("                 BATALHA DE DADOS...\n", C.YELLOW))

def show_stats(p1, p2):
    print(color(f" {p1.name} ({p1.kind})", C.GREEN))
    print(f"  HP: {p1.hp}/{p1.max_hp}  ATK: {p1.atk}  DEF: {p1.defense}  Items: {p1.items}")
    print()
    print(color(f" {p2.name} ({p2.kind})", C.RED))
    print(f"  HP: {p2.hp}/{p2.max_hp}  ATK: {p2.atk}  DEF: {p2.defense}  Items: {p2.items}")
    print('-' * 50)
    
def choose_character(player_label):
    header()
    slowprint(f"{player_label}, escolha seu personagem:\n", 0.003)
    keys = list(CHARACTERS.keys())
    for i, k in enumerate(keys, 1):
        v = CHARACTERS[k]
        print(f" {i}. {color(k, C.BOLD)} - HP:{v['hp']} ATK:{v['atk']} DEF:{v['def']}  - {v['desc']}")
    print()
    while True:
        choice = input("Escolha (1-{}): ".format(len(keys))).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            return keys[int(choice) - 1]
        print(color("Escolha inválida. Tente novamente.", C.RED))

def choose_mode():
    header()
    print("Modos:")
    print(" 1. Jogador vs CPU (local)")
    print(" 2. Jogador vs Jogador (local)")
    print(" 3. Hospedar partida (rede)")
    print(" 4. Conectar à partida (rede)")
    print(" 5. CPU vs CPU (teste)")
    while True:
        c = input("Escolha modo (1-5): ").strip()
        if c in ('1','2','3','4','5'):
            return c
        print(color("Escolha inválida.", C.RED))

def choose_protocol():
    header()
    print("Protocolo de Rede:")
    print(" 1. TCP (confiável)")
    print(" 2. UDP (rápido)")
    while True:
        c = input("Escolha protocolo (1-2): ").strip()
        if c == '1': return True  # TCP
        if c == '2': return False # UDP
        print(color("Escolha inválida.", C.RED))

def get_network_config():
    header()
    print("Configuração de Rede:")
    print("Exemplos de IP:")
    print("  IPv4: 127.0.0.1 (local) ou 192.168.1.100")
    print("  IPv6: ::1 (local) ou fe80::1%eth0")
    
    host = input("IP do servidor (Enter = qualquer): ").strip()
    if not host:
        host = ""
    
    port_input = input(f"Porta (Enter = {DEFAULT_PORT}): ").strip()
    try:
        port = int(port_input) if port_input else DEFAULT_PORT
    except:
        port = DEFAULT_PORT
        
    return host, port

def choose_dice():
    header()
    print("Selecione o tipo de dado para as batalhas:")
    print(" 1. d6  (padrão)")
    print(" 2. d8  (mais variabilidade)")
    print(" 3. d10 (maiores picos/crit)")
    while True:
        c = input("Escolha (1-3): ").strip()
        if c == '1': return 'd6'
        if c == '2': return 'd8'
        if c == '3': return 'd10'
        print(color("Escolha inválida.", C.RED))

# CPU decision simple AI
def cpu_choose_action(cpu, opponent):
    if cpu.hp <= cpu.max_hp * 0.35 and cpu.items['cura'] > 0:
        return 'heal'
    if cpu.items['fury'] > 0 and opponent.hp <= opponent.max_hp * 0.5 and random.random() < 0.4:
        return 'fury'
    return 'attack'

def player_choose_action(player):
    print()
    print("Ações:")
    print(" 1. Atacar")
    print(" 2. Usar item (cura/fury)")
    print(" 3. Passar (pegar foco)")
    while True:
        c = input("Escolha ação (1-3): ").strip()
        if c in ('1','2','3'):
            return c
        print(color("Escolha inválida.", C.RED))

def use_item(player):
    print()
    print("Itens disponíveis:")
    print(" 1. Cura (+10 HP) - Quantidade:", player.items['cura'])
    print(" 2. Fury (próx. ataque +50%) - Quantidade:", player.items['fury'])
    print(" 3. Voltar")
    while True:
        c = input("Escolha (1-3): ").strip()
        if c == '1':
            if player.items['cura'] <= 0:
                print(color("Sem curas restantes.", C.RED))
                return False
            healed = player.heal(10)
            player.items['cura'] -= 1
            print(color(f"{player.name} usou Cura e recuperou {healed} HP!", C.GREEN))
            time.sleep(1.2)
            return True
        if c == '2':
            if player.items['Sem aura'] <= 0:
                print(color("Sem Aura restantes.", C.RED))
                return False
            player.items['fury'] -= 1
            player.buff_turns = 2
            print(color(f"{player.name} ativou modo AURA! Próximos ataques com +50% por 2 turnos.", C.YELLOW))
            time.sleep(1.2)
            return True
        if c == '3':
            return False
        print(color("Escolha inválida.", C.RED))

# ---------- Round Logic ----------
def play_turn(attacker, defender, dice):
    if attacker.is_cpu:
        action = cpu_choose_action(attacker, defender)
        if action == 'heal':
            healed = attacker.heal(10)
            attacker.items['cura'] -= 1
            slowprint(color(f"{attacker.name} (CPU) usou Cura e recuperou {healed} HP!", C.MAG), 0.003)
            time.sleep(1)
            return
        if action == 'aura':
            attacker.items['aura'] -= 1
            attacker.buff_turns = 2
            slowprint(color(f"{attacker.name} (CPU) ativou modo AURA! +50% por 2 turnos.", C.YELLOW), 0.003)
            time.sleep(1)
            return
    else:
        choice = player_choose_action(attacker)
        if choice == '2':
            used = use_item(attacker)
            if used:
                return
        elif choice == '3':
            attacker.defense += 1
            attacker.debuff_turns = 0
            slowprint(color(f"{attacker.name} passou e aumentou DEF em 1 por uma rodada.", C.CYAN), 0.003)
            time.sleep(0.9)
            return

    # perform attack
    roll, crit, damage = attack_roll(attacker, defender, dice)
    defender.take_damage(damage)
    sroll = color(str(roll), C.YELLOW)
    sdam = color(str(damage), C.RED if damage>0 else C.GREY)
    if crit:
        slowprint(color(f"{attacker.name} rolou {sroll} (CRÍTICO!) e causou {sdam} de dano!", C.MAG), 0.002)
    else:
        slowprint(f"{attacker.name} rolou {sroll} e causou {sdam} de dano.", 0.002)
    time.sleep(0.9)

def decay_buffs(p):
    if p.buff_turns > 0:
        p.buff_turns -= 1
    if p.debuff_turns > 0:
        p.debuff_turns -= 1
    base_def = CHARACTERS[p.kind]['def']
    if p.defense > base_def + 3:
        p.defense = base_def

# ---------- Match Flow ----------
def battle(p1, p2, dice):
    round_no = 1
    while p1.alive() and p2.alive():
        header()
        print(color(f"--- Round {round_no} ---", C.BLUE))
        show_stats(p1, p2)

        # player 1 turn
        slowprint(color(f"Vez de {p1.name}!", C.GREEN), 0.002)
        play_turn(p1, p2, dice)
        decay_buffs(p1)
        if not p2.alive():
            break

        # player 2 turn
        slowprint(color(f"Vez de {p2.name}!", C.RED), 0.002)
        play_turn(p2, p1, dice)
        decay_buffs(p2)

        round_no += 1

    winner = p1 if p1.alive() else p2
    slowprint(color(f"\n>>> {winner.name} venceu a batalha! <<<\n", C.BOLD + C.GREEN if winner==p1 else C.BOLD + C.RED), 0.004)
    time.sleep(1.2)
    return winner

# Batalha em rede simplificada
def network_battle(p1, p2, dice, network, is_host):
    round_no = 1
    my_turn = is_host  # Host sempre começa
    
    while p1.alive() and p2.alive():
        header()
        print(color(f"--- Round {round_no} (Rede) ---", C.BLUE))
        show_stats(p1, p2)
        
        if my_turn:
            # Minha vez
            slowprint(color(f"SUA vez!", C.GREEN), 0.002)
            play_turn(p1, p2, dice)
            
            # Enviar resultado
            msg = f"JOGADA|{p1.hp}|{p2.hp}|{p1.items}|{p1.buff_turns}"
            network.send_message(msg)
            
        else:
            # Vez do oponente
            slowprint(color(f"Vez do OPONENTE...", C.YELLOW), 0.002)
            msg = network.receive_message()
            if not msg:
                print(color("Conexão perdida!", C.RED))
                return None
                
            # Processar jogada do oponente
            if msg.startswith("JOGADA|"):
                parts = msg.split("|")
                try:
                    p2.hp = int(parts[2])  # HP do defensor (eu)
                    # Simular que o oponente atacou
                    slowprint(color("Oponente fez sua jogada!", C.MAG), 0.002)
                except:
                    print(color("Erro na mensagem!", C.RED))
        
        decay_buffs(p1)
        decay_buffs(p2)
        my_turn = not my_turn
        round_no += 1
        time.sleep(1)
    
    winner = p1 if p1.alive() else p2
    slowprint(color(f"\n>>> {winner.name} venceu! <<<\n", C.BOLD + C.GREEN if winner==p1 else C.BOLD + C.RED), 0.004)
    return winner

# ---------- Main Menu & Loop ----------
def main():
    random.seed()
    while True:
        header()
        print("Bem-vindo à Batalha de Dados P2P!")
        print()
        print("1. Jogar")
        print("2. Instruções")
        print("3. Sair")
        choice = input("Escolha (1-3): ").strip()
        
        if choice == '3':
            slowprint("Até a próxima, guerreiro!", 0.005)
            break
            
        if choice == '2':
            header()
            print("Instruções:")
            print("- Escolha um personagem. Cada um tem HP / ATK / DEF diferentes.")
            print("- Em cada turno, escolha atacar, usar item, ou passar.")
            print("- Itens: Cura (+10 HP), Fury (+50% dano por 2 turnos).")
            print("- Dados: escolha d6/d8/d10 para rolagens. Rolagens máximas são críticos.")
            print("- Vence quem zerar o HP do oponente.")
            print()
            print("NOVOS RECURSOS DE REDE:")
            print("- Suporte a TCP (confiável) e UDP (rápido)")
            print("- Compatível com IPv4 e IPv6")
            print("- Modo hospedar: aguarda conexões")
            print("- Modo conectar: conecta a uma partida")
            input("\nPressione Enter para voltar...")
            continue
            
        if choice == '1':
            mode = choose_mode()
            dice = choose_dice()
            
            if mode in ('1', '2', '5'):
                # Modos locais (originais)
                if mode == '1':
                    kind1 = choose_character("Jogador")
                    p1 = Combatant("Você", kind1, is_cpu=False)
                    kind2 = random.choice(list(CHARACTERS.keys()))
                    p2 = Combatant("CPU", kind2, is_cpu=True)
                    slowprint(f"CPU escolheu {kind2}!", 0.003)
                    
                elif mode == '2':
                    kind1 = choose_character("Jogador 1")
                    kind2 = choose_character("Jogador 2")
                    p1 = Combatant("Jogador1", kind1, is_cpu=False)
                    p2 = Combatant("Jogador2", kind2, is_cpu=False)
                    
                else:  # mode == '5'
                    kind1 = random.choice(list(CHARACTERS.keys()))
                    kind2 = random.choice(list(CHARACTERS.keys()))
                    p1 = Combatant("CPU-A", kind1, is_cpu=True)
                    p2 = Combatant("CPU-B", kind2, is_cpu=True)
                    slowprint(f"CPU-A: {kind1} vs CPU-B: {kind2}", 0.003)
                
                input("Pressione Enter para começar...")
                score_p1 = 0
                score_p2 = 0
                
                for match in range(1,4):
                    p1.reset_round()
                    p2.reset_round()
                    header()
                    slowprint(color(f"=== Batalha {match} ===", C.CYAN), 0.003)
                    winner = battle(p1, p2, dice)
                    if winner == p1:
                        score_p1 += 1
                    else:
                        score_p2 += 1
                    slowprint(f"Placar: {p1.name} {score_p1} x {score_p2} {p2.name}\n", 0.003)
                    if score_p1 == 2 or score_p2 == 2:
                        break
                    if match < 3:
                        input("Próxima batalha: pressione Enter...")
                
                if score_p1 > score_p2:
                    slowprint(color(f"{p1.name} venceu a série!", C.GREEN), 0.003)
                else:
                    slowprint(color(f"{p2.name} venceu a série!", C.GREEN), 0.003)
                input("Pressione Enter para voltar ao menu...")
                
            else:
                # Modos de rede (3 = hospedar, 4 = conectar)
                use_tcp = choose_protocol()
                protocol_name = "TCP" if use_tcp else "UDP"
                
                network = SimpleNetwork()
                
                try:
                    if mode == '3':  # Hospedar
                        host, port = get_network_config()
                        kind1 = choose_character("Seu personagem")
                        
                        if not network.create_server(host or "", port, use_tcp):
                            input("Erro ao criar servidor. Pressione Enter...")
                            continue
                            
                        slowprint(f"Aguardando conexão {protocol_name}...", 0.003)
                        result = network.wait_connection()
                        
                        if not result:
                            input("Erro na conexão. Pressione Enter...")
                            continue
                            
                        # Enviar info do jogo
                        game_info = f"GAME|{kind1}|{dice}"
                        network.send_message(game_info)
                        
                        # Receber info do oponente
                        opp_msg = network.receive_message()
                        if opp_msg and opp_msg.startswith("GAME|"):
                            parts = opp_msg.split("|")
                            opp_char = parts[1] if len(parts) > 1 else "Guerreiro"
                        else:
                            opp_char = "Guerreiro"
                        
                        p1 = Combatant("Você", kind1)
                        p2 = Combatant("Oponente", opp_char)
                        
                        slowprint(f"Oponente escolheu: {opp_char}", 0.003)
                        input("Pressione Enter para começar batalha em rede...")
                        
                        winner = network_battle(p1, p2, dice, network, True)
                        
                    else:  # mode == '4' - Conectar
                        host, port = get_network_config()
                        if not host:
                            host = "127.0.0.1"
                            
                        kind1 = choose_character("Seu personagem")
                        
                        if not network.connect_to_server(host, port, use_tcp):
                            input("Erro na conexão. Pressione Enter...")
                            continue
                            
                        # Receber info do host
                        host_msg = network.receive_message()
                        if host_msg and host_msg.startswith("GAME|"):
                            parts = host_msg.split("|")
                            host_char = parts[1] if len(parts) > 1 else "Guerreiro"
                            dice = parts[2] if len(parts) > 2 else dice
                        else:
                            host_char = "Guerreiro"
                        
                        # Enviar nossa info
                        game_info = f"GAME|{kind1}|{dice}"
                        network.send_message(game_info)
                        
                        p1 = Combatant("Você", kind1)
                        p2 = Combatant("Host", host_char)
                        
                        slowprint(f"Host escolheu: {host_char}", 0.003)
                        slowprint(f"Usando dados: {dice}", 0.003)
                        input("Pressione Enter para começar batalha em rede...")
                        
                        winner = network_battle(p1, p2, dice, network, False)
                    
                    input("Pressione Enter para voltar ao menu...")
                    
                except Exception as e:
                    print(color(f"Erro na partida em rede: {e}", C.RED))
                    input("Pressione Enter...")
                finally:
                    network.close()
        else:
            print(color("Escolha inválida.", C.RED))
            time.sleep(0.6)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaindo... até logo!")
        sys.exit(0)