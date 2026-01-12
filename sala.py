from pygame import *
import sys
from pygame.locals import QUIT
import math
from bau import Bau
from inimigos.MagoElementar import MagoElementar
from inimigos.aranhadosol import AranhaDoSol
from inimigos.arqueiro import Arqueiro
from inimigos.ratodesangue import RatoDeSangue
from inimigos.vampirosol import VampiroSol
from itensDic import ConjuntoItens
from mapa import Mapa
from inimigos.orb import Orb
from inimigos.espectro import Espectro
import inimigos.MouthOrbBoss as bossmod
from colisao import Colisao
from loja import Loja
from random import randint, sample, choice
import gerenciador_andar
from screen_shake import screen_shaker
from cutscene import Cutscene
from som import GerenciadorDeMusica
from som import musica
from som import GerenciadorDeSom
from som import som
from loja import Loja
from inimigos.caveiradefogo import CaveiraDeFogo
from inimigos.morcegopadrao import MorcegoPadrao
from inimigos.furacao import Furacao
from inimigos.nuvemBoss import NuvemBoss
from inimigos.nuvemBoss2 import NuvemBoss2
from inimigos.MouthOrbBoss2 import MouthOrb2
from inimigos.Cachorro import Cerbero
from inimigos.massa_de_olhos import Massa
from inimigos.zombie import Zombie
from armas import LaminaDaNoite, Chigatana, Karambit, EspadaDoTita, MachadoDoInverno, EspadaEstelar, MarteloSolar, Arco, ListaMods
from botao import Botao
from inimigos.polvo import Polvo
from inimigos.aranha_lunar import AranhaLunar
from inimigos.esqueleto_gelo import EsqueletoGelo
from inimigos.esqueleto_peconhento import EsqueletoPeconhento
from save_manager import SaveManager
from dificuldade import dificuldade_global
from utils import resource_path
import pygame


def pixel_para_grid(x, y, offset, tile_size_scaled):
    """Converte coordenadas de pixel para grid, considerando offset e tamanho do tile escalado"""
    grid_x = int((x - offset[0]) / tile_size_scaled)
    grid_y = int((y - offset[1]) / tile_size_scaled)
    return grid_x, grid_y

def grid_para_pixel(grid_x, grid_y, offset, tile_size_scaled):
    """Converte coordenadas de grid para pixel (centro do tile), considerando offset"""
    x = offset[0] + (grid_x * tile_size_scaled) + (tile_size_scaled / 2)
    y = offset[1] + (grid_y * tile_size_scaled) + (tile_size_scaled / 2)
    return x, y

init()
fonte = font.SysFont("Arial", 24)


class Sala:
    def __init__(self, caminho_mapa, tela, player, gerenciador_andar, set_minimapa_callback):
        self.tela = tela
        self.gerenciador_andar = gerenciador_andar
        self.mapa = Mapa(caminho_mapa,self.tela,self.tela.get_width(),self.tela.get_height(),self.gerenciador_andar)
        # self.mapa = Mapa("andar1/1.tmx",self.tela,self.tela.get_width(),self.tela.get_height(),self.gerenciador_andar)

        self.lista_mods = ListaMods()
        self.loots = []

        self.musica_atual = None

        self.player = player
        self.colisao = Colisao(self.mapa, self.player)
        self.colisao.adicionar_entidade(player)
        self.set_minimapa = set_minimapa_callback

        self.porta_liberada = False

        self.pocoesHp = transform.scale(image.load(resource_path('assets/itens/pocaodevida.png')), (64,64))
        self.pocoesMp = transform.scale(image.load(resource_path('assets/itens/pocaodemana.png')), (64,64))

        self.ranges_doors = self.mapa.get_rangesdoors()

        self.almaspritesheet = image.load(resource_path('./assets/Itens/almaSpriteSheet.png')).convert_alpha()

        self.lojista_img = transform.scale(image.load(resource_path('./assets/Player/Ikoojista.png')).convert_alpha(),(67.5,132.3))

        self.frames_alma = [self.almaspritesheet.subsurface(Rect(i * 32, 0, 32, 32)) for i in range(4)]

        self.frame_alma_idx = 0
        self.tempo_anterior_alma = time.get_ticks()
        self.duracao_frame_alma = 200
        self.itensDisp = ConjuntoItens()
        self.colliders = self.mapa.get_colliders()

        no_atual = self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]
        tipo = no_atual["tipo"]

        if tipo == "loja":
            if "itens_loja" in no_atual:
                ids_sorteados = no_atual["itens_loja"]
                comprados = no_atual.get("itens_comprados", [False, False, False])
            else:
                ids_disponiveis = list(self.itensDisp.itens_por_id)
                ids_sorteados = sample(ids_disponiveis, 3)
                comprados = [False, False, False]
                no_atual["itens_loja"] = ids_sorteados
                no_atual["itens_comprados"] = comprados

            self.loja = Loja(self.itensDisp, self.player, ids_sorteados, comprados, no_atual)
        else:
            self.loja = None
        self.player.sala_atual = self


        self.em_transicao = False
        self.visitada = False
        self.cutscene = None

        self.portal_spritesheet = image.load(
            resource_path('assets/TileSet/coisas/Portal_Animação.png')
        ).convert_alpha()

        self.portal_frames = []
        frame_count = 4

        sheet_width = self.portal_spritesheet.get_width()
        sheet_height = self.portal_spritesheet.get_height()

        frame_width = sheet_width // frame_count
        frame_height = sheet_height

        for i in range(frame_count):
            frame = self.portal_spritesheet.subsurface(
                Rect(i * frame_width, 0, frame_width, frame_height)
            )
            frame = transform.scale(frame, (128, 128))
            self.portal_frames.append(frame)

        self.portal_frame_idx = 0
        self.portal_frame_delay = 150  # ms
        self.portal_last_update = time.get_ticks()

        self.spawn_points = self.mapa.get_inimigospawn()
        if tipo == 'loja':
            self.max_leves = 0
            self.leve_atual = self.max_leves + 2 
        else:
            self.leve_atual = 0
            if self.gerenciador_andar.numero_andar == 1:
                self.max_leves = randint(1, 2)
            elif self.gerenciador_andar.numero_andar == 2:
                self.max_leves = randint(3, 4)
            elif self.gerenciador_andar.numero_andar == 3:
                self.max_leves = randint(4, 6)
            elif self.gerenciador_andar.numero_andar == 4:
                self.max_leves = randint(5, 7)
            else:
                self.max_leves = randint(5, 7)
        self.inimigos_por_leva = 1
        self.tempo_entrada = time.get_ticks()
        self.cooldown_inicial = 1000
        self.inimigos_spawnados = False
        self.cooldown_entre_levas = 1000
        self.tempo_ultima_leva = 0
        self.aguardando_nova_leva = False

        self.fumaça_particula = []
        self.ultima_fumaça = 0
        self.intervalo_fumaça = 100

        self.inventario_cheio_msg = ""
        self.inventario_cheio_tempo = 0
        self.inventario_cheio_duracao = 2000

        tipo = self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]['tipo']
        bau_aberto = self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual].get('bau_aberto', False)
        self.bau_interagido = False
        self.ativar_menu_bau = False # eu adicionei isso aqui depois de fazer o iniciar e continuar por conta de um erro que estava dando, se DO NADA der merda no bau a culpa é disso e eu vou me matar
        if tipo == 'bau':
            x, y = self.mapa.get_rangebau()[0].topleft
            self.bau = Bau(self.itensDisp, x, y)

            if bau_aberto:
                self.bau.aberto = True
                self.bau.animando = False
                self.bau.frame_index = len(self.bau.frames) - 1
                self.bau.image = self.bau.frames[-1]
                self.bau.menu_ativo = False  # Garante que não reabra
            else:
                self.ativar_menu_bau = False
        else:
            self.bau = None

        if tipo == "boss" and not gerenciador_andar.sala_foi_conquistada(gerenciador_andar.sala_atual):
            fundo = self.tela.copy()
            numerodoandar = self.gerenciador_andar.numero_andar

            if numerodoandar == 1:
                cenas = [
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/player.png')).convert_alpha(), (640,960)), "fala": "Prepare-se para morrer", "lado": "esquerda"},
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/olhoBoss.png')).convert_alpha(), (840,840)), "fala": "Blaarr blar ble", "lado": "direita"}
                ]
                self.cutscene = Cutscene(cenas, fundo, self.tela.get_width(), self.tela.get_height())

            if numerodoandar == 2:
                cenas = [
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/nuvemBoss.png')).convert_alpha(), (800,800)), "fala": "....", "lado": "direita"},
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/player.png')).convert_alpha(), (640,960)), "fala": "que nojo", "lado": "esquerda"}

                ]
                self.cutscene = Cutscene(cenas, fundo, self.tela.get_width(), self.tela.get_height())
            if numerodoandar == 3:
                cenas = [
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/player.png')).convert_alpha(), (800,800)), "fala": "Você está um pouco... diferente", "lado": "direita"},
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/olhoBoss2.png')).convert_alpha(), (640,960)), "fala": "BLAAR BLER MORRA", "lado": "esquerda"}

                ]
                self.cutscene = Cutscene(cenas, fundo, self.tela.get_width(), self.tela.get_height())
            if numerodoandar == 4:
                cenas = [
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/player.png')).convert_alpha(), (800,800)), "fala": "Eu vou te matar nuvem monstruosa", "lado": "direita"},
                    {"imagem": transform.scale(image.load(resource_path('assets/cutscene/nuvemBoss2.png')).convert_alpha(), (640,960)), "fala": "..........", "lado": "esquerda"}

                ]
                self.cutscene = Cutscene(cenas, fundo, self.tela.get_width(), self.tela.get_height())

        self.portal_img = transform.scale(image.load(resource_path('assets/TileSet/coisas/Portal.png')).convert_alpha(), (128, 128))





        if not gerenciador_andar.sala_foi_conquistada(gerenciador_andar.sala_atual):
            self.inimigos = self._criar_inimigos()
        else:
            self.inimigos = []
            self.porta_liberada = True
            self.visitada = True

        for inimigo in self.inimigos:
            self.colisao.adicionar_entidade(inimigo)


        self.musicas_de_combate = [
        resource_path("BloodVein SCORE/OST/MusicaDeCombate.mp3"),
        resource_path("BloodVein SCORE/OST/MusicaDeCombate2.mp3")
        ]

        self.musica_escolhida = choice(self.musicas_de_combate)
        self.boss_musica = 0

        self.save_manager = SaveManager()
        game_state = self.save_manager.generate_game_state(self.player, self.gerenciador_andar, self)
        self.save_manager.save_game(game_state, resource_path("save_file.json"))

        self.alagard = font.Font(resource_path('assets/fontes/alagard.ttf'), 25)

        self.game_vitoria = False
        self.vitoria_inicio = None


    def _criar_inimigos(self):
        if self.gerenciador_andar.sala_foi_conquistada(self.gerenciador_andar.sala_atual):
            self.leve_atual = self.max_leves + 2
            return []
        tipo_sala = self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]["tipo"]

        if 'spawn' in tipo_sala:
            self.leve_atual = self.max_leves + 2
            return []

        

        tempo_atual = time.get_ticks()
        if tempo_atual - self.tempo_entrada < self.cooldown_inicial and not self.inimigos_spawnados:
            return []

        if "boss" in tipo_sala:
            self.boss_musica = "suicidio"
            musica.tocar(resource_path("BloodVein SCORE/OST/MusicaDoBoss.mp3"))
            xboss,yboss= self.spawn_points[0]
            numero = self.gerenciador_andar.numero_andar
            if numero == 1:
                boss = bossmod.MouthOrb(xboss, yboss, 192, 192)
                boss.nome_base = "Mãe Orbe"
                self.leve_atual = self.max_leves + 2
                return[boss]
            elif numero == 2:
                boss = NuvemBoss(xboss-200, yboss-200, 400,400)
                boss.nome_base = "Visão Carmesim"
                self.leve_atual = self.max_leves + 2
                return[boss]
            elif numero == 3:
                boss = MouthOrb2(xboss, yboss,192, 192 )
                boss.nome_base = "Vovó Orbe"
                self.leve_atual = self.max_leves + 2
                return [boss]
            elif numero == 4:
                boss = NuvemBoss2(xboss-200, yboss-200, 400,400)
                boss.nome_base = "Visão Ácida"
                self.leve_atual = self.max_leves + 2
                return[boss]


        # self.leve_atual = self.max_leves + 2
        # return []

        self.inimigos_spawnados = True

        

        if not self.visitada:
            self.leve_atual = 0

        if self.leve_atual < self.max_leves:
            self.leve_atual += 1
            inimigos = []

            for x, y in self.spawn_points:
                testrect = Rect(x,y,50,50)
                inimigo = self._criar_inimigo_aleatorio(x, y, tipo_sala)
                if self.player.get_hitbox().colliderect(testrect) and isinstance(inimigo, (EsqueletoPeconhento, EsqueletoGelo, AranhaLunar, Zombie, VampiroSol, RatoDeSangue, MagoElementar, Arqueiro, AranhaDoSol)):
                    continue
                inimigos.append(inimigo)

            return inimigos

        return []

    def adicionar_inimigo(self, inimigo):
        self.inimigos.append(inimigo)
    
    def _criar_inimigo_aleatorio(self, x, y, tipo_sala):
        elite = "bau" in tipo_sala

        # tipos_disponiveis = ["furacao","caveiradefogo","morcegopadrao","orb","espectro","polvo", "esqueletogelo", "massa", "zombie","aranhalunar","esqueletogelo","ratodesangue", "aranhadosol","arqueiro", "vampirosol","magoelementar","esqueletopeconhento"]
        #tipos_disponiveis = ["furacao","caveiradefogo","morcegopadrao","orb","espectro","polvo", "esqueletogelo", "massa", "zombie","aranhalunar","esqueletogelo","ratodesangue", "aranhadosol","arqueiro", "vampirosol","magoelementar","esqueletopeconhento"]

        geral = ["morcegopadrao", "ratodesangue","polvo","aranhalunar"]
        andar1 = geral + ["orb", "esqueletogelo","espectro"]
        andar2 = geral + ["furacao", "arqueiro", "esqueletopeconhento"]
        andar3 = geral + ["caveiradefogo","magoelementar", "massa"]
        andar4 = geral + ["vampirosol","aranhadosol","zombie"]

        andar_atual = self.gerenciador_andar.numero_andar
        if andar_atual == 1:
            pool_inimigos = andar1
        elif andar_atual == 2:
            pool_inimigos = andar2
        elif andar_atual == 3:
            pool_inimigos = andar3
        elif andar_atual >= 4:
            pool_inimigos = andar4
        else:
            pool_inimigos = geral

        tipo_escolhido = choice(pool_inimigos)


        if tipo_escolhido == "furacao":
            inimigo = Furacao(x, y, 64, 64, hp=75 if not elite else 300)
            inimigo.nome_base = "Furacão"
            inimigo.aplicar_modificadores(elite=elite)


        elif tipo_escolhido == "caveiradefogo":
            inimigo = CaveiraDeFogo(x, y, 64, 64, hp=75 if not elite else 300)
            inimigo.nome_base = "Caveira de Fogo"
            inimigo.aplicar_modificadores(elite=elite)


        elif tipo_escolhido == "morcegopadrao":
            inimigo = MorcegoPadrao(x, y, 64, 64, hp=75 if not elite else 300)
            inimigo.nome_base = "Morcego Padrão"
            inimigo.aplicar_modificadores(elite=elite)


        elif tipo_escolhido == "orb":
            inimigo = Orb(x, y, 64, 64, hp=120 if not elite else 300)
            inimigo.nome_base = "Orb"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "espectro":
            inimigo = Espectro(x, y, 64, 64, hp=120 if not elite else 300)
            inimigo.nome_base = "Espectro"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "polvo":
            inimigo = Polvo(x, y, 64, 64, hp=120 if not elite else 300)
            inimigo.nome_base = "Polvo"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "massa":
            inimigo = Massa(x, y, 100, 100, hp=200 if not elite else 300)
            inimigo.nome_base = "Massa de Olhos"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "zombie":
            inimigo = Zombie(x, y, 96, 96, hp=200 if not elite else 300)
            inimigo.nome_base = "Zumbi"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "aranhalunar":
            inimigo = AranhaLunar(x, y, 50, 50, hp=100 if not elite else 300)
            inimigo.nome_base = "Aranha Lunar"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "esqueletogelo":
            inimigo = EsqueletoGelo(x, y, 96, 96, hp=200 if not elite else 300)
            inimigo.nome_base = "Esqueleto de Gelo"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "ratodesangue":
            inimigo = RatoDeSangue(x, y, 64, 64, hp=75 if not elite else 300)
            inimigo.nome_base = "Rato De Sangue"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "esqueletopeconhento":
            inimigo = EsqueletoPeconhento(x, y, 96, 96, hp=200 if not elite else 300)
            inimigo.nome_base = "Esqueleto Peçonhento"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "aranhadosol":
            inimigo = AranhaDoSol(x, y, 48, 48, hp=110 if not elite else 300)
            inimigo.nome_base = "Aranha Sol"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "arqueiro":
            inimigo = Arqueiro(x, y, 128, 128, hp=140 if not elite else 300)
            inimigo.nome_base = "Arqueiro"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "vampirosol":
            inimigo = VampiroSol(x, y, 96, 96, hp=250 if not elite else 300)
            inimigo.nome_base = "Vampiro Sol"
            inimigo.aplicar_modificadores(elite=elite)

        elif tipo_escolhido == "magoelementar":
            inimigo = MagoElementar(x, y, 96, 96, hp=80 if not elite else 300)
            inimigo.nome_base = "Mago Elementar"
            inimigo.aplicar_modificadores(elite=elite)

        # Adicione outros tipos de inimigos aqui no futuro:
        # elif tipo_escolhido == "novo_inimigo":
        #     inimigo = NovoInimigo(x, y, ...)

        return inimigo


    def particulas_fumaça(self,x,y):
        return{'x': x + randint(-10,20),
               'y': y + randint(-10,10),
               "size": randint(5,15),
               'alpha': randint(30,100),
               'life': randint(500,1000),
               'created': time.get_ticks(),
               'color': (228, 212, 211)
               }


    def atualizar(self,dt,teclas, eventos):

        agora = time.get_ticks()
        if agora - self.portal_last_update >= self.portal_frame_delay:
            self.portal_last_update = agora
            self.portal_frame_idx = (self.portal_frame_idx + 1) % len(self.portal_frames)

        if self.cutscene and self.cutscene.ativa:
            self.cutscene.update(eventos)  # ou eventos se estiver usando eventos
            return  # pausa o resto da sala

        agora = time.get_ticks()

        temp_rect_player = Rect(self.player.get_hitbox().x, self.player.get_hitbox().y+90, self.player.get_hitbox().width, self.player.get_hitbox().height-90)
        em_espinhos = any(temp_rect_player.colliderect(e) for e in self.mapa.get_espinhos())

        if em_espinhos:
            if not self.player.em_espinhos:
                self.player.em_espinhos = True
                self.player.velocidadeMov = 0.2
                self.player.tomar_dano(10)
                self.player.tempo_ultimo_dano_espinhos = time.get_ticks()

            elif time.get_ticks() - self.player.tempo_ultimo_dano_espinhos >= self.player.cooldown_dano_espinhos:
                self.player.tomar_dano(10)
                self.player.tempo_ultimo_dano_espinhos = time.get_ticks()


        else:
            if self.player.em_espinhos:
                self.player.em_espinhos = False
                self.player.velocidadeMov = self.player.velocidade_base

        if not any(inimigo.vivo for inimigo in self.inimigos) and self.leve_atual < self.max_leves:
            if not self.aguardando_nova_leva:
                self.aguardando_nova_leva = True
                self.tempo_ultima_leva = agora
            elif agora - self.tempo_ultima_leva >= self.cooldown_entre_levas:
                self.aguardando_nova_leva = False
                nova_leva = self._criar_inimigos()
                self.inimigos.extend(nova_leva)

                for inimigo in nova_leva:
                    self.colisao.adicionar_entidade(inimigo)

        for inimigo in self.inimigos:
            if inimigo.vivo and self.player.hp > 0:
                p_rect = Rect(self.player.x, self.player.y, 60, 120)

                if isinstance(inimigo, (EsqueletoGelo, EsqueletoPeconhento)):
                    inimigo.atualizar(p_rect.center, self.tela, self.mapa.matriz, self.mapa.get_offset(), self.player)
                elif isinstance(inimigo, (bossmod.MouthOrb, MouthOrb2)):
                    inimigo.atualizar(p_rect.center, self.tela, self)
                elif isinstance(inimigo, (NuvemBoss, NuvemBoss2)):
                    inimigo.atualizar(p_rect.center, self.tela, self.player)
                elif isinstance(inimigo, (Orb, Espectro, Massa, Furacao, CaveiraDeFogo, Polvo)):
                    inimigo.atualizar(p_rect.center, self.tela)
                else:
                    inimigo.atualizar(p_rect.center, self.tela, self.mapa.matriz, self.mapa.get_offset())
                
                inimigo.dar_dano = lambda val=inimigo.dano: self.player.tomar_dano(val)


        self.colisao.checar_colisoes(dt)
        for inimigo in self.inimigos:
            if inimigo not in self.colisao.entidades:
                self.colisao.adicionar_entidade(inimigo)

        if not self.visitada:
            self.porta_liberada = False
            if self.player.x > 50 and self.player.x < self.tela.get_width() - 50:
                self.visitada = True
        else:
            self.porta_liberada = (not any(inimigo.vivo for inimigo in self.inimigos) and self.leve_atual >= self.max_leves and not self.aguardando_nova_leva)

        if self.pode_trocar_de_sala() and teclas[K_e]:
            original_pos = (self.player.x, self.player.y)
            original_vel = (self.player.vx, self.player.vy)

            try:
                # Remove efeitos do item ativo atual (se existir e não afetar inimigos)
                if hasattr(self.player, 'itemAtivo') and self.player.itemAtivo is not None:
                    if not self.player.itemAtivo.afetaIni:
                        # Remove os efeitos
                        self.player.itemAtivo.remover_efeitos(self.player)

                        # Restaura a posição/velocidade
                        self.player.x, self.player.y = original_pos
                        self.player.vx, self.player.vy = original_vel

                        # Atualiza atributos para garantir consistência
                        self.player.atualizar_atributos()

                # Remove efeitos do item ativo esgotado (se existir e não afetar inimigos)
                if hasattr(self.player, 'itemAtivoEsgotado') and self.player.itemAtivoEsgotado is not None:
                    if not self.player.itemAtivoEsgotado.afetaIni:
                        # Faz backup dos atributos antes de remover
                        atributos_backup = self.player.atributos.copy()

                        # Remove os efeitos
                        self.player.itemAtivoEsgotado.remover_efeitos(self.player)

                        # Restaura a posição/velocidade
                        self.player.x, self.player.y = original_pos
                        self.player.vx, self.player.vy = original_vel

                        # Atualiza atributos para garantir consistência
                        self.player.atributos = atributos_backup
                        self.player.atualizar_atributos()

                    self.player.itemAtivoEsgotado = None

            except Exception as e:
                print(f"Erro ao remover efeitos de item ativo: {e}")
                # Garante que a posição/velocidade seja restaurada mesmo em caso de erro
                self.player.x, self.player.y = original_pos
                self.player.vx, self.player.vy = original_vel
                if hasattr(self.player, 'atributos'):
                    self.player.atualizar_atributos()
            self.player.player_rect.topleft = (self.player.x, self.player.y)



            self._trocar_de_sala()


        if self.porta_liberada and self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]['tipo'] == 'boss' and any(self.player.get_hitbox().colliderect(portal) for portal in self.mapa.get_trocar_andar()) and teclas[K_e]:
            original_pos = (self.player.x, self.player.y)
            original_vel = (self.player.vx, self.player.vy)

            if self.player.itemAtivo is not None:
                if not self.player.itemAtivo.afetaIni:
                    # Remove efeitos mas mantém a posição/velocidade
                    self.player.itemAtivo.remover_efeitos(self.player)
                    self.player.x, self.player.y = original_pos
                    self.player.vx, self.player.vy = original_vel


            if self.player.itemAtivoEsgotado is not None :
                if not self.player.itemAtivoEsgotado.afetaIni:
                    self.player.itemAtivoEsgotado.remover_efeitos()
                    self.player.x, self.player.y = original_pos
                    self.player.vx, self.player.vy = original_vel
                self.player.itemAtivoEsgotado = None
            self.player.player_rect.topleft = (self.player.x, self.player.y)

            self.avancar_andar()


        if self.bau:
            self.bau.update(player_hitbox=self.player.get_hitbox())

            if not self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual].get("bau_aberto", False):
                if self.player.get_hitbox().colliderect(self.bau.rect) and teclas[K_e] and self.porta_liberada:
                    if not self.bau.aberto:
                        self.bau.abrir()
                        self.player.vx = 0
                        self.player.vy = 0
                        self.player.travado = True


            if (self.bau.aberto and not self.bau.animando and not self.ativar_menu_bau and not self.bau_interagido and self.player.get_hitbox().colliderect(self.bau.rect)):
                self.ativar_menu_bau = True
                self.bau_interagido = True

            if not self.bau.menu_ativo and self.ativar_menu_bau:
                self.ativar_menu_bau = False
                self.player.travado = False

        now = time.get_ticks()

        if not self.gerenciador_andar.sala_foi_conquistada(self.gerenciador_andar.sala_atual):
            if (not any(inimigo.vivo for inimigo in self.inimigos)) and self.leve_atual < self.max_leves:
                som.tocar("Spawn")
                # entre levas, mostrar fumaça
                if now - int(self.ultima_fumaça) > self.intervalo_fumaça:
                    for x, y in self.spawn_points:
                        self.fumaça_particula.append(self.particulas_fumaça(x, y))
                    self.ultima_fumaça = now

                for particula in self.fumaça_particula[:]:
                    particula['alpha'] -= 0.4
                    particula['size'] += 0.2
                    if now - particula['created'] > particula['life'] or particula['alpha'] <= 0:
                        self.fumaça_particula.remove(particula)
            else:
                self.fumaça_particula.clear()

        if (any((inimigo.vivo for inimigo in
                 self.inimigos)) or self.leve_atual < self.max_leves) and not self.gerenciador_andar.sala_foi_conquistada(
                self.gerenciador_andar.sala_atual):
            if self.boss_musica == 0:
                musica.tocar(self.musica_escolhida, fade_ms=1000)
        elif self.boss_musica == 0 and (not self.loja or self.loja.musica == 0):
            musica.tocar(resource_path("BloodVein SCORE/OST/MapaForadoCombate.mp3"), fade_ms=1000)
            self.musica_escolhida = choice(self.musicas_de_combate)

        for evento in eventos:
            if evento.type == MOUSEBUTTONDOWN and evento.button == 1:
                for botao, arma in self.loots[:]:
                    if botao.checkForInput(mouse.get_pos()):
                        if len(self.player.inventario) < 21:
                            arma.aplicaModificador()
                            self.player.inventario.append(arma)
                            self.loots.remove((botao, arma))
                        else:
                            self.inventario_cheio_msg = "Inventário cheio!"
                            self.inventario_cheio_tempo = time.get_ticks()



    def desenhar_inimigos(self, tela):
        offset_x, offset_y = screen_shaker.offset
        for inimigo in self.inimigos:
            if inimigo.vivo:
                inimigo.desenhar(tela, (self.player.x, self.player.y), offset=(offset_x, offset_y))
            else:
                if not getattr(inimigo, "alma_coletada", True):
                    if not hasattr(inimigo, "vai_dropar_alma"):
                        inimigo.vai_dropar_alma = randint(0, 1) == 1  # decide 50/50 uma vez
                    if inimigo.vai_dropar_alma:
                        pos = (inimigo.x + 16, inimigo.y + 16)
                        self.desenha_alma(pos)
                        alma_hitbox = Rect(0, 0, 100, 100)
                        alma_hitbox.center = pos
                        if self.player.get_hitbox().colliderect(alma_hitbox):
                            self.player.almas += 1
                            inimigo.alma_coletada = True
                if not getattr(inimigo, "pocao_coletada", True):
                    if not hasattr(inimigo, "vai_dropar_pocao"):
                        pode_dropar_hp = self.player.pocoesHp < 4
                        pode_dropar_mp = self.player.pocoesMp < 4

                        if pode_dropar_hp or pode_dropar_mp:
                            inimigo.vai_dropar_pocao = randint(1, 3) == 1
                            if inimigo.vai_dropar_pocao:
                                tipos_disponiveis = []
                                if pode_dropar_hp:
                                    tipos_disponiveis.append("hp")
                                if pode_dropar_mp:
                                    tipos_disponiveis.append("mp")

                                inimigo.tipo_pocao = choice(tipos_disponiveis)
                        else:
                            inimigo.vai_dropar_pocao = False
                            inimigo.pocao_coletada = True

                    if inimigo.vai_dropar_pocao:
                        pos = (inimigo.x + 64, inimigo.y + 16)
                        self.desenha_pocao(pos, inimigo.tipo_pocao)
                        pocao_hitbox = Rect(0, 0, 50, 50)
                        pocao_hitbox.center = pos
                        if self.player.get_hitbox().colliderect(pocao_hitbox):
                            if inimigo.tipo_pocao == "hp":
                                self.player.pocoesHp += 1
                            else:
                                self.player.pocoesMp += 1
                            inimigo.pocao_coletada = True
                if not getattr(inimigo, "loot_coletado", True):
                    if not hasattr(inimigo, "vai_dropar_loot"):
                        inimigo.vai_dropar_loot = randint(1, 100) <= 30 # 30% de chance de cair loot

                    if getattr(inimigo, "vai_dropar_loot", False) and not hasattr(inimigo, "loot_botao_criado"):
                        pos = (inimigo.x + 16, inimigo.y + 32)
                        chance = randint(1, 100)
                        if chance <= dificuldade_global.chance("lendaria"):
                            raridade = "lendaria"
                            cor = (255, 255, 0)
                        elif chance <= dificuldade_global.chance("raro"):
                            raridade = "raro"
                            cor = (128, 0, 128)
                        elif chance <= dificuldade_global.chance("incomum"):
                            raridade = "incomum"
                            cor = (0, 255, 0)
                        else:
                            raridade = "comum"
                            cor = (255, 255, 255)

                        arma_tipo = choice([
                            LaminaDaNoite, Chigatana, Karambit, EspadaDoTita,
                            MachadoDoInverno, EspadaEstelar, MarteloSolar, Arco
                        ])
                        arma = arma_tipo(raridade, self.lista_mods)

                        # Carrega a imagem da bola
                        bola_img = transform.scale(image.load(resource_path(f"assets/itens/bola{raridade}.png")), (64, 64))

                        # Cria o botão com a bola como imagem
                        fontinha = font.Font(resource_path('assets/fontes/alagard.ttf'), 18)
                        botao = Botao(
                            image=bola_img,
                            pos=pos,
                            text_input=arma.nome,
                            font=fontinha,
                            base_color=cor,
                            hovering_color=cor,
                            value=arma
                        )

                        # Ajusta a posição do retângulo para centralizar a bola
                        botao.rect = bola_img.get_rect(center=(pos[0], pos[1]))

                        self.loots.append((botao, arma))
                        inimigo.loot_botao_criado = True

    def desenhar(self, tela):

        if self.cutscene and self.cutscene.ativa:
            self.cutscene.draw(self.tela)
            return

        offset_x, offset_y = screen_shaker.offset
        self.mapa.desenhar(self.porta_liberada)



        if self.bau:
            bau_pos = (self.bau.rect.x + offset_x, self.bau.rect.y + offset_y)

            if self.porta_liberada and not self.bau.aberto:
                # Criar uma máscara da imagem do baú
                bau_mask = pygame.mask.from_surface(self.bau.image)
                outline_points = bau_mask.outline()

                # Superfície para o contorno com tamanho idêntico à imagem do baú
                outline_surface = Surface(self.bau.image.get_size(), SRCALPHA)

                # Desenhar o contorno (outline) diretamente na posição certa
                espessura = 3  # Aumente esse valor para contornos mais grossos
                for dx in range(-espessura, espessura + 1):
                    for dy in range(-espessura, espessura + 1):
                        if dx == 0 and dy == 0:
                            continue
                        for x, y in outline_points:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < outline_surface.get_width() and 0 <= ny < outline_surface.get_height():
                                outline_surface.set_at((nx, ny), (255, 255, 255, 255))

                # Desenhar brilho pulsante
                tempo = time.get_ticks() / 500
                alpha = int(100 + 80 * math.sin(tempo))
                # Criar brilho maior que o baú
                brilho_size = (self.bau.image.get_width() + 20, self.bau.image.get_height() + 20)
                brilho = Surface(brilho_size, SRCALPHA)

                # Desenhar elipse centralizada no brilho
                draw.ellipse(brilho, (255, 255, 150, alpha), brilho.get_rect())

                # Calcular posição para centralizar brilho em cima do baú
                brilho_pos = (
                    bau_pos[0] - (brilho.get_width() - self.bau.image.get_width()) // 2,
                    bau_pos[1] - (brilho.get_height() - self.bau.image.get_height()) // 2
                )

                # Blit do brilho no lugar certo
                tela.blit(brilho, brilho_pos)

                # Desenhar o outline na mesma posição do baú
                tela.blit(outline_surface, bau_pos)

            # Desenhar o baú por cima do contorno e brilho
            tela.blit(self.bau.image, bau_pos)

        if self.pode_trocar_de_sala() and not self.em_transicao:
            texto = self.alagard.render(f"Aperte E para entrar na porta", True, (255, 255, 255))
            rect_texto = texto.get_rect(center=(tela.get_width() // 2, 50))
            tela.blit(texto, rect_texto)

        if self.bau and not self.bau.aberto and self.player.get_hitbox().colliderect(self.bau.rect) and self.porta_liberada:
            texto_bau = self.alagard.render("Aperte E para abrir o baú", True, (255, 255, 255))
            rect_bau = texto_bau.get_rect(center=(tela.get_width() // 2, 50))
            tela.blit(texto_bau, rect_bau)

        if self.hitbox_loja():
            if self.player.get_hitbox().colliderect(self.hitbox_loja()[0]):
                texto_loja = self.alagard.render("Aperte E para entrar na loja", True, (255, 255, 255))
                rect_loja = texto_loja.get_rect(center=(tela.get_width() // 2, 50))
                tela.blit(texto_loja, rect_loja)

        offset_x, offset_y = screen_shaker.offset

        # Desenhar fumaça nos spawn points
        for particula in self.fumaça_particula:
            s = Surface((particula['size'] * 2, particula['size'] * 2), SRCALPHA)
            draw.circle(
                s,
                (*particula['color'], particula['alpha']),
                (particula['size'], particula['size']),
                particula['size']
            )
            tela.blit(s, (
                particula['x'] - particula['size'] + offset_x,
                particula['y'] - particula['size'] + offset_y
            ))


        if self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]['tipo'] == 'loja':
            self.tela.blit(self.lojista_img, (950 + offset_x, 490 + offset_y))


        #debug visual das colisões do player e do mapa:
        # for collider in self.mapa.get_colliders():
        #     draw.rect(tela, (255,0,0), collider['rect'], 1)
        # draw.rect(tela, (0,255,0), self.player.player_rect, 2)
        for botao, arma in self.loots:
            # if len(self.loots) < 0:
            #     print("cucucucucu")
            self.tela.blit(botao.image, botao.rect)

            mouse_pos = mouse.get_pos()
            if botao.rect.collidepoint(mouse_pos):
                botao.changeColor(mouse_pos)

                texto_render = botao.font.render(botao.text_input, True, botao.hovering_color)
                largura = texto_render.get_width() + 20
                altura = texto_render.get_height() + 10

                texto_x = botao.x_pos - largura // 2
                texto_y = botao.y_pos - 50

                fundo = Surface((largura, altura), SRCALPHA)
                fundo.fill((0, 0, 0, 160))
                self.tela.blit(fundo, (texto_x, texto_y))

                # Texto
                self.tela.blit(texto_render, (texto_x + 10, texto_y + 5))
        if time.get_ticks() - self.inventario_cheio_tempo < self.inventario_cheio_duracao and self.inventario_cheio_msg:
            font_msg = font.Font(resource_path('assets/fontes/alagard.ttf'), 36)
            texto = font_msg.render(self.inventario_cheio_msg, True, (255, 0, 0))
            texto_rect = texto.get_rect(center=(self.tela.get_width() // 2, self.tela.get_height() - 75))

            # Add background for better visibility
            bg_rect = Rect(0, 0, texto.get_width() + 20, texto.get_height() + 10)
            bg_rect.center = (self.tela.get_width() // 2, self.tela.get_height() - 50)
            bg_surface = Surface(bg_rect.size, SRCALPHA)
            bg_surface.fill((0, 0, 0, 180))
            self.tela.blit(bg_surface, bg_rect)

            self.tela.blit(texto, texto_rect)

        if self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]["tipo"] == "boss" and self.porta_liberada and self.gerenciador_andar.numero_andar != 4:
            offset_x, offset_y = screen_shaker.offset
            pos_x, pos_y = 1500 + offset_x, 600 + offset_y

            portal_frame = self.portal_frames[self.portal_frame_idx]
            self.tela.blit(portal_frame, (pos_x, pos_y))

        agora = time.get_ticks()  # milissegundos

        if (
            self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]["tipo"] == "boss"
            and self.porta_liberada
            and self.gerenciador_andar.numero_andar == 4
        ):
            if self.vitoria_inicio is None:
                self.vitoria_inicio = agora
            elif agora - self.vitoria_inicio >= 3000:
                self.game_vitoria = True
        else:
            self.vitoria_inicio = None


        # # DEBUG: Desenhar grade e caminho
        # offset_x, offset_y = self.mapa.get_offset()
        # tile_size_scaled = 32 * 3.25

        # # 1. Desenhar grade de tiles
        # for y in range(self.mapa.tmx_data.height + 1):
        #     draw.line(
        #         tela, (100, 100, 100, 150),
        #         (offset_x, offset_y + y * tile_size_scaled),
        #         (offset_x + self.mapa.tmx_data.width * tile_size_scaled, offset_y + y * tile_size_scaled),
        #         1
        #     )
        # for x in range(self.mapa.tmx_data.width + 1):
        #     draw.line(
        #         tela, (100, 100, 100, 150),
        #         (offset_x + x * tile_size_scaled, offset_y),
        #         (offset_x + x * tile_size_scaled, offset_y + self.mapa.tmx_data.height * tile_size_scaled),
        #         1
        #     )

        # # 2. Desenhar caminho do inimigo
        # for inimigo in self.inimigos:
        #     if not inimigo.vivo:
        #         continue
        #     if hasattr(inimigo, 'caminho_atual') and inimigo.caminho_atual:
        #         for i, (gx, gy) in enumerate(inimigo.caminho_atual):
        #             px, py = grid_para_pixel(
        #                 gx, gy,
        #                 self.mapa.get_offset(),
        #                 tile_size_scaled
        #             )
        #             # Desenhar ponto do caminho
        #             draw.circle(tela, (0, 255, 0), (int(px), int(py)), 5)

        #             # Desenhar linha entre pontos
        #             if i > 0:
        #                 prev_px, prev_py = grid_para_pixel(
        #                     inimigo.caminho_atual[i-1][0], inimigo.caminho_atual[i-1][1],
        #                     self.mapa.get_offset(),
        #                     tile_size_scaled
        #                 )
        #                 draw.line(tela, (0, 200, 0), (prev_px, prev_py), (px, py), 2)

        # # 3. Desenhar posição atual em grid
        # for inimigo in self.inimigos:
        #     if not inimigo.vivo:
        #         continue
        #     gx, gy = pixel_para_grid(
        #         inimigo.x, inimigo.y,
        #         self.mapa.get_offset(),
        #         tile_size_scaled
        #     )
        #     text = fonte.render(f"({gx},{gy})", True, (255, 255, 255))
        #     tela.blit(text, (inimigo.x - 20, inimigo.y - 30))



    def pode_trocar_de_sala(self):

        return self.porta_liberada and any(self.player.get_hitbox().colliderect(rangee['colisor']) for rangee in self.ranges_doors)


    def _trocar_de_sala(self):
        if self.em_transicao:
            return
        self.fade(fade_in=False, duration=2000)
        som.tocar('passar_porta')
        for porta in self.ranges_doors:
            if self.player.get_hitbox().colliderect(porta['colisor']) and self.porta_liberada:


                self.em_transicao = True



                if not any(inimigo.vivo for inimigo in self.inimigos) and self.leve_atual >= self.max_leves:
                    self.gerenciador_andar.marcar_sala_conquistada(self.gerenciador_andar.sala_atual)

                codigo_porta = porta['codigoporta']

                if codigo_porta in self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual].get("portas", {}):

                    direcao_porta = codigo_porta
                    nova_sala = self.gerenciador_andar.ir_para_proxima_sala(codigo_porta)

                    if nova_sala:
                        nova_instancia = Sala(nova_sala, self.tela, self.player, self.gerenciador_andar, self.set_minimapa)

                        nova_instancia.player = self.player
                        nova_instancia.gerenciador_andar = self.gerenciador_andar

                        if direcao_porta == 'cima':
                            nova_instancia.player.player_rect.topleft = (914, 644)
                        elif direcao_porta == 'baixo':
                            nova_instancia.player.player_rect.topleft = (914, 176)
                        elif direcao_porta == 'esquerda':
                            nova_instancia.player.player_rect.topleft = (1550, 350)
                        elif direcao_porta == 'direita':
                            nova_instancia.player.player_rect.topleft = (300, 350)
                        else:
                            nova_instancia.player.player_rect.topleft = (self.tela.get_width() // 2, self.tela.get_height() // 2)

                        self.__dict__.update(nova_instancia.__dict__)

                        self.player.proibir_dash_ate = time.get_ticks() + 1000

                        self.player.resetar_estado_temporario()




                        print(f"Transição para: {nova_sala} via {codigo_porta}")
                        self.em_transicao = False
                        self.fade(fade_in=True, duration=2000)
                        return
                break


    def desenha_alma(self,pos):
        tempo_atual = time.get_ticks()
        if tempo_atual - self.tempo_anterior_alma >= self.duracao_frame_alma:
            self.tempo_anterior_alma = tempo_atual
            self.frame_alma_idx = (self.frame_alma_idx + 1) % len(self.frames_alma)

        frame = self.frames_alma[self.frame_alma_idx]
        frame = transform.scale(frame, (64, 64))
        rect = frame.get_rect(center=pos)
        self.tela.blit(frame, rect)

    def desenha_pocao(self, pos, tipo):
        if tipo == "hp":
            pocao_img = self.pocoesHp
        else:
            pocao_img = self.pocoesMp

        pocao_img = transform.scale(pocao_img, (32, 32))
        rect = pocao_img.get_rect(center=pos)
        self.tela.blit(pocao_img, rect)

    def fade(self, fade_in=True, duration=500):
        """Efeito de transição de fade (para entrada ou saída de sala)
        Args:
            fade_in (bool): Se True, fade de preto para tela (entrada). Se False, fade para preto (saída).
            duration (int): Duração total do efeito em milissegundos.
        """

        fade_surface = Surface((1425,775), SRCALPHA)
        steps = 30
        #delay = max(1, duration // steps)  # Garante pelo menos 1ms de delay

        if fade_in:
            # Fade in (preto -> tela)
            for alpha in range(255, -1, -255 // steps):
                self.desenhar(self.tela)
                fade_surface.fill((0, 0, 0, alpha))
                self.tela.blit(fade_surface, (248,100))
                display.flip()
                #time.delay(delay)
        else:
            # Fade out (tela -> preto)
            for alpha in range(0, 256, 255 // steps):
                self.desenhar(self.tela)
                fade_surface.fill((0, 0, 0, alpha))
                self.tela.blit(fade_surface, (248,100))
                display.flip()
                #time.delay(delay)

    def avancar_andar(self):
        # Verifica se é sala do boss e se colidiu com o portal
        portal = self.mapa.get_trocar_andar()
        if (self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]['tipo'] == 'boss' and
            self.player.get_hitbox().colliderect(portal[0]) and
            self.porta_liberada):

            self.boss_musica = 0

            # Pré-salva o andar atual (opcional)
            andar_num = self.gerenciador_andar.numero_andar
            import shutil
            shutil.copy(resource_path('data/andar_atual.json'), resource_path(f'data/backup_andar{andar_num}.json'))

            # Avança para o próximo andar
            self.gerenciador_andar.numero_andar += 1
            self.gerenciador_andar.gerar_andar(self.gerenciador_andar.numero_andar)

            # Recria a sala com o novo andar
            spawn_id = self.gerenciador_andar.get_sala_spawn()
            self.gerenciador_andar.sala_atual = spawn_id
            caminho_tmx = self.gerenciador_andar.get_arquivo_atual()

            from minimapa import Minimapa
            self.set_minimapa(Minimapa(self.gerenciador_andar, self.tela))

            nova_sala = Sala(
                caminho_tmx,
                self.tela,
                self.player,
                self.gerenciador_andar,
                self.set_minimapa
            )
            self.__dict__.update(nova_sala.__dict__)

    def get_save_data(self):
        return {
            'porta_liberada': self.porta_liberada,
            'visitada': self.visitada,
            'bau': {
                'aberto': self.bau.aberto if self.bau else False,
                'interagido': self.bau_interagido,
                'menu_ativo': getattr(self, 'ativar_menu_bau', False)
            } if self.bau else None,
            'em_transicao': self.em_transicao
        }

    def load_save_data(self, data, conjunto_itens):

        self.porta_liberada = data['porta_liberada']
        self.visitada = data['visitada']
        self.em_transicao = data.get('em_transicao', False)


        if data['bau'] and self.bau:
            self.bau.aberto = data['bau']['aberto']
            self.bau_interagido = data['bau']['interagido']
            self.ativar_menu_bau = data['bau']['menu_ativo']

            if self.bau.aberto:
                self.bau.animando = False
                self.bau.frame_index = len(self.bau.frames) - 1
                self.bau.image = self.bau.frames[-1]

        self.colisao.entidades = [self.player] + self.inimigos


    def hitbox_loja(self):
        tipo_sala = self.gerenciador_andar.grafo.nodes[self.gerenciador_andar.sala_atual]["tipo"]
        if not 'loja' in tipo_sala:
            return []

        range_loja = self.mapa.get_rangeloja()

        return range_loja if range_loja else []

