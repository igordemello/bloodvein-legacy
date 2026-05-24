from pygame import *
import sys
from pygame.locals import QUIT
import math
from bau import Bau
from config import Config
from hud import Hud
from inimigo import Inimigo
from player import Player
from botao import Botao
from mapa import Mapa
from colisao import Colisao
from inimigos.orb import Orb
from inimigos.MouthOrbBoss import MouthOrb
from sala import Sala
from itensDic import *
from gerenciador_andar import GerenciadorAndar
from menu import Menu
from menu import gerenciamento
from loja import Loja
from minimapa import Minimapa
from menuarmas import *
from screen_shake import screen_shaker
from save_manager import SaveManager
from som import GerenciadorDeSom
from som import som
from pause import Pause
import os
from gameover import GameOver
import shutil
from som import GerenciadorDeMusica
from som import musica
from inventario import Inventario
from torch import TorchManager, Torch
from enum import Enum, auto
from dificuldade import dificuldade_global
from utils import resource_path
from discord_rpc import DiscordRPC
from input_manager import InputManager

BASE_W = 1920
BASE_H = 1080

class EstadoDoJogo(Enum):
    MENU = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    INVENTARIO = auto()
    GAME_OVER = auto()
    ESCOLHA_ARMA = auto()
    LOJA = auto()
    BAU = auto()
    CUTSCENE = auto()
    CONTROLES = auto()
    CREDITOS = auto()
    VITORIA = auto()
    CONFIG = auto()

class Game:
    def __init__(self):
        init()
        joystick.init()

        if joystick.get_count() > 0:
            self.joystick = joystick.Joystick(0)
            self.joystick.init()
        else:
            self.joystick = None

        self.input = InputManager(self.joystick)

        self.clock = time.Clock()

        info = display.Info()

        self.monitor_w, self.monitor_h = info.current_w, info.current_h
        self.largura, self.altura = self.monitor_w, self.monitor_h
        # self.largura, self.altura = (1280,720)
        self.window = display.set_mode(
            (self.largura, self.altura),
            flags= DOUBLEBUF | FULLSCREEN | HWSURFACE,
            vsync=1
        )

        self.render_surface = Surface((BASE_W, BASE_H))

        self.screen = self.render_surface

        self.scale_x = self.largura / BASE_W
        self.scale_y = self.altura / BASE_H

        self.config = Config(self.screen, self)

        display.set_caption("Blood Vein")
        mouse.set_visible(False)
        logo = image.load(resource_path('assets/logo.png'))
        display.set_icon(logo)

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)

        self.imagem_cursor = transform.scale(image.load(resource_path('assets/UI/cursor.png')).convert_alpha(),
                                             (32, 32))
        self.imagem_cursor_click = transform.scale(
            image.load(resource_path('assets/UI/cursor_click.png')).convert_alpha(), (32, 32))
        self.cursor_clicando = False

        self.dados_run_salvos = None

        self.estado = EstadoDoJogo.MENU
        self.config_origem = EstadoDoJogo.MENU
        self.fonte = font.Font(resource_path('assets/fontes/alagard.ttf'), 48)
        self.fps_font = font.SysFont("Arial", 24)
        self.fps_text = self.fps_font.render("FPS: 60", True, (255, 255, 255))

        self.save_manager = SaveManager()
        self.pause = Pause()
        self.game_over = GameOver()
        self.menu = Menu(self.screen)

        self.mensagem_salvo = None
        self.tempo_mensagem_salvo = 0

        self.bau_foi_aberto_esse_frame = False

        self.player = None
        self.hud = None
        self.andar = None
        self.minimapa = None
        self.sala_atual = None
        self.menu_armas = None
        self.inventario = None
        self.menu_armas_ativo = None

        self.cd_arma_jogo = 350
        self.foi_pra_jogo = 0

        self.imagem_fundo_pause = None

        self.imagem_controles = image.load(resource_path('assets/tela_controles_VERSAO_DE_GENTE.png')).convert_alpha()
        self.imagem_vitoria = image.load(resource_path('assets/fim-de-jogo.png')).convert_alpha()
        self.imagem_creditos = image.load(resource_path('assets/tela_creditos.png')).convert_alpha()

        self.discord = DiscordRPC()
        self.discord.conectar()
        self.rpc_estado_atual = None
        self.atualizar_rpc(
            estado=f"No menu",
            detalhes=f"Aguardando para iniciar",
            imagem="logo"
        )


    def criar_luz(self, raio):
        luz = Surface((raio * 2, raio * 2), SRCALPHA)

        for r in range(raio, 0, -1):
            alpha = int(200 * (1 - (r / raio)) ** 2)
            draw.circle(
                luz,
                (0, 0, 0, alpha),
                (raio, raio),
                r
            )

        return luz
    
    def aplicar_luz(self):
        # escurece tudo
        self.darkness.fill((0, 0, 0, 125))

        # centro do player
        px, py = self.player.player_rect.center
        raio = self.luz_player.get_width() // 2

        # posição da luz
        pos_luz = (px - raio, py - raio)

        # remove a escuridão onde a luz passa
        self.darkness.blit(
            self.luz_player,
            (px - raio, py - raio),
            special_flags=BLEND_RGBA_SUB
        )


    def resetar_jogo(self, com_nova_run=False):
        self.player = Player(950, 400, 32 * 2, 48 * 2, self.joystick)
        self.hud = Hud(self.player, self.screen)
        self.player.set_hud(self.hud)
        self.andar = GerenciadorAndar()
        self.minimapa = Minimapa(self.andar, self.screen)
        self.sala_atual = Sala("andar1/spawn.tmx", self.screen, self.player, self.andar, self.set_minimapa)
        self.menu_armas = MenuArmas(self.hud)
        if com_nova_run:
            self.dados_run_salvos = {
                "arma_data": self.menu_armas.arma_atual.get_save_data(),
                "arma_tipo": self.menu_armas.arma_atual.__class__.__name__,
                "modificador" : self.menu_armas.arma_atual.modificador.nome,
                'modificador_detalhes': {
                    'nome': self.menu_armas.arma_atual.modificador.nome,
                    'valor': self.menu_armas.arma_atual.modificador.valor
                },
                "dificuldade": self.menu_armas.dificuldades[self.menu_armas.dificuldade_selecionada],
                "trait": self.menu_armas.traits[self.menu_armas.trait_selecionada]
            }
        self.inventario = Inventario(self.screen, self.player, self.hud)
        self.menu_armas_ativo = com_nova_run
        self.darkness = Surface((1920, 1080), SRCALPHA)
        # self.darkness.fill((0, 0, 0, 220))

        self.luz_player = self.criar_luz(500)

        self.torch_manager = TorchManager()

        self.torch_manager.add(
            Torch(600, 240, self.criar_luz, self.andar, inferior=False)
        )

        self.torch_manager.add(
            Torch(1300, 240, self.criar_luz, self.andar,inferior=False)
        )

        # tochas inferiores

        self.torch_manager.add(
            Torch(600, 800, self.criar_luz, self.andar,inferior=True)
        )

        self.torch_manager.add(
            Torch(1300, 800, self.criar_luz, self.andar,inferior=True)
        )

    def reiniciar_run_salva(self):
        if not self.dados_run_salvos:
            return

        from dificuldade import dificuldade_global
        from armas import ListaMods

        dificuldade_global.set_dificuldade(self.dados_run_salvos["dificuldade"])

        trait_salva = self.dados_run_salvos["trait"]

        # Resetar tudo
        self.resetar_jogo(com_nova_run=False)

        if not self.menu_armas:
            self.menu_armas = MenuArmas(self.hud)
        if trait_salva in self.menu_armas.traits:
            self.menu_armas.trait_selecionada = self.menu_armas.traits.index(trait_salva)

        atributos_por_trait = {
            "Vampira": {"forca": 5, "destreza": 5, "agilidade": 5, "vigor": 5, "resistencia": 5, "estamina": 5,
                        "sorte": 5},
            "Ancião": {"forca": 3, "destreza": 6, "agilidade": 7, "vigor": 3, "resistencia": 4, "estamina": 6,
                       "sorte": 5},
            "Peçonhento": {"forca": 4, "destreza": 6, "agilidade": 5, "vigor": 6, "resistencia": 3, "estamina": 6,
                           "sorte": 4},
            "Mercúrio": {"forca": 4, "destreza": 7, "agilidade": 7, "vigor": 2, "resistencia": 4, "estamina": 6,
                         "sorte": 2},
            "Humano": {"forca": 3, "destreza": 3, "agilidade": 3, "vigor": 3, "resistencia": 3, "estamina": 3,
                       "sorte": 8}
        }
        if trait_salva in atributos_por_trait:
            self.player.atributos.update(atributos_por_trait[trait_salva])

        arma_tipo = self.dados_run_salvos["arma_tipo"]
        arma_data = self.dados_run_salvos["arma_data"]
        mods = ListaMods()
        arma_classe = getattr(__import__('armas'), arma_tipo)
        nova_arma = arma_classe(arma_data["raridade"], mods)
        nova_arma.load_save_data(arma_data, mods)

        mod_class = getattr(sys.modules[__name__], self.dados_run_salvos['modificador'])
        nova_arma.modificador = mod_class(nova_arma)
        if self.dados_run_salvos.get('modificador_detalhes'):
            nova_arma.modificador.valor = self.dados_run_salvos['modificador_detalhes']['valor']
            nova_arma.nome = f"{nova_arma.tipoDeArma} {nova_arma.modificador.nome} {nova_arma.raridadeStr}"


        self.player.arma = nova_arma

        self.player.set_hud(self.hud)
        self.player.atualizar_atributos()
        self.player.atualizar_arma()


    def set_minimapa(self, novo):
        self.minimapa = novo

    def loop(self):
        self.tela_intro()


        while True:
            dt = self.clock.tick(60)
            eventos = event.get()
            mx, my = mouse.get_pos()
            mouse_pos = (
                int(mx / self.scale_x),
                int(my / self.scale_y)
            )
            keys = key.get_pressed()

            for ev in eventos:
                if ev.type == QUIT:
                    self.discord.fechar()
                    quit()
                    sys.exit()

            screen_shaker.update(dt)
            self.tratar_eventos(eventos, mouse_pos, keys, dt)
            self.atualizar(dt, keys, eventos, mouse_pos)
            self.desenhar(mouse_pos)
            scaled = transform.smoothscale(
                self.render_surface,
                (self.largura, self.altura)
            )

            self.window.blit(scaled, (0,0))

            cursor_pos = (
                int(mouse_pos[0] * self.scale_x),
                int(mouse_pos[1] * self.scale_y)
            )

            if self.cursor_clicando:
                self.window.blit(self.imagem_cursor_click, cursor_pos)
            else:
                self.window.blit(self.imagem_cursor, cursor_pos)
            display.update()

    def tratar_eventos(self, eventos, mouse_pos, keys, dt):
        if self.estado == EstadoDoJogo.MENU:
            for ev in eventos:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    escolha = self.menu.checar_clique(mouse_pos)
                    if escolha == "jogo":
                        self.apagar_saves()
                        som.tocar("Startar")
                        self.resetar_jogo(com_nova_run=True)
                        self.estado = EstadoDoJogo.ESCOLHA_ARMA
                        self.atualizar_rpc(
                            estado=f"Escolhendo classe",
                            detalhes=f"Estudando os arquétipos",
                            imagem="logo"
                        )
                    elif escolha == "continuar":
                        som.tocar("click3")
                        try:
                            dados = self.save_manager.load_game(resource_path("save_file.json"))
                            self.resetar_jogo()
                            self.player.load_save_data(dados['player'], self.sala_atual.itensDisp,
                                                       self.player.lista_mods)
                            self.andar.load_save_data(dados['map'])
                            self.sala_atual = Sala(self.andar.get_arquivo_atual(), self.screen, self.player, self.andar,
                                                   self.set_minimapa)
                            self.sala_atual.load_save_data(dados['sala'], self.sala_atual.itensDisp)
                            self.estado = EstadoDoJogo.JOGANDO
                            self.atualizar_rpc(
                                estado=f"Explorando o castelo",
                                detalhes=f"Andar {self.andar.numero_andar}",
                                imagem="logo"
                            )
                            self.player.atualizar_arma()
                            self.player.atualizar_atributos()
                        except Exception as e:
                            print(f"Erro ao carregar jogo: {e}")

                    elif escolha == "creditos":
                        self.estado = EstadoDoJogo.CREDITOS
                    elif escolha == "controles":
                        self.estado = EstadoDoJogo.CONTROLES
                    elif escolha == "opcoes":
                        self.config.modo_pause  = False
                        self.config_origem = EstadoDoJogo.MENU
                        self.estado = EstadoDoJogo.CONFIG
                    elif escolha == "sair":
                        self.discord.fechar()
                        quit()
                        sys.exit()

        elif self.estado == EstadoDoJogo.JOGANDO:
            self.player.tratar_eventos(eventos)
            for ev in eventos:
                if ev.type == KEYDOWN:
                    current_time = time.get_ticks()
                    # item ativo
                    if ev.key == K_q and current_time - self.player.ativo_ultimo_uso > 2500:
                        self.player.ativo_ultimo_uso = current_time
                        self.player.usarItemAtivo(self.sala_atual)
                    # hablidades
                    teclas_para_verificar = [K_1, K_2, K_3, K_4]
                    for i in range(4):
                        if ev.key == teclas_para_verificar[i] and self.player.hotkeys[i] != 0:
                            self.player.ativar_habilidade(self.player.hotkeys[i], mouse_pos)
                    # pocoes
                    if ev.key == K_c:
                        self.player.usar_pocao_vida()
                    if ev.key == K_v:
                        self.player.usar_pocao_mana()
                    if ev.key == K_PERIOD:
                        item_id = int(input("Digite o ID do item para debug: "))
                        encontrado = False
                        for item_nome, item in self.sala_atual.itensDisp.itens.items():
                            if hasattr(item, 'id') and item.id == item_id:
                                if isinstance(item, Item):
                                    self.player.adicionarItem(item)
                                elif isinstance(item, ItemAtivo):
                                    self.player.adicionarItem(item)
                                print(f"Item '{item_nome}' (ID {item_id}) adicionado ao jogador.")
                                encontrado = True
                                break

                    if ev.key == K_ESCAPE:
                        self.imagem_fundo_pause = self.screen.copy()
                        self.estado = EstadoDoJogo.PAUSADO
                        self.atualizar_rpc(
                            estado=f"Jogo pausado",
                            detalhes=f"Planejando o próximo movimento",
                            imagem="logo"
                        )
                    elif ev.key == K_i:
                        self.inventario.toggle()
                        self.estado = EstadoDoJogo.INVENTARIO if self.inventario.visible else EstadoDoJogo.JOGANDO
                    elif ev.key == K_TAB:
                        self.minimapa.toggle()
                    elif ev.key == K_e:
                        if self.sala_atual.hitbox_loja() and self.player.get_hitbox().colliderect(
                                self.sala_atual.hitbox_loja()[0]):
                            self.estado = EstadoDoJogo.LOJA
                elif ev.type == MOUSEBUTTONDOWN:
                    if ev.button == 1:
                        self.player.ataque_espadaPrincipal(self.sala_atual.inimigos, mouse_pos, dt)

                    elif ev.button == 3:
                        self.player.ataque_espadaSecundario(self.sala_atual.inimigos, mouse_pos, dt)


        elif self.estado == EstadoDoJogo.LOJA:
            for ev in eventos:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    resultado = self.sala_atual.loja.checar_compra(mouse_pos, self.screen)
                    if resultado == "sair":
                        self.estado = EstadoDoJogo.JOGANDO
                        self.atualizar_rpc(
                            estado=f"Explorando o castelo",
                            detalhes=f"Andar {self.andar.numero_andar}",
                            imagem="logo"
                        )


        elif self.estado == EstadoDoJogo.BAU:
            for ev in eventos:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    resultado = self.sala_atual.bau.checar_clique_bau(mouse_pos)

                    if resultado == "sair":
                        self.estado = EstadoDoJogo.JOGANDO
                        self.atualizar_rpc(
                            estado=f"Explorando o castelo",
                            detalhes=f"Andar {self.andar.numero_andar}",
                            imagem="logo"
                        )
                        self.sala_atual.bau.menu_ativo = False
                        self.sala_atual.ativar_menu_bau = False
                        self.sala_atual.player.travado = False
                    elif resultado:
                        self.player.adicionarItem(resultado)
                        self.sala_atual.gerenciador_andar.grafo.nodes[self.sala_atual.gerenciador_andar.sala_atual][
                            "bau_aberto"] = True
                        self.estado = EstadoDoJogo.JOGANDO
                        self.atualizar_rpc(
                            estado=f"Explorando o castelo",
                            detalhes=f"Andar {self.andar.numero_andar}",
                            imagem="logo"
                        )
                        self.sala_atual.bau.menu_ativo = False
                        self.sala_atual.ativar_menu_bau = False
                        self.sala_atual.player.travado = False

                    if resultado:
                        self.sala_atual.bau.menu_ativo = False
                        self.sala_atual.ativar_menu_bau = False
                        self.sala_atual.bau_interagido = False
                        self.sala_atual.player.travado = False
                        self.bau_foi_aberto_esse_frame = False

        elif self.estado == EstadoDoJogo.PAUSADO:
            print("PAUSE EVENT FRAME")  # Diagnóstico
            for ev in eventos:
                print(f"Evento: {ev}")
                if ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.estado = EstadoDoJogo.JOGANDO
                    self.atualizar_rpc(
                        estado=f"Explorando o castelo",
                        detalhes=f"Andar {self.andar.numero_andar}",
                        imagem="logo"
                    )
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    escolha = self.pause.checar_clique_pause(mouse_pos)

                    if escolha == "sair":
                        self.estado = EstadoDoJogo.MENU
                        self.atualizar_rpc(
                            estado=f"No menu",
                            detalhes=f"Aguardando para iniciar",
                            imagem="logo"
                        )
                        self.pausado = False
                    elif escolha == "continuar":
                        self.estado = EstadoDoJogo.JOGANDO
                        self.atualizar_rpc(
                            estado=f"Explorando o castelo",
                            detalhes=f"Andar {self.andar.numero_andar}",
                            imagem="logo"
                        )
                        self.pausado = False
                    elif escolha == "opcoes":
                        self.config.modo_pause  = True
                        self.config_origem = EstadoDoJogo.PAUSADO
                        self.estado = EstadoDoJogo.CONFIG

        elif self.estado == EstadoDoJogo.INVENTARIO:
            for ev in eventos:
                if ev.type == KEYDOWN and ev.key == K_i:
                    self.inventario.toggle()
                    self.estado = EstadoDoJogo.JOGANDO
                    self.atualizar_rpc(
                        estado=f"Explorando o castelo",
                        detalhes=f"Andar {self.andar.numero_andar}",
                        imagem="logo"
                    )
            self.inventario.checar_clique_armas(eventos, mouse_pos)
            self.inventario.checar_clique_navegacao(eventos, mouse_pos)
            self.inventario.checar_clique_inventario(eventos, mouse_pos)

        elif self.estado == EstadoDoJogo.GAME_OVER:
            for ev in eventos:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    escolha = self.game_over.checar_clique_pause(mouse_pos)
                    if escolha == "nova run":
                        self.apagar_saves()
                        self.resetar_jogo(com_nova_run=True)
                        self.estado = EstadoDoJogo.ESCOLHA_ARMA
                        self.atualizar_rpc(
                            estado=f"Escolhendo classe",
                            detalhes=f"Estudando os arquétipos",
                            imagem="logo"
                        )
                    elif escolha == "reiniciar":
                        self.reiniciar_run_salva()
                        self.estado = EstadoDoJogo.JOGANDO
                        self.atualizar_rpc(
                            estado=f"Explorando o castelo",
                            detalhes=f"Andar {self.andar.numero_andar}",
                            imagem="logo"
                        )
                    elif escolha == "sair":
                        self.estado = EstadoDoJogo.MENU
                        self.atualizar_rpc(
                            estado=f"No menu",
                            detalhes=f"Aguardando para iniciar",
                            imagem="logo"
                        )


        elif self.estado == EstadoDoJogo.ESCOLHA_ARMA:
            for ev in eventos:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    resultado = self.menu_armas.checar_clique_menu(mouse_pos)
                    if resultado:
                        if resultado == "sair":
                            self.estado = EstadoDoJogo.MENU
                            self.atualizar_rpc(
                                estado=f"No menu",
                                detalhes=f"Aguardando para iniciar",
                                imagem="logo"
                            )
                            return 
                        arma, atributos, trait, dificuldade = resultado
                        self.player.arma = arma
                        self.player.atributos = atributos
                        self.player.atualizar_arma()
                        self.player.atualizar_atributos()
                        self.player.atualizar_traits(trait)
                        dificuldade_global.set_dificuldade(dificuldade.lower())
                        self.dados_run_salvos = {
                            "arma_data": arma.get_save_data(),
                            "arma_tipo": arma.__class__.__name__,
                            "modificador": arma.modificador.nome,
                            'modificador_detalhes': {
                                'nome': arma.modificador.nome,
                                'valor': arma.modificador.valor
                            },
                            "dificuldade": dificuldade,
                            "trait": trait
                        }

                        self.hud.atualizar_arma_icon()
                        som.tocar("clique3")
                        self.estado = EstadoDoJogo.JOGANDO
                        self.atualizar_rpc(
                            estado=f"Explorando o castelo",
                            detalhes=f"Andar {self.andar.numero_andar}",
                            imagem="logo"
                        )
                        self.foi_pra_jogo = time.get_ticks()

        elif self.estado == EstadoDoJogo.CONFIG:
            for ev in eventos:
                if ev.type == MOUSEBUTTONDOWN and ev.button == 1:
                    resultado = self.config.tratar_clique(mouse_pos)
                    if resultado == "voltar":
                        self.config.modo_pause = False
                        self.estado = self.config_origem
                elif ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.config.modo_pause = False
                    self.estado = self.config_origem

        elif self.estado == EstadoDoJogo.CONTROLES or self.estado == EstadoDoJogo.CREDITOS or self.estado == EstadoDoJogo.VITORIA:
            for ev in eventos:
                if ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.estado = EstadoDoJogo.MENU
                    self.atualizar_rpc(
                        estado=f"No menu",
                        detalhes=f"Aguardando para iniciar",
                        imagem="logo"
                    )

        for ev in eventos:
            if ev.type == MOUSEBUTTONDOWN:
                self.cursor_clicando = True
            elif ev.type == MOUSEBUTTONUP:
                self.cursor_clicando = False

    def atualizar(self, dt, keys, eventos, mouse_pos):
        if self.sala_atual:
            if self.sala_atual.game_vitoria:
                self.estado = EstadoDoJogo.VITORIA
                self.atualizar_rpc(
                    estado=f"No menu",
                    detalhes=f"Aguardando para iniciar",
                    imagem="logo"
                )
                self.sala_atual.game_vitoria = False
        if self.sala_atual:
            if self.sala_atual.cutscene and self.sala_atual.cutscene.ativa:
                self.estado = EstadoDoJogo.CUTSCENE
        if self.estado == EstadoDoJogo.CUTSCENE:
            self.sala_atual.cutscene.update(eventos)
            if not self.sala_atual.cutscene.ativa:
                self.estado = EstadoDoJogo.JOGANDO
                self.atualizar_rpc(
                    estado=f"Explorando o castelo",
                    detalhes=f"Andar {self.andar.numero_andar}",
                    imagem="logo"
                )
            return
        if self.estado == EstadoDoJogo.JOGANDO:
            self.sala_atual.atualizar(dt, keys, eventos, mouse_pos)
            self.player.atualizar(dt, keys, mouse_pos)
            self.torch_manager.update()
            mouse_buttons = mouse.get_pressed()

            if time.get_ticks() - self.foi_pra_jogo > self.cd_arma_jogo:
                if mouse_buttons[0]:
                    self.player.ataque_espadaPrincipal(self.sala_atual.inimigos, mouse_pos, dt)

            if (
                    self.estado == EstadoDoJogo.JOGANDO and
                    self.sala_atual.bau and
                    self.sala_atual.ativar_menu_bau and
                    not self.bau_foi_aberto_esse_frame
            ):
                if self.sala_atual.bau.menu_ativo:
                    self.estado = EstadoDoJogo.BAU
                    self.player.travado = True
                    self.bau_foi_aberto_esse_frame = True

            if self.player.gameOver:
                self.apagar_saves()
                self.estado = EstadoDoJogo.GAME_OVER
                self.atualizar_rpc(
                    estado=f"No menu",
                    detalhes=f"Aguardando para iniciar",
                    imagem="logo"
                )

    def desenhar(self, mouse_pos):
        # self.screen.fill((0, 0, 0))
        self.render_surface.fill((0,0,0))
        offset_x, offset_y = screen_shaker.offset

        if self.estado == EstadoDoJogo.MENU or (self.estado == EstadoDoJogo.CONFIG and self.config_origem == EstadoDoJogo.MENU):
            self.menu.run()
            self.menu.desenho(self.screen, mouse_pos, self)

        elif self.estado == EstadoDoJogo.CONFIG and self.config_origem == EstadoDoJogo.PAUSADO:
            if self.imagem_fundo_pause:
                self.screen.blit(self.imagem_fundo_pause, (0, 0))
            overlay = Surface((1920, 1080), SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

        elif self.estado == EstadoDoJogo.ESCOLHA_ARMA:
            self.menu_armas.menu_ativo = True
            self.menu_armas.desenhar_menu(self.screen, mouse_pos)

        elif self.estado == EstadoDoJogo.JOGANDO:
            self.hud.desenhaFundo()
            self.sala_atual.desenhar(self.screen, mouse_pos)
        
            # desenha tochas (sprite)
            self.torch_manager.draw(self.screen, screen_shaker.offset)

            # partículas da tocha (antes da luz)
            self.torch_manager.draw_particles(self.screen, screen_shaker.offset)

            # luz do player
            self.aplicar_luz()

            # luz das tochas
            self.torch_manager.aplicar_luzes(self.darkness, screen_shaker.offset)

            for inimigo in self.sala_atual.inimigos:
                if hasattr(inimigo, "projeteis"):
                    for projetil in inimigo.projeteis:
                        if "luz" in projetil:
                            projetil["luz"].apply(
                                self.darkness,
                                projetil["x"],
                                projetil["y"],
                                screen_shaker.offset
                            )

            # escuridão final
            self.screen.blit(self.darkness, (0, 0))

            self.sala_atual.desenhar_inimigos(self.screen, mouse_pos)
            self.player.desenhar(self.screen, mouse_pos)
            self.hud.desenhar()
            self.hud.update(self.clock.get_time())
            self.minimapa.draw()
            self.inventario.desenhar(mouse_pos)

        elif self.estado == EstadoDoJogo.LOJA:
            self.sala_atual.desenhar(self.screen, mouse_pos)
            self.sala_atual.loja.desenhar_loja(self.screen, mouse_pos)

        elif self.estado == EstadoDoJogo.BAU:
            self.sala_atual.desenhar(self.screen, mouse_pos)
            self.sala_atual.bau.bauEscolherItens(self.screen, mouse_pos)

        elif self.estado == EstadoDoJogo.INVENTARIO:
            self.hud.desenhaFundo()
            self.sala_atual.desenhar(self.screen, mouse_pos)
            self.player.desenhar(self.screen, mouse_pos)
            self.sala_atual.desenhar_inimigos(self.screen, mouse_pos)
            self.hud.desenhar(minimal=True)
            self.hud.update(self.clock.get_time())
            self.minimapa.draw()
            self.inventario.desenhar(mouse_pos)


        elif self.estado == EstadoDoJogo.PAUSADO:
            try:
                self.clock.tick(60)  # Garante que o loop anda mesmo travado
                print("PAUSE FRAME OK")  # Ver se trava nesse print
                self.pause.pauseFuncionamento(self.screen, mouse_pos,self.imagem_fundo_pause)
            except Exception as e:
                print(f"[GAME DRAW PAUSE CRASH] {type(e).__name__}: {e}")

        elif self.estado == EstadoDoJogo.GAME_OVER:
            self.game_over.gameOverFuncionamento(self.screen, mouse_pos)

        elif self.estado == EstadoDoJogo.CUTSCENE:
            self.sala_atual.cutscene.draw(self.screen)

        #if time.get_ticks() % 500 < 16:
        #    fps = int(self.clock.get_fps())
        #    self.fps_text = self.fps_font.render(f"FPS: {fps}", True, (255, 255, 255))
        #self.screen.blit(self.fps_text, (10 + offset_x, 10 + offset_y))

        elif self.estado == EstadoDoJogo.CONTROLES:
            self.screen.blit(self.imagem_controles, (0, 0))

        elif self.estado == EstadoDoJogo.VITORIA:
            self.screen.blit(self.imagem_vitoria, (0, 0))

        elif self.estado == EstadoDoJogo.CREDITOS:
            self.screen.blit(self.imagem_creditos, (0, 0))

        if self.estado == EstadoDoJogo.CONFIG:
            self.config.desenhar(self.screen, mouse_pos)

        if self.mensagem_salvo and time.get_ticks() - self.tempo_mensagem_salvo < 2000:
            self.screen.blit(self.mensagem_salvo, (1920 // 2 - self.mensagem_salvo.get_width() // 2, 900))

    def apagar_saves(self):
        try:
            save_path = resource_path("save_file.json")
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception as e:
            print(f"Erro ao apagar save: {e}")

        data_dir = resource_path("data")
        if os.path.exists(data_dir):
            for item in os.listdir(data_dir):
                try:
                    os.remove(os.path.join(data_dir, item))
                except Exception as e:
                    print(f"Erro ao apagar arquivo em data/: {e}")

    def tela_intro(self):
        tela = self.render_surface
        logo = image.load(resource_path('assets/tela_intro.png')).convert()
        logo = transform.scale(logo, (1920, 1080))

        fade_surface = Surface((1920, 1080))
        fade_surface.fill((0, 0, 0))

        # Fade in
        for alpha in range(255, -1, -5):
            tela.blit(logo, (0, 0))
            fade_surface.set_alpha(alpha)
            tela.blit(fade_surface, (0, 0))
            scaled = transform.scale(
                self.render_surface,
                (self.largura, self.altura)
            )

            self.window.blit(scaled, (0,0))
            display.update()
            time.delay(30)

        # Espera com a imagem por 1.5 segundos
        tela.blit(logo, (0, 0))
        scaled = transform.scale(
            self.render_surface,
            (self.largura, self.altura)
        )

        self.window.blit(scaled, (0,0))
        display.update()
        time.delay(500)

        # Fade out
        for alpha in range(0, 256, 5):
            tela.blit(logo, (0, 0))
            fade_surface.set_alpha(alpha)
            tela.blit(fade_surface, (0, 0))
            scaled = transform.scale(
                self.render_surface,
                (self.largura, self.altura)
            )

            self.window.blit(scaled, (0,0))
            display.update()
            time.delay(30)

    def atualizar_rpc(self, estado, detalhes, imagem="logo"):
        novo_estado = (estado, detalhes, imagem)
        if self.rpc_estado_atual != novo_estado:
            self.discord.atualizar(estado, detalhes, imagem)
            self.rpc_estado_atual = novo_estado