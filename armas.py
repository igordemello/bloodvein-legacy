from ast import Mult
from pygame import *
import sys
from pygame.locals import QUIT
import math
from random import randint, choice
from abc import ABC, abstractmethod
from som import GerenciadorDeSom
from som import som
from dificuldade import dificuldade_global
from utils import resource_path

# raridade
RARIDADES = {
    "comum": 1,
    "incomun": 2,
    "raro": 3,
    "lendaria": 4
}


# classe modificador
class Modificador(ABC):
    @abstractmethod
    def aplicarMod(self, arma):
        pass


# classe arma
class Arma(ABC):
    @abstractmethod
    def aplicaModificador(self):
        pass

    def ataquePrincipal(self, inimigo):
        pass

    def ataqueSecundario(self, inimigo):
        pass

    def get_save_data(self):
        return {
            'tipo': self.__class__.__name__,
            'raridade': self.raridadeStr,
            'dano': self.dano,
            'velocidade': self.velocidade,
            'lifeSteal': self.lifeSteal,
            'chanceCritico': self.chanceCritico,
            'danoCriticoMod': self.danoCriticoMod,
            'modificador': self.modificador.nome if hasattr(self, 'modificador') else None,
            'modificador_detalhes': {
                'nome': self.modificador.nome,
                'valor': self.modificador.valor
            } if hasattr(self, 'modificador') else None
        }

    def load_save_data(self, data, lista_mods=None):
        self.dano = data['dano']
        self.velocidade = data['velocidade']
        self.lifeSteal = data['lifeSteal']
        self.chanceCritico = data['chanceCritico']
        self.danoCriticoMod = data['danoCriticoMod']

        if data['modificador'] and lista_mods:
            mod_class = getattr(sys.modules[__name__], data['modificador'])
            self.modificador = mod_class(self)
            if data.get('modificador_detalhes'):
                self.modificador.valor = data['modificador_detalhes']['valor']

        # self.aplicaModificador()


# MODIFICADORES:
class Amaldicoado(Modificador):
    def __init__(self, arma):
        self.nome = "Amaldicoado"
        self.atributos = ["dano", "velocidade", "lifeSteal", "chanceCritico", "danoCriticoMod"]

        self.atributo_bom = choice(self.atributos)
        self.atributo_ruim = choice([a for a in self.atributos if a != self.atributo_bom])

        self.valor = {
            "bom": round(randint(100, 200) / 10, 1),  # de +10.0 até +20.0
            "ruim": round(randint(50, 150) / 10, 1)  # de -10.0 até -20.0
        }

    def aplicarMod(self, arma):
        valor_bom = self.valor["bom"]
        setattr(arma, self.atributo_bom, max(1, getattr(arma, self.atributo_bom) + valor_bom))  # Garante mínimo de dano
        valor_ruim = self.valor["ruim"]
        setattr(arma, self.atributo_ruim, max(0.2 if self.atributo_ruim == "velocidade" else 1,
                                              getattr(arma, self.atributo_ruim) - valor_ruim))


class Rapida(Modificador):
    def __init__(self, arma):
        self.valor = randint(15 + arma.raridade, 30 + arma.raridade) / 10
        self.nome = "Rapida"

    def aplicarMod(self, arma):
        arma.velocidade = max(0.2, min(2.0, self.valor))  # Velocidade entre 0.2 e 2.0
        arma.dano = max(1, arma.dano - self.valor)  # Dano mínimo de 1


class Afiada(Modificador):
    def __init__(self, arma):
        self.valor = arma.dano * 0.3 + arma.raridade * 3  # Reduzido de 0.5 para 0.3 e de 5 para 3
        self.nome = "Afiada"

    def aplicarMod(self, arma):
        arma.dano = max(1, arma.dano + self.valor)  # Dano mínimo de 1


class Precisa(Modificador):
    def __init__(self, arma):
        self.valor = 3 * arma.raridade  # Reduzido de 5 para 3
        self.nome = "Precisa"

    def aplicarMod(self, arma):
        arma.chanceCritico = max(1, arma.chanceCritico + self.valor)  # Chance crítica mínima de 1%


class Impactante(Modificador):
    def __init__(self, arma):
        self.valor = arma.raridade * 0.5  # Reduzido impacto
        self.nome = "Impactante"

    def aplicarMod(self, arma):
        arma.danoCriticoMod += self.valor


class Sangrenta(Modificador):
    def __init__(self, arma):
        self.valor = arma.lifeSteal / 3  # Reduzido de /2 para /3
        self.nome = "Sangrenta"

    def aplicarMod(self, arma):
        arma.lifeSteal += self.valor


class Pesada(Modificador):
    def __init__(self, arma):
        self.valor = arma.dano * 0.8  # Reduzido de 1.0 para 0.8
        self.nome = "Pesada"

    def aplicarMod(self, arma):
        arma.dano = max(1, arma.dano + self.valor)  # Dano mínimo de 1
        arma.velocidade = max(0.2, arma.velocidade * 0.7)  # Velocidade mínima de 0.2


class Sortuda(Modificador):
    def __init__(self, arma):
        self.valor = arma.chanceCritico * 2  # Reduzido de 4 para 2
        self.nome = "Sortuda"

    def aplicarMod(self, arma):
        arma.chanceCritico = max(1, arma.chanceCritico + self.valor)  # Chance crítica mínima de 1%
        arma.danoCriticoMod *= 0.9  # Reduzido impacto negativo de 0.8 para 0.9


class Potente(Modificador):
    def __init__(self, arma):
        self.valor = 1 * arma.raridade  # Reduzido de 2 para 1
        self.nome = "Potente"

    def aplicarMod(self, arma):
        arma.danoCriticoMod += self.valor
        arma.chanceCritico = max(1, arma.chanceCritico * 0.7)  # Chance crítica mínima de 1%


class ListaMods:
    def __init__(self):
        self.modificadores = [
            Rapida, Afiada, Precisa,
            Impactante, Sangrenta, Pesada,
            Sortuda, Potente, Amaldicoado
        ]

        self.modificadores_por_nome = {
            cls.__name__: cls for cls in self.modificadores
        }

    def get_mod_by_name(self, nome):
        """Obtém uma classe de modificador pelo nome"""
        return self.modificadores_por_nome.get(nome)

    def getMod(self, raridade_str):
        """Retorna um modificador aleatório, sem restrição por raridade"""
        return choice(self.modificadores)


# ARMAS:
class LaminaDaNoite(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Lamina da Noite"
        self.ataqueTipo = "melee"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage reduced from 10 to 8, and range reduced
        self.dano = max(1, 8 + randint(3 * self.raridade, 6 * self.raridade))  # Dano mínimo de 1
        self.velocidade = max(0.2, 1.0)  # Velocidade mínima de 0.2
        self.cooldown = max(100, 400)  # Cooldown mínimo de 100
        self.range = (40, 90)  # hitbox arma
        self.radius = 100
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 3)  # Life steal reduzido de /2 para /3
        self.lifeStealMod = 2
        self.chanceCritico = max(1, 8)  # Chance crítica mínima de 1%
        self.danoCriticoMod = 1.5  # Reduzido de 2 para 1.5
        self.comboMult = 1
        self.clock = time.Clock()

        self.secEhAtaque = True
        self.ehRanged = False
        self.ehAOE = False

        self.spriteIcon = resource_path('assets/UI/LaminaDaNoite.png')
        self.sprite = resource_path('assets/Player/espada.png')
        self.carta = resource_path('assets/Itens/Carta_espada_lunar.png')
        self.size = (20 * 2, 54 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)  # Retorna a classe do modificador
        self.modificador = mod_classe(self)  # Instancia com self (a arma)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        # Garante os valores mínimos após aplicar modificadores
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(2.0, self.velocidade))  # Limite máximo de velocidade
        self.chanceCritico = max(1, self.chanceCritico)

    def ataquePrincipal(self, inimigo):
        dano_final = max(1,
                         self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)  # Dano mínimo de 1
        if inimigo.congelado == True:
            inimigo.congelado = False
            inimigo.velocidade /= 0.5
        if randint(1, 100) <= max(1, self.chanceCritico):  # Chance crítica mínima de 1%
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
        else:
            inimigo.tomar_dano(dano_final)
            inimigo.ultimo_dano_critico = False
            inimigo.ultimo_dano = dano_final

    def ataqueSecundario(self, inimigo, player):
        dano_final = max(1,
        self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)  # Dano mínimo de 1
        current_time = time.get_ticks()
        custo = 50 * player.mpModificador
        if player.mp < custo:
            # Ativa mensagem de sem mana no HUD
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if player.mp <= 0:
            return
        else:
            player.mp -= custo
            player.hp -= 15
            inimigo.tomar_dano(dano_final*2)
            inimigo.congelado = True
            inimigo.velocidade *= 0.5




class Chigatana(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Chigatana"
        self.ataqueTipo = "melee"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage reduced from 10 to 7
        self.dano = max(1, 7 + randint(3 * self.raridade, 6 * self.raridade))
        self.velocidade = max(0.2, 1.8)  # Reduzida de 2.0 para 1.8
        self.cooldown = max(100, 400)
        self.range = (35, 90)
        self.radius = 100
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 4)
        self.lifeStealMod = 4
        self.chanceCritico = max(1, 5)
        self.danoCriticoMod = 1.5  # Reduzido de 2 para 1.5
        self.comboMult = 1
        self.clock = time.Clock()

        self.secEhAtaque = True
        self.ehRanged = False
        self.ehAOE = False

        self.spriteIcon = resource_path('assets/UI/chigatana.png')
        self.sprite = resource_path('assets/player/chigatana.png')
        self.carta = resource_path('assets/Itens/Carta_espada_sangue.png')
        self.size = (20 * 2, 54 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)
        self.modificador = mod_classe(self)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"
        self.valorSangramento = 1.8 * self.raridade  # Reduzido de 2.2 para 1.8

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(2.0, self.velocidade))  # Limite máximo de velocidade
        self.chanceCritico = max(1, self.chanceCritico)

    def ataquePrincipal(self, inimigo):
        dano_final = max(1,
                         self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)
        if randint(1, 100) <= max(1, self.chanceCritico):
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
        else:
            inimigo.tomar_dano(dano_final)
            inimigo.ultimo_dano_critico = False
            inimigo.ultimo_dano = dano_final

    def ataqueSecundario(self, inimigo, player):
        current_time = time.get_ticks()
        custo = 40 * player.mpModificador
        if player.mp < custo:
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if player.mp <= 0:
            return
        else:
            player.mp -= custo
            inimigo.modificadorDanoRecebido = self.valorSangramento
            inimigo.sangrando = True


class Karambit(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Adaga"
        self.ataqueTipo = "melee"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage reduced from 5 to 4
        self.dano = max(1, 4 + randint(3 * self.raridade, 6 * self.raridade))
        self.velocidade = max(0.2, 2.0)
        self.cooldown = max(100, 300)
        self.range = (50, 50)
        self.radius = 80
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 2)
        self.lifeStealMod = 2
        self.chanceCritico = max(1, 5)
        self.danoCriticoMod = 1.5  # Reduzido de 2 para 1.5
        self.comboMult = 1
        self.clock = time.Clock()

        self.secEhAtaque = True
        self.ehRanged = False
        self.ehAOE = False

        self.spriteIcon = resource_path('assets/UI/Karambit.png')
        self.sprite = resource_path('assets/player/Karambit.png')
        self.carta = resource_path('assets/Itens/Carta_Adaga.png')
        self.size = (32 * 2, 32 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)
        self.modificador = mod_classe(self)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(2.5, self.velocidade))  # Limite máximo de velocidade para adagas
        self.chanceCritico = max(1, self.chanceCritico)

    def ataquePrincipal(self, inimigo):
        dano_final = max(1,
                         self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)
        if randint(1, 100) <= max(1, self.chanceCritico):
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
        else:
            inimigo.tomar_dano(dano_final)
            inimigo.ultimo_dano_critico = False
            inimigo.ultimo_dano = dano_final

    def ataqueSecundario(self, inimigo, player):
        current_time = time.get_ticks()
        custo = 40 * player.mpModificador
        if player.mp < custo:
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if player.mp <= 0:
            return
        else:
            player.mp -= custo
            inimigo.envenenar(5, self.dano)


class EspadaDoTita(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Espada do Tita"
        self.ataqueTipo = "melee"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage reduced from 25 to 20, range reduced
        self.dano = max(1, 20 + randint(10 * self.raridade, 15 * self.raridade))
        self.velocidade = max(0.2, 0.4)  # Reduzida de 0.5 para 0.4 (arma mais lenta)
        self.cooldown = max(100, 400)
        self.range = (40, 115)
        self.radius = 100
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 2)
        self.lifeStealMod = 2
        self.chanceCritico = max(1, 12)
        self.danoCriticoMod = 2.5  # Reduzido de 3 para 2.5
        self.comboMult = 1
        self.clock = time.Clock()
        self.criticoOg = self.chanceCritico
        self.danoCritOg = self.danoCriticoMod

        self.secEhAtaque = False
        self.ehRanged = False
        self.ehAOE = False

        self.pitch_minimo = 0.8  # Pitch quando chance crítica está no mínimo
        self.pitch_maximo = 1.5

        self.spriteIcon = resource_path('assets/UI/espadadotita.png')
        self.sprite = resource_path('assets/player/espadadotita.png')
        self.carta = resource_path('assets/Itens/Carta_titã.png')
        self.size = (25 * 2, 70 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)
        self.modificador = mod_classe(self)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(0.6, self.velocidade))  # Limite máximo de velocidade para armas pesadas
        self.chanceCritico = max(1, self.chanceCritico)
        self.criticoOg = self.chanceCritico
        self.danoCritOg = self.danoCriticoMod

    def ataquePrincipal(self, inimigo):
        dano_final = max(1,
                         self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)
        if randint(1, 100) <= max(1, self.chanceCritico):
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
        else:
            inimigo.tomar_dano(dano_final)
            inimigo.ultimo_dano_critico = False
            inimigo.ultimo_dano = dano_final
        self.chanceCritico = max(1, self.criticoOg)
        self.danoCriticoMod = self.danoCritOg

    def ataqueSecundario(self, player):
        current_time = time.get_ticks()
        custo = 50 * player.mpModificador
        if player.mp < custo:
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if self.chanceCritico > 100 or player.mp <= 0:
            return

        # Calcula pitch baseado na chance crítica
        chance_normalizada = (self.chanceCritico - self.criticoOg) / (100 - self.criticoOg)
        pitch = self.pitch_minimo + (self.pitch_maximo - self.pitch_minimo) * min(1.0, chance_normalizada)

        # Toca o som com pitch ajustado
        som.tocar_com_pitch('carrega_critico', pitch=pitch)

        # Aumenta a chance crítica
        self.chanceCritico = min(100, self.chanceCritico * 2)  # Limita a 100%
        self.danoCriticoMod *= 1.5
        player.mp -= custo


class MachadoDoInverno(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Machado Do Inverno"
        self.ataqueTipo = "melee"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage reduced from 15 to 12, range reduced
        self.dano = max(1, 12 + randint(10 * self.raridade, 15 * self.raridade))
        self.velocidade = max(0.2, 0.5)  # Reduzida de 0.7 para 0.5 (arma mais lenta)
        self.cooldown = max(100, 400)
        self.range = (40, 80)
        self.radius = 100
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 2)
        self.lifeStealMod = 2
        self.chanceCritico = max(1, 15)
        self.danoCriticoMod = 1.8  # Reduzido de 2.5 para 1.8
        self.comboMult = 1
        self.clock = time.Clock()
        self.criticoOg = self.chanceCritico
        self.danoCritOg = self.danoCriticoMod

        self.secEhAtaque = True
        self.ehRanged = False
        self.ehAOE = False

        self.spriteIcon = resource_path('assets/UI/machadodoinverno.png')
        self.sprite = resource_path('assets/player/machadodoinverno.png')
        self.carta = resource_path('assets/Itens/Carta_machado_gelo.png')
        self.size = (23 * 2, 54 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)
        self.modificador = mod_classe(self)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(0.7, self.velocidade))  # Limite máximo de velocidade para armas pesadas
        self.chanceCritico = max(1, self.chanceCritico)
        self.criticoOg = self.chanceCritico
        self.danoCritOg = self.danoCriticoMod

    def ataquePrincipal(self, inimigo):
        dano_final = max(1,
                         self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)
        if inimigo.congelado:
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
            inimigo.congelado = False
            inimigo.velocidade /= 0.25
        if randint(1, 100) <= max(1, self.chanceCritico):
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
        else:
            inimigo.tomar_dano(dano_final)
            inimigo.ultimo_dano_critico = False
            inimigo.ultimo_dano = dano_final
        self.chanceCritico = max(1, self.criticoOg)
        self.danoCriticoMod = self.danoCritOg

    def ataqueSecundario(self, inimigo, player):
        current_time = time.get_ticks()
        custo = 35 * player.mpModificador
        if player.mp < custo:
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if player.mp <= 0:
            return
        else:
            inimigo.velocidade *= 0.25
            inimigo.congelado = True
            player.mp -= custo
            player.last_dash_time = current_time


class EspadaEstelar(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Espada Estelar"
        self.ataqueTipo = "melee"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage reduced from 20 to 15
        self.dano = max(1, 15 + randint(6 * self.raridade, 12 * self.raridade))
        self.velocidade = max(0.2, 0.8)
        self.cooldown = max(100, 400)
        self.range = (40, 90)
        self.radius = 100
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 2)
        self.lifeStealMod = 2
        self.chanceCritico = max(1, 10)
        self.danoCriticoMod = 1.8  # Reduzido de 2 para 1.8
        self.comboMult = 1
        self.clock = time.Clock()

        self.secEhAtaque = True
        self.ehRanged = True
        self.ehAOE = False

        self.spriteIcon = resource_path('assets/UI/espadaestelar.png')
        self.sprite = resource_path('assets/player/espadaestelar.png')
        self.carta = resource_path('assets/Itens/Carta_espada_laser.png')
        self.size = (23 * 2, 54 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)
        self.modificador = mod_classe(self)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(1.5, self.velocidade))  # Limite máximo de velocidade
        self.chanceCritico = max(1, self.chanceCritico)

    def ataquePrincipal(self, inimigo):
        dano_final = max(1,
                         self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)
        if randint(1, 100) <= max(1, self.chanceCritico):
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
        else:
            inimigo.tomar_dano(dano_final)
            inimigo.ultimo_dano_critico = False
            inimigo.ultimo_dano = dano_final

    def ataqueSecundario(self, player, mouse_pos):
        current_time = time.get_ticks()
        custo = 20 * player.mpModificador
        if player.mp < custo:
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if player.mp <= 0:
            return
        else:
            player.criar_projetil(mouse_pos, (max(1, self.dano / 1.5)), cor=(24, 212, 59))  # Reduzido de /2.5 para /3
            player.mp -= custo
            player.last_dash_time = current_time


class MarteloSolar(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Martelo Solar"
        self.ataqueTipo = "melee"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage reduced from 15 to 12
        self.dano = max(1, 12 + randint(10 * self.raridade, 15 * self.raridade))
        self.velocidade = max(0.5, 0.8)  # Reduzida de 0.5 para 0.4 (arma mais lenta)
        self.cooldown = max(100, 250)
        self.range = (52, 80)
        self.radius = 100
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 2)
        self.lifeStealMod = 2
        self.chanceCritico = max(1, 13)
        self.danoCriticoMod = 1.8  # Reduzido de 2 para 1.8
        self.comboMult = 1
        self.clock = time.Clock()

        self.secEhAtaque = True
        self.ehRanged = True
        self.ehAOE = True
        self.danoAOE = max(1, self.dano * 0.6)  # Reduzido de 0.8 para 0.6

        self.spriteIcon = resource_path('assets/UI/martelo_icone.png')
        self.sprite = resource_path('assets/player/martelo_solar.png')
        self.carta = resource_path('assets/Itens/Carta_Sol.png')
        self.size = (27 * 2, 51 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)
        self.modificador = mod_classe(self)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(0.6, self.velocidade))  # Limite máximo de velocidade para armas pesadas
        self.chanceCritico = max(1, self.chanceCritico)
        self.danoAOE = max(1, self.dano * 0.6)  # Reduzido de 0.8 para 0.6

    def ataquePrincipal(self, inimigo):
        dano_final = max(1,
                         self.dano * inimigo.modificadorDanoRecebido * dificuldade_global.mult_dano_inimigo * self.comboMult)
        if randint(1, 100) <= max(1, self.chanceCritico):
            inimigo.tomar_dano(dano_final * self.danoCriticoMod, critico=True)
            inimigo.ultimo_dano_critico = True
            inimigo.ultimo_dano = dano_final * self.danoCriticoMod
        else:
            inimigo.tomar_dano(dano_final)
            inimigo.ultimo_dano_critico = False
            inimigo.ultimo_dano = dano_final

    def ataqueSecundario(self, player, mouse_pos):
        current_time = time.get_ticks()
        custo = 30 * player.mpModificador
        if player.mp < custo:
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if player.mp - (30 * player.mpModificador) < 0:
            return
        else:
            som.tocar('martelo2')
            aoeMartelo = player.criarAOE(mouse_pos, 300)
            if aoeMartelo is None:
                return
            player.mp -= custo
            player.last_dash_time = current_time
            return aoeMartelo


class Arco(Arma):
    def __init__(self, raridadeStr: str, listaMods: ListaMods):
        self.tipoDeArma = "Arco"
        self.ataqueTipo = "ranged"
        self.raridadeStr = raridadeStr
        self.raridade = RARIDADES.get(self.raridadeStr, 1)
        # Base damage significantly reduced from 20 to 12
        self.dano = max(1, 4 + randint(4 * self.raridade, 5 * self.raridade))
        self.velocidade = max(0.2, 0.7)
        self.cooldown = max(100, 300)
        self.range = (40, 90)
        self.radius = 90
        self.efeitos = None
        self.lifeSteal = max(1, self.dano / 3)  # Reduzido de /2 para /3
        self.lifeStealMod = 2
        self.chanceCritico = max(1, 8)  # Reduzido de 10 para 8
        self.danoCriticoMod = 1.8  # Reduzido de 2 para 1.8
        self.comboMult = 1
        self.clock = time.Clock()

        self.secEhAtaque = True
        self.ehRanged = True
        self.ehAOE = False

        self.spriteIcon = resource_path('assets/UI/arco.png')
        self.sprite = resource_path('assets/player/arco.png')
        self.carta = resource_path('assets/Itens/Carta_Arco.png')
        self.size = (51 * 2, 27 * 2)
        self.pivot = (self.size[0] / 2, 0)

        mod_classe = listaMods.getMod(self.raridadeStr)
        self.modificador = mod_classe(self)
        self.nome = f"{self.tipoDeArma} {self.modificador.nome} {self.raridadeStr}"

    def aplicaModificador(self):
        self.modificador.aplicarMod(self)
        self.dano = max(1, self.dano)
        self.velocidade = max(0.2, min(1.5, self.velocidade))  # Limite máximo de velocidade para arcos
        self.chanceCritico = max(1, self.chanceCritico)

    def ataquePrincipal(self, player, mouse_pos):
        dano_final = max(1, self.dano * dificuldade_global.mult_dano_inimigo * self.comboMult)
        som.tocar('arco_acerto')
        sprite_projetil = image.load(resource_path('assets/player/flecha.png')).convert_alpha()
        player.criar_projetil(mouse_pos, dano=dano_final, cor=None, sprite=sprite_projetil)

    def ataqueSecundario(self, player, mouse_pos):
        dano_final = max(1, self.dano * dificuldade_global.mult_dano_inimigo * self.comboMult)
        sprite_projetil = image.load(resource_path('assets/player/flecha.png')).convert_alpha()
        angulo_central = player.calcular_angulo(mouse_pos)
        angulo_abertura = math.radians(5)
        current_time = time.get_ticks()
        custo = 20 * player.mpModificador
        if player.mp < custo:
            player.hud.mensagem_sem_mana = True
            player.hud.tempo_mensagem_mana = current_time
            return
        if player.mp <= 0:
            return
        else:
            som.tocar('tripleshota')
            player.mp -= custo
            player.last_dash_time = current_time
            player.criar_projetil(mouse_pos, dano=dano_final, cor=None, sprite=sprite_projetil,
                                  angulo_personalizado=angulo_central)
            player.criar_projetil(mouse_pos, dano=dano_final, cor=None, sprite=sprite_projetil,
                                  angulo_personalizado=angulo_central - angulo_abertura)
            player.criar_projetil(mouse_pos, dano=dano_final, cor=None, sprite=sprite_projetil,
                                  angulo_personalizado=angulo_central + angulo_abertura)