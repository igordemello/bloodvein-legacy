class Dificuldade:
    def __init__(self, nivel='normal'):
        self.set_dificuldade(nivel)

    def set_dificuldade(self, nivel):
        self.nivel = nivel.lower()
        if nivel == 'fácil': #fácil e depois normal
            self.mult_dano_jogador = 0.8 #dano NO jogador
            self.mult_dano_inimigo = 1.2 #dano DO jogador
            self.levas = 1
            print("facil")
        elif nivel == 'normal':
            self.mult_dano_jogador = 1
            self.mult_dano_inimigo = 1
            self.levas = 1
            print("normal")
        elif nivel == 'criança da noite':
            self.mult_dano_jogador = 1.5
            self.mult_dano_inimigo = 0.7
            self.levas = 2
            print("c")
        elif nivel == 'lua de sangue':
            self.mult_dano_jogador = 2.5
            self.mult_dano_inimigo = 0.5
            self.levas = 3
            print("l")
        else:
            self.mult_dano_jogador = 1.0
            self.mult_dano_inimigo = 1.0
            self.levas = 3
            print("cuzinhomelado")

    def chance(self, raridade):
        raridade = raridade.lower()
        chances = {
            'fácil': {
                'comum': 88,  # Aumentado de 70
                'incomum': 8,  # Reduzido de 20
                'raro': 3.5,  # Reduzido de 7
                'lendaria': 0.5 # Reduzido de 3
            },
            'normal': {
                'comum': 85,  # Aumentado de 60
                'incomum': 10,  # Reduzido de 20
                'raro': 4,  # Mantido igual
                'lendaria': 1  # Reduzido de 13
            },
            'criança da noite': {
                'comum': 78,  # Aumentado de 50
                'incomum': 10,  # Reduzido de 20
                'raro': 8,  # Aumentado de 7
                'lendaria': 4  # Reduzido de 23
            },
            'lua de sangue': {
                'comum': 70,  # Aumentado de 40
                'incomum': 10,  # Reduzido de 20
                'raro': 10,  # Aumentado de 7
                'lendaria': 5  # Reduzido de 33
            }
        }

        dist = chances.get(self.nivel, chances['normal'])
        print(dist.get(raridade, 0))
        return dist.get(raridade, 0)



dificuldade_global = Dificuldade('Normal')

