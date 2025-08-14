import random

def roll_dice():
    return random.randint(1, 6)

def main():
    # Character selection
    print("Escolha seu personagem:")
    print("1 - Pica-Pau")
    print("2 - Zeca Urubu")
    choice = input("Digite 1 ou 2: ")
    
    while choice not in ['1', '2']:
        print("Escolha inválida! Digite 1 ou 2.")
        choice = input("Digite 1 ou 2: ")
    
    player = "Pica-Pau" if choice == '1' else "Zeca Urubu"
    opponent = "Zeca Urubu" if choice == '1' else "Pica-Pau"
    
    player_hp = 10
    opponent_hp = 10
    turn = 1
    
    print(f"\nVocê escolheu {player}! Que comece a batalha contra {opponent}!\n")
    
    while player_hp > 0 and opponent_hp > 0:
        print(f"Turno {turn}")
        print(f"{player} HP: {player_hp} | {opponent} HP: {opponent_hp}")
        
        # Player's turn
        input("Pressione Enter para rolar o dado...")
        player_roll = roll_dice()
        print(f"{player} rolou: {player_roll}")
        
        if player_roll == 6:
            print(f"{player} acertou um golpe crítico!")
            opponent_hp -= 5
        else:
            print(f"{player} acertou um golpe normal.")
            opponent_hp -= 1
        
        if opponent_hp <= 0:
            print(f"\n{opponent} foi derrotado! {player} vence!")
            break
        
        # Opponent's turn
        print(f"\nVez de {opponent}...")
        opponent_roll = roll_dice()
        print(f"{opponent} rolou: {player_roll}")
        
        if opponent_roll == 6:
            print(f"{opponent} acertou um golpe crítico!")
            player_hp -= 5
        else:
            print(f"{opponent} acertou um golpe normal.")
            player_hp -= 1
        
        if player_hp <= 0:
            print(f"\n{player} foi derrotado! {opponent} vence!")
            break
        
        print("\n" + "-"*40 + "\n")
        turn += 1

if __name__ == "__main__":
    main()