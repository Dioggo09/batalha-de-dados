#!/usr/bin/env python3
"""
Batalha de Dados - versão com suporte a rede TCP/UDP e IPv4/IPv6
Melhorias adicionadas:
- Interface melhorada para escolher protocolo e endereço
- Protocolo de camada de aplicação estruturado
- Modo cliente-servidor aprimorado
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
import struct
from enum import Enum

colorama.init()

# ---------- Constantes de Rede ----------
DEFAULT_PORT = 12345
BUFFER_SIZE = 4096
PROTOCOL_VERSION = "1.0"
MESSAGE_HEADER_SIZE = 8

# ---------- Protocolo de Camada de Aplicação ----------
class MessageType(Enum):
    HANDSHAKE = 1
    GAME_CONFIG = 2
    CHARACTER_SELECT = 3
    GAME_STATE = 4
    PLAYER_ACTION = 5
    TURN_RESULT = 6
    GAME_END = 7
    HEARTBEAT = 8
    ERROR = 9

class GameProtocol:
    @staticmethod
    def encode_message(msg_type, data):
        """Codifica mensagem no protocolo de aplicação"""
        try:
            message = {
                'type': msg_type.value,
                'data': data,
                'timestamp': time.time(),
                'version': PROTOCOL_VERSION
            }
            
            json_data = json.dumps(message)
            data_bytes = json_data.encode('utf-8')
            data_size = len(data_bytes)
            
            # Header: tamanho (4 bytes) + tipo (4 bytes)
            header = struct.pack('!II', data_size, msg_type.value)
            
            return header + data_bytes
            
        except Exception as e:
            print(color(f"Erro ao codificar mensagem: {e}", C.RED))
            return b""
    
    @staticmethod
    def decode_message(data):
        """Decodifica mensagem do protocolo"""
        try:
            if len(data) < MESSAGE_HEADER_SIZE:
                return None
                
            # Ler header
            data_size, msg_type = struct.unpack('!II', data[:MESSAGE_HEADER_SIZE])
            
            if len(data) < MESSAGE_HEADER_SIZE + data_size:
                return None
                
            # Ler dados
            json_data = data[MESSAGE_HEADER_SIZE:MESSAGE_HEADER_SIZE + data_size].decode('utf-8')
            parsed = json.loads(json_data)
            
            return {
                'type': MessageType(parsed['type']),
                'data': parsed['data'],
                'timestamp': parsed['timestamp'],
                'version': parsed['version']
            }
            
        except Exception as e:
            print(color(f"Erro ao decodificar mensagem: {e}", C.RED))
            return None

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

# ---------- Rede Aprimorada ----------
class AdvancedNetwork:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.is_tcp = True
        self.peer_addr = None
        self.buffer = b""
        
    def is_ipv6_address(self, addr):
        try:
            ip = ipaddress.ip_address(addr)
            return ip.version == 6
        except:
            return False
    
    def create_server(self, host, port, use_tcp=True):
        """Cria servidor com protocolo cliente-servidor"""
        self.is_tcp = use_tcp
        try:
            # Escolher família de endereços (IPv4 ou IPv6)
            if host and self.is_ipv6_address(host):
                family = socket.AF_INET6
                if not host: host = "::"
            else:
                family = socket.AF_INET
                if not host: host = "0.0.0.0"
                
            # Criar socket
            if use_tcp:
                self.socket = socket.socket(family, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind((host, port))
                self.socket.listen(1)
                print(color(f"Servidor TCP criado em {host}:{port}", C.GREEN))
            else:
                self.socket = socket.socket(family, socket.SOCK_DGRAM)
                self.socket.bind((host, port))
                print(color(f"Servidor UDP criado em {host}:{port}", C.GREEN))
                
            return True
        except Exception as e:
            print(color(f"Erro ao criar servidor: {e}", C.RED))
            return False
    
    def wait_connection(self):
        """Aguarda conexão com handshake do protocolo"""
        try:
            if self.is_tcp:
                print(color("Aguardando conexão TCP...", C.YELLOW))
                client_sock, addr = self.socket.accept()
                self.socket = client_sock
                self.peer_addr = addr
                print(color(f"Cliente conectado: {addr[0]}:{addr[1]}", C.GREEN))
                
                # Handshake do protocolo
                return self._perform_handshake_server()
                
            else:
                print(color("Aguardando primeira mensagem UDP...", C.YELLOW))
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                self.peer_addr = addr
                print(color(f"Cliente UDP: {addr[0]}:{addr[1]}", C.GREEN))
                
                # Processar handshake UDP
                msg = GameProtocol.decode_message(data)
                if msg and msg['type'] == MessageType.HANDSHAKE:
                    self.connected = True
                    # Responder handshake
                    response = GameProtocol.encode_message(
                        MessageType.HANDSHAKE,
                        {'version': PROTOCOL_VERSION, 'status': 'accepted'}
                    )
                    self.socket.sendto(response, addr)
                    return True
                    
        except Exception as e:
            print(color(f"Erro na conexão: {e}", C.RED))
            return False
    
    def connect_to_server(self, host, port, use_tcp=True):
        """Conecta ao servidor com handshake do protocolo"""
        self.is_tcp = use_tcp
        try:
            # Escolher família
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
                
            # Handshake do protocolo
            return self._perform_handshake_client()
            
        except Exception as e:
            print(color(f"Erro na conexão: {e}", C.RED))
            return False
    
    def _perform_handshake_server(self):
        """Handshake do servidor usando protocolo de aplicação"""
        try:
            # Receber handshake do cliente
            data = self._receive_raw()
            if not data:
                return False
                
            msg = GameProtocol.decode_message(data)
            if not msg or msg['type'] != MessageType.HANDSHAKE:
                return False
                
            client_version = msg['data'].get('version', '0.0')
            print(color(f"Handshake recebido (versão {client_version})", C.CYAN))
            
            # Responder handshake
            response = GameProtocol.encode_message(
                MessageType.HANDSHAKE,
                {
                    'version': PROTOCOL_VERSION,
                    'status': 'accepted',
                    'server_info': 'Batalha de Dados Server'
                }
            )
            
            if self.is_tcp:
                self.socket.sendall(response)
            else:
                self.socket.sendto(response, self.peer_addr)
                
            self.connected = True
            print(color("Handshake concluído!", C.GREEN))
            return True
            
        except Exception as e:
            print(color(f"Erro no handshake: {e}", C.RED))
            return False
    
    def _perform_handshake_client(self):
        """Handshake do cliente usando protocolo de aplicação"""
        try:
            # Enviar handshake
            handshake = GameProtocol.encode_message(
                MessageType.HANDSHAKE,
                {
                    'version': PROTOCOL_VERSION,
                    'client_info': 'Batalha de Dados Client'
                }
            )
            
            if self.is_tcp:
                self.socket.sendall(handshake)
            else:
                self.socket.sendto(handshake, self.peer_addr)
                
            # Receber resposta
            data = self._receive_raw()
            if not data:
                return False
                
            response = GameProtocol.decode_message(data)
            if not response or response['type'] != MessageType.HANDSHAKE:
                return False
                
            if response['data'].get('status') != 'accepted':
                print(color("Handshake rejeitado pelo servidor", C.RED))
                return False
                
            self.connected = True
            server_version = response['data'].get('version', '0.0')
            print(color(f"Handshake aceito (servidor v{server_version})", C.GREEN))
            return True
            
        except Exception as e:
            print(color(f"Erro no handshake: {e}", C.RED))
            return False
    
    def send_message(self, msg_type, data):
        """Envia mensagem usando protocolo de aplicação"""
        if not self.connected:
            return False
            
        try:
            message = GameProtocol.encode_message(msg_type, data)
            if not message:
                return False
                
            if self.is_tcp:
                self.socket.sendall(message)
            else:
                self.socket.sendto(message, self.peer_addr)
                
            return True
            
        except Exception as e:
            print(color(f"Erro ao enviar: {e}", C.RED))
            self.connected = False
            return False
    
    def receive_message(self):
        """Recebe mensagem usando protocolo de aplicação"""
        if not self.connected:
            return None
            
        try:
            data = self._receive_raw()
            if not data:
                return None
                
            return GameProtocol.decode_message(data)
            
        except Exception as e:
            print(color(f"Erro ao receber: {e}", C.RED))
            self.connected = False
            return None
    
    def _receive_raw(self):
        """Recebe dados brutos do socket"""
        try:
            if self.is_tcp:
                # Para TCP, ler header primeiro
                while len(self.buffer) < MESSAGE_HEADER_SIZE:
                    chunk = self.socket.recv(BUFFER_SIZE)
                    if not chunk:
                        return b""
                    self.buffer += chunk
                
                # Ler tamanho da mensagem
                data_size = struct.unpack('!I', self.buffer[:4])[0]
                total_size = MESSAGE_HEADER_SIZE + data_size
                
                # Ler resto da mensagem
                while len(self.buffer) < total_size:
                    chunk = self.socket.recv(BUFFER_SIZE)
                    if not chunk:
                        return b""
                    self.buffer += chunk
                
                # Extrair mensagem completa
                message_data = self.buffer[:total_size]
                self.buffer = self.buffer[total_size:]
                
                return message_data
            else:
                # UDP recebe mensagem completa
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                return data
                
        except Exception as e:
            print(color(f"Erro ao receber dados: {e}", C.RED))
            return b""
    
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

    def to_dict(self):
        """Converte para dicionário para transmissão em rede"""
        return {
            'name': self.name,
            'kind': self.kind,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'atk': self.atk,
            'defense': self.defense,
            'items': self.items,
            'buff_turns': self.buff_turns,
            'debuff_turns': self.debuff_turns
        }
    
    def from_dict(self, data):
        """Atualiza estado a partir de dicionário"""
        self.hp = data.get('hp', self.hp)
        self.items = data.get('items', self.items)
        self.buff_turns = data.get('buff_turns', self.buff_turns)
        self.debuff_turns = data.get('debuff_turns', self.debuff_turns)

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
________  .____________ ___________  __      __  _____ __________  _________
\______ \ |   \_   ___ \\_   _____/ /  \    /  \/  _  \\______   \/   _____/
 |    |  \|   /    \  \/ |    __)_  \   \/\/   /  /_\  \|       _/\_____  \ 
 |    `   \   \     \____|        \  \        /    |    \    |   \/        \
/_______  /___|\______  /_______  /   \__/\  /\____|__  /____|_  /_______  /
        \/            \/        \/         \/         \/       \/        \/ 
    """, C.CYAN))
    print(color("            BATALHA DE DADOS...\n", C.YELLOW))

def show_stats(p1, p2):
    print(color(f" {p1.name} ({p1.kind})", C.GREEN))
    print(f"  HP: {p1.hp}/{p1.max_hp}  ATK: {p1.atk}  DEF: {p1.defense}  Items: {p1.items}")
    if p1.buff_turns > 0:
        print(color(f"  BUFF ativo por {p1.buff_turns} turnos", C.YELLOW))
    print()
    print(color(f" {p2.name} ({p2.kind})", C.RED))
    print(f"  HP: {p2.hp}/{p2.max_hp}  ATK: {p2.atk}  DEF: {p2.defense}  Items: {p2.items}")
    if p2.buff_turns > 0:
        print(color(f"  BUFF ativo por {p2.buff_turns} turnos", C.YELLOW))
    print('=' * 60)

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
    print("Modos de Jogo:")
    print(" 1. Jogador vs CPU (local)")
    print(" 2. Jogador vs Jogador (local)")
    print(" 3. Hospedar partida (servidor)")
    print(" 4. Conectar à partida (cliente)")
    print(" 5. CPU vs CPU (demonstração)")
    while True:
        c = input("Escolha modo (1-5): ").strip()
        if c in ('1','2','3','4','5'):
            return c
        print(color("Escolha inválida.", C.RED))

def choose_protocol():
    """Interface melhorada para escolher protocolo"""
    header()
    print(color("CONFIGURAÇÃO DE PROTOCOLO DE REDE", C.BOLD))
    print("="*50)
    print()
    print("Protocolos disponíveis:")
    print(f" 1. {color('TCP', C.GREEN)} (Transmission Control Protocol)")
    print("    • Conexão confiável e ordenada")
    print("    • Garantia de entrega das mensagens")
    print("    • Melhor para jogos que precisam de sincronização")
    print("    • Recomendado para este jogo")
    print()
    print(f" 2. {color('UDP', C.YELLOW)} (User Datagram Protocol)")
    print("    • Conexão rápida mas não confiável")
    print("    • Sem garantia de entrega")
    print("    • Melhor para jogos em tempo real")
    print("    • Experimental para este jogo")
    print()
    print(color("Dica: TCP é recomendado para melhor experiência", C.CYAN))
    print()
    
    while True:
        c = input("Escolha protocolo (1-2): ").strip()
        if c == '1': 
            print(color("TCP selecionado - conexão confiável", C.GREEN))
            return True
        if c == '2': 
            print(color("UDP selecionado - conexão rápida", C.YELLOW))
            return False
        print(color("Escolha inválida.", C.RED))

def get_network_config(is_server=True):
    """Interface melhorada para configuração de endereço"""
    header()
    mode_text = "SERVIDOR" if is_server else "CLIENTE"
    print(color(f"CONFIGURAÇÃO DE ENDEREÇO - MODO {mode_text}", C.BOLD))
    print("="*50)
    print()
    
    # Mostrar informações sobre tipos de endereço
    print("Tipos de endereço suportados:")
    print()
    print(color("IPv4:", C.CYAN))
    print("  • 127.0.0.1 ou localhost (local)")
    print("  • 192.168.x.x (rede local/LAN)")
    print("  • IP público (internet)")
    print()
    print(color("IPv6:", C.CYAN))
    print("  • ::1 (local)")
    print("  • fe80::x (link-local)")
    print("  • Endereços globais")
    print()
    
    if is_server:
        print(color("Configuração do Servidor:", C.GREEN))
        print("• Deixe vazio para aceitar conexões em todos os endereços")
        print("• Especifique um IP para limitar a interface")
        host = input("IP do servidor (Enter = todos): ").strip()
        if not host:
            print(color("→ Servidor aceitará conexões em todos os endereços", C.GREY))
        else:
            # Validar endereço
            try:
                ip = ipaddress.ip_address(host)
                ip_type = "IPv6" if ip.version == 6 else "IPv4"
                print(color(f"→ Endereço {ip_type} válido: {host}", C.GREEN))
            except:
                print(color(f"→ Aviso: '{host}' pode não ser um IP válido", C.YELLOW))
    else:
        print(color("Configuração do Cliente:", C.GREEN))
        print("• Digite o IP do servidor para conectar")
        host = input("IP do servidor: ").strip()
        if not host:
            host = "127.0.0.1"
            print(color("→ Usando localhost (127.0.0.1)", C.GREY))
        else:
            # Validar endereço
            try:
                ip = ipaddress.ip_address(host)
                ip_type = "IPv6" if ip.version == 6 else "IPv4"
                print(color(f"→ Conectando via {ip_type}: {host}", C.GREEN))
            except:
                print(color(f"→ Tentando resolver: {host}", C.YELLOW))
    
    print()
    port_input = input(f"Porta (1024-65535, Enter = {DEFAULT_PORT}): ").strip()
    try:
        port = int(port_input) if port_input else DEFAULT_PORT
        if port < 1024 or port > 65535:
            print(color("Aviso: porta fora do range recomendado (1024-65535)", C.YELLOW))
        else:
            print(color(f"→ Porta configurada: {port}", C.GREEN))
    except:
        port = DEFAULT_PORT
        print(color(f"→ Usando porta padrão: {DEFAULT_PORT}", C.GREY))
        
    return host, port

def choose_dice():
    header()
    print("Selecione o tipo de dado para as batalhas:")
    print(" 1. d6  (padrão - equilibrado)")
    print(" 2. d8  (mais variabilidade)")
    print(" 3. d10 (maiores picos e críticos)")
    print()
    print(color("Dica: Dados maiores = mais variação nos resultados", C.CYAN))
    while True:
        c = input("Escolha (1-3): ").strip()
        if c == '1': return 'd6'
        if c == '2': return 'd8'
        if c == '3': return 'd10'
        print(color("Escolha inválida.", C.RED))

# CPU AI
def cpu_choose_action(cpu, opponent):
    if cpu.hp <= cpu.max_hp * 0.35 and cpu.items['cura'] > 0:
        return 'heal'
    if cpu.items['fury'] > 0 and opponent.hp <= opponent.max_hp * 0.5 and random.random() < 0.4:
        return 'fury'
    return 'attack'

def player_choose_action(player):
    print()
    print("Ações disponíveis:")
    print(" 1. Atacar")
    print(" 2. Usar item")
    print(" 3. Defender (passa o turno, +1 DEF)")
    while True:
        c = input("Escolha ação (1-3): ").strip()
        if c in ('1','2','3'):
            return c
        print(color("Escolha inválida.", C.RED))

def use_item(player):
    print()
    print("Itens disponíveis:")
    print(f" 1. Cura (+10 HP) - Restante: {player.items['cura']}")
    print(f" 2. Fury (+50% dano, 2 turnos) - Restante: {player.items['fury']}")
    print(" 3. Voltar")
    while True:
        c = input("Escolha item (1-3): ").strip()
        if c == '1':
            if player.items['cura'] <= 0:
                print(color("Sem curas restantes.", C.RED))
                continue
            healed = player.heal(10)
            player.items['cura'] -= 1
            print(color(f"{player.name} usou Cura e recuperou {healed} HP!", C.GREEN))
            time.sleep(1.2)
            return True
        if c == '2':
            if player.items['fury'] <= 0:
                print(color("Sem Fury restantes.", C.RED))
                continue
            player.items['fury'] -= 1
            player.buff_turns = 2
            print(color(f"{player.name} ativou FURY! Próximos ataques +50% por 2 turnos!", C.YELLOW))
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
        if action == 'fury':
            attacker.items['fury'] -= 1
            attacker.buff_turns = 2
            slowprint(color(f"{attacker.name} (CPU) ativou modo FURY! +50% por 2 turnos.", C.YELLOW), 0.003)
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
            slowprint(color(f"{attacker.name} defendeu e aumentou DEF em 1.", C.CYAN), 0.003)
            time.sleep(0.9)
            return

    # Realizar ataque
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

        # Turno jogador 1
        slowprint(color(f"Vez de {p1.name}!", C.GREEN), 0.002)
        play_turn(p1, p2, dice)
        decay_buffs(p1)
        if not p2.alive():
            break

        # Turno jogador 2
        slowprint(color(f"Vez de {p2.name}!", C.RED), 0.002)
        play_turn(p2, p1, dice)
        decay_buffs(p2)

        round_no += 1

    winner = p1 if p1.alive() else p2
    slowprint(color(f"\n>>> {winner.name} venceu a batalha! <<<\n", C.BOLD + C.GREEN if winner==p1 else C.BOLD + C.RED), 0.004)
    time.sleep(1.2)
    return winner

# Batalha em rede usando protocolo de aplicação
def network_battle(p1, p2, dice, network, is_host):
    round_no = 1
    my_turn = is_host  # Host sempre começa
    
    # Sincronizar estado inicial usando protocolo
    game_state_data = {
        'round': round_no,
        'players': [p1.to_dict(), p2.to_dict()],
        'current_player': 0 if my_turn else 1,
        'dice': dice
    }
    network.send_message(MessageType.GAME_STATE, game_state_data)
    
    while p1.alive() and p2.alive():
        header()
        print(color(f"--- Round {round_no} (Rede) ---", C.BLUE))
        show_stats(p1, p2)
        
        if my_turn:
            # Minha vez
            slowprint(color("SUA VEZ!", C.GREEN), 0.002)
            
            # Executar ação
            if p1.is_cpu:
                action = cpu_choose_action(p1, p2)
                if action == 'heal' and p1.items['cura'] > 0:
                    healed = p1.heal(10)
                    p1.items['cura'] -= 1
                    action_data = {'type': 'heal', 'amount': healed}
                elif action == 'fury' and p1.items['fury'] > 0:
                    p1.items['fury'] -= 1
                    p1.buff_turns = 2
                    action_data = {'type': 'fury', 'turns': 2}
                else:
                    roll, crit, damage = attack_roll(p1, p2, dice)
                    p2.take_damage(damage)
                    action_data = {'type': 'attack', 'roll': roll, 'crit': crit, 'damage': damage}
            else:
                choice = player_choose_action(p1)
                if choice == '2':
                    if use_item(p1):
                        action_data = {'type': 'item_used'}
                    else:
                        continue
                elif choice == '3':
                    p1.defense += 1
                    action_data = {'type': 'defend', 'def_bonus': 1}
                else:
                    roll, crit, damage = attack_roll(p1, p2, dice)
                    p2.take_damage(damage)
                    action_data = {'type': 'attack', 'roll': roll, 'crit': crit, 'damage': damage}
            
            # Enviar resultado da ação usando protocolo
            turn_result_data = {
                'round': round_no,
                'player': 0,
                'action': action_data,
                'players_state': [p1.to_dict(), p2.to_dict()]
            }
            
            if not network.send_message(MessageType.TURN_RESULT, turn_result_data):
                print(color("Erro ao enviar jogada!", C.RED))
                return None
                
        else:
            # Vez do oponente
            slowprint(color("Aguardando jogada do oponente...", C.YELLOW), 0.002)
            
            msg = network.receive_message()
            if not msg:
                print(color("Conexão perdida!", C.RED))
                return None
            
            if msg['type'] == MessageType.TURN_RESULT:
                # Processar jogada do oponente
                players_data = msg['data'].get('players_state', [])
                if len(players_data) >= 2:
                    # Atualizar estados (invertidos porque sou o cliente)
                    p1.from_dict(players_data[1])
                    p2.from_dict(players_data[0])
                    
                action = msg['data'].get('action', {})
                action_type = action.get('type', '')
                
                if action_type == 'attack':
                    roll = action.get('roll', 1)
                    crit = action.get('crit', False)
                    damage = action.get('damage', 0)
                    if crit:
                        slowprint(color(f"Oponente rolou {roll} (CRÍTICO!) e causou {damage} de dano!", C.MAG), 0.002)
                    else:
                        slowprint(f"Oponente rolou {roll} e causou {damage} de dano.", 0.002)
                elif action_type == 'heal':
                    amount = action.get('amount', 0)
                    slowprint(color(f"Oponente se curou em {amount} HP!", C.GREEN), 0.002)
                elif action_type == 'fury':
                    slowprint(color("Oponente ativou FURY!", C.YELLOW), 0.002)
                elif action_type == 'defend':
                    slowprint(color("Oponente defendeu!", C.CYAN), 0.002)
                    
            elif msg['type'] == MessageType.GAME_END:
                winner_data = msg['data'].get('winner')
                print(color(f"{winner_data} venceu a partida!", C.YELLOW))
                return None
        
        # Verificar fim do jogo
        if not p1.alive() or not p2.alive():
            winner = p1 if p1.alive() else p2
            
            # Notificar fim do jogo usando protocolo
            end_data = {'winner': winner.name}
            network.send_message(MessageType.GAME_END, end_data)
            
            slowprint(color(f"\n>>> {winner.name} venceu a batalha! <<<\n", C.BOLD + C.GREEN), 0.004)
            return winner
        
        # Aplicar efeitos de fim de turno
        decay_buffs(p1)
        decay_buffs(p2)
        
        # Alternar turno
        my_turn = not my_turn
        if my_turn:
            round_no += 1
            
        time.sleep(1)

# ---------- Main Menu & Loop ----------
def main():
    random.seed()
    while True:
        header()
        print("Bem-vindo à Batalha de Dados!")
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
            print("- Em cada turno, escolha atacar, usar item, ou defender.")
            print("- Itens: Cura (+10 HP), Fury (+50% dano por 2 turnos).")
            print("- Dados: escolha d6/d8/d10 para rolagens. Rolagens máximas são críticos.")
            print("- Vence quem zerar o HP do oponente.")
            print()
            print("RECURSOS DE REDE:")
            print("- Suporte a TCP (confiável) e UDP (rápido)")
            print("- Compatível com IPv4 e IPv6")
            print("- Protocolo de aplicação estruturado")
            print("- Modo cliente-servidor aprimorado")
            print("- Sincronização automática de estado")
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
                # Modos de rede com protocolo de aplicação
                use_tcp = choose_protocol()
                
                network = AdvancedNetwork()
                
                try:
                    if mode == '3':  # Hospedar (servidor)
                        host, port = get_network_config(is_server=True)
                        kind1 = choose_character("Seu personagem")
                        
                        if not network.create_server(host or "", port, use_tcp):
                            input("Erro ao criar servidor. Pressione Enter...")
                            continue
                            
                        slowprint("Aguardando conexão...", 0.003)
                        if not network.wait_connection():
                            input("Erro na conexão. Pressione Enter...")
                            continue
                        
                        # Trocar informações do jogo usando protocolo
                        game_info = {
                            'host_character': kind1,
                            'dice_type': dice,
                            'protocol_version': PROTOCOL_VERSION
                        }
                        network.send_message(MessageType.GAME_CONFIG, game_info)
                        
                        # Receber resposta do cliente
                        client_msg = network.receive_message()
                        if client_msg and client_msg['type'] == MessageType.CHARACTER_SELECT:
                            opp_char = client_msg['data'].get('character', 'Guerreiro')
                        else:
                            opp_char = 'Guerreiro'
                        
                        p1 = Combatant("Você", kind1)
                        p2 = Combatant("Oponente", opp_char)
                        
                        slowprint(f"Oponente escolheu: {opp_char}", 0.003)
                        input("Pressione Enter para começar batalha em rede...")
                        
                        winner = network_battle(p1, p2, dice, network, True)
                        
                    else:  # mode == '4' - Conectar (cliente)
                        host, port = get_network_config(is_server=False)
                        if not host:
                            host = "127.0.0.1"
                            
                        kind1 = choose_character("Seu personagem")
                        
                        if not network.connect_to_server(host, port, use_tcp):
                            input("Erro na conexão. Pressione Enter...")
                            continue
                            
                        # Receber configuração do host
                        host_msg = network.receive_message()
                        if host_msg and host_msg['type'] == MessageType.GAME_CONFIG:
                            host_char = host_msg['data'].get('host_character', 'Guerreiro')
                            dice = host_msg['data'].get('dice_type', dice)
                            host_version = host_msg['data'].get('protocol_version', '1.0')
                            print(color(f"Protocolo do servidor: v{host_version}", C.CYAN))
                        else:
                            host_char = 'Guerreiro'
                        
                        # Enviar seleção de personagem
                        char_data = {'character': kind1}
                        network.send_message(MessageType.CHARACTER_SELECT, char_data)
                        
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