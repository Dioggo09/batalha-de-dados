#!/usr/bin/env python3
"""
Batalha de Dados - versão com colorama para rodar no CMD/terminal.
"""

import random
import os
import sys
import time
import colorama
colorama.init()

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
 |____/ \__,_|\__|_|_|\___/|_| |_|\___| |____/ \__,_|_.__/ 
    """, C.CYAN))
    print(color("                 BATALHA DE DADOS\n", C.YELLOW))

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
    print(" 1. Jogador vs CPU")
    print(" 2. Jogador vs Jogador (mesmo teclado)")
    print(" 3. CPU vs CPU (teste automático)")
    while True:
        c = input("Escolha modo (1-3): ").strip()
        if c in ('1','2','3'):
            return c
        print(color("Escolha inválida.", C.RED))

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
    # if low HP and has heal -> heal
    if cpu.hp <= cpu.max_hp * 0.35 and cpu.items['cura'] > 0:
        return 'heal'
    # if has fury and opponent HP low -> fury (burst)
    if cpu.items['fury'] > 0 and opponent.hp <= opponent.max_hp * 0.5 and random.random() < 0.4:
        return 'fury'
    # otherwise attack
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
            if player.items['fury'] <= 0:
                print(color("Sem Fury restantes.", C.RED))
                return False
            player.items['fury'] -= 1
            player.buff_turns = 2  # duas rodadas com buff
            print(color(f"{player.name} ativou FURY! Próximos ataques com +50% por 2 turnos.", C.YELLOW))
            time.sleep(1.2)
            return True
        if c == '3':
            return False
        print(color("Escolha inválida.", C.RED))

# ---------- Round Logic ----------
def play_turn(attacker, defender, dice):
    # attacker decides action
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
            slowprint(color(f"{attacker.name} (CPU) ativou FURY! +50% por 2 turnos.", C.YELLOW), 0.003)
            time.sleep(1)
            return
        # else attack
    else:
        choice = player_choose_action(attacker)
        if choice == '2':
            used = use_item(attacker)
            if used:
                return
            # fallback to attack if didn't use
        elif choice == '3':
            # passar = ganha um pequeno buff (defesa aumentada temporariamente)
            attacker.defense += 1
            attacker.debuff_turns = 0
            slowprint(color(f"{attacker.name} passou e aumentou DEF em 1 por uma rodada.", C.CYAN), 0.003)
            time.sleep(0.9)
            return
        # else continue to attack

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
    # If someone used pass and increased defense temporarily, revert it here:
    # For simplicity, we do not track the exact pass-turn - but we can clip defense to base.
    base_def = CHARACTERS[p.kind]['def']
    if p.defense > base_def + 3:  # safety cap
        p.defense = base_def

# ---------- Match Flow ----------
def battle(p1, p2, dice):
    # returns winner name
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

# ---------- Main Menu & Loop ----------
def main():
    random.seed()  # init RNG
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
            print("- Em cada turno, escolha atacar, usar item, ou passar.")
            print("- Itens: Cura (+10 HP), Fury (+50% dano por 2 turnos).")
            print("- Dados: escolha d6/d8/d10 para rolagens. Rolagens máximas são críticos.")
            print("- Vence quem zerar o HP do oponente.")
            input("\nPressione Enter para voltar...")
            continue
        if choice == '1':
            mode = choose_mode()
            dice = choose_dice()
            # prepare combatants
            if mode == '1':
                kind1 = choose_character("Jogador")
                p1 = Combatant("Você", kind1, is_cpu=False)
                # CPU pick random
                kind2 = random.choice(list(CHARACTERS.keys()))
                p2 = Combatant("CPU", kind2, is_cpu=True)
                slowprint(f"CPU escolheu {kind2}!", 0.003)
                input("Pressione Enter para começar a melhor de 3...")
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
                    slowprint(f"Placar: Você {score_p1} x {score_p2} CPU\n", 0.003)
                    if score_p1 == 2 or score_p2 == 2:
                        break
                    input("Próxima batalha: pressione Enter...")
                if score_p1 > score_p2:
                    slowprint(color("Parabéns! Você venceu a série!", C.GREEN), 0.003)
                else:
                    slowprint(color("CPU venceu a série. Tente de novo!", C.RED), 0.003)
                input("Pressione Enter para voltar ao menu...")
            elif mode == '2':
                kind1 = choose_character("Jogador 1")
                kind2 = choose_character("Jogador 2")
                p1 = Combatant("Jogador1", kind1, is_cpu=False)
                p2 = Combatant("Jogador2", kind2, is_cpu=False)
                input("Pressione Enter para começar (melhor de 3)...")
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
                    slowprint(f"Placar: Jogador1 {score_p1} x {score_p2} Jogador2\n", 0.003)
                    if score_p1 == 2 or score_p2 == 2:
                        break
                    input("Próxima batalha: pressione Enter...")
                if score_p1 > score_p2:
                    slowprint(color("Jogador1 venceu a série!", C.GREEN), 0.003)
                else:
                    slowprint(color("Jogador2 venceu a série!", C.GREEN), 0.003)
                input("Pressione Enter para voltar ao menu...")
            else:  # CPU vs CPU
                kind1 = random.choice(list(CHARACTERS.keys()))
                kind2 = random.choice(list(CHARACTERS.keys()))
                p1 = Combatant("CPU-A", kind1, is_cpu=True)
                p2 = Combatant("CPU-B", kind2, is_cpu=True)
                slowprint(f"CPU-A: {kind1} vs CPU-B: {kind2}", 0.003)
                input("Pressione Enter para iniciar simulação (melhor de 3)...")
                score_p1 = 0
                score_p2 = 0
                for match in range(1,4):
                    p1.reset_round()
                    p2.reset_round()
                    header()
                    slowprint(color(f"=== Simulação {match} ===", C.CYAN), 0.003)
                    winner = battle(p1, p2, dice)
                    if winner == p1:
                        score_p1 += 1
                    else:
                        score_p2 += 1
                    slowprint(f"Placar: CPU-A {score_p1} x {score_p2} CPU-B\n", 0.003)
                    if score_p1 == 2 or score_p2 == 2:
                        break
                    time.sleep(0.8)
                slowprint(color("Simulação finalizada.", C.YELLOW), 0.003)
                input("Pressione Enter para voltar ao menu...")
        else:
            print(color("Escolha inválida.", C.RED))
            time.sleep(0.6)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaindo... até logo!")
        sys.exit(0)
