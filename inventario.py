from pygame import *
import sys
from pygame.locals import QUIT
import math
from bau import Bau
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
import shutil
from habilidades import GerenciadorHabilidades
from utils import resource_path 
class Inventario():
    def __init__(self, screen, player, hud):
        self.botoes_atributos = []
        self.botoes_habilidades = []
        self.screen = screen
        self.visible = False
        self.player = player
        self.hud = hud
        self.armasFundo = image.load(resource_path('assets/UI/armas_inventario.png')).convert_alpha()
        self.itensFundo = image.load(resource_path('assets/UI/itens_inventario.png')).convert_alpha()
        self.atributosFundo = image.load(resource_path('assets/UI/status_inventario.png')).convert_alpha()

        self.aba_atual = 0
        self.botoes_navegacao = []
        self.fonte_botoes = font.Font(resource_path('assets/fontes/alagard.ttf'), 24)

        self.gerenciador_habilidades = GerenciadorHabilidades()

        self.item_width, self.item_height = 230, 240

        self.carta_imgs = {
            "comum": transform.scale(image.load(resource_path('assets/itens/carta_comum.png')).convert_alpha(),
                                     (self.item_width + 40, self.item_height + 130)),
            "rara": transform.scale(image.load(resource_path('assets/itens/carta_rara.png')).convert_alpha(),
                                    (self.item_width + 40, self.item_height + 130)),
            "lendaria": transform.scale(image.load(resource_path('assets/itens/carta_lendaria.png')).convert_alpha(),
                                        (self.item_width + 40, self.item_height + 130)),
            "ativo": transform.scale(image.load(resource_path('assets/itens/carta_ativo.png')).convert_alpha(),
                                     (self.item_width + 40, self.item_height + 130))
        }

        self.fator_escala_arma = (self.item_width + 40) / 53

        #nao me responsabilizo por isso
        self.item_hover_atual = None
        self.tempo_hover = 0
        self.alpha_hover = 0

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.aba_atual = 0

    def desenhar_botoes_navegacao(self, mouse_pos):
        self.botoes_navegacao = []
        largura_botao = 150
        altura_botao = 45
        pos_y = 70



        if self.aba_atual == 0:
            botao_esquerda = Botao(None, (690 + largura_botao // 2, pos_y + altura_botao // 2),
                                   "Itens", self.fonte_botoes, (255, 255, 255), (0, 0, 0), 1)
            botao_direita = Botao(None, (1082 + largura_botao // 2, pos_y + altura_botao // 2),
                                  "Status", self.fonte_botoes, (255, 255, 255), (0, 0, 0), -1)
        elif self.aba_atual == 1:
            botao_esquerda = Botao(None, (690 + largura_botao // 2, pos_y + altura_botao // 2),
                                   "Armas", self.fonte_botoes, (255, 255, 255), (0, 0, 0), 0)
            botao_direita = Botao(None, (1082 + largura_botao // 2, pos_y + altura_botao // 2),
                                  "Status", self.fonte_botoes, (255, 255, 255), (0, 0, 0), -1)
        else:
            botao_esquerda = Botao(None, (690 + largura_botao // 2, pos_y + altura_botao // 2),
                                   "Armas", self.fonte_botoes, (255, 255, 255), (0, 0, 0), 0)
            botao_direita = Botao(None, (1082 + largura_botao // 2, pos_y + altura_botao // 2),
                                  "Itens", self.fonte_botoes, (255, 255, 255), (0, 0, 0), 1)

        botao_esquerda.changeColor(mouse_pos)
        botao_direita.changeColor(mouse_pos)

        botao_esquerda.update(self.screen)
        botao_direita.update(self.screen)
        self.botoes_navegacao = [botao_esquerda, botao_direita]

    def desenhar(self, mouse_pos):
        if not self.visible:
            return



        if self.aba_atual == 0:
            self.desenharArma(mouse_pos)
        elif self.aba_atual == 1:
            self.desenharItem(mouse_pos)
        else:
            self.desenharStats(mouse_pos)
        self.desenhar_botoes_navegacao(mouse_pos)

    def desenharItem(self, mouse_pos):
        self.screen.blit(self.itensFundo, (0, 0))
        item_hover = None
        item_hover_pos = (0, 0)
        mouse_x, mouse_y = mouse_pos

        # itens passivos
        for i, (item, qtd) in enumerate(self.player.itens.items()):
            x = 385 + (i % 7) * 107
            y = 560 + (i // 7) * 107
            sprite = transform.scale(item.sprite, (100, 100))
            self.screen.blit(sprite, (x, y))

            rect_item = Rect(x, y, 100, 100)
            if rect_item.collidepoint(mouse_x, mouse_y):
                item_hover = item
                item_hover_pos = (x, y)

        # item ativo
        if self.player.itemAtivo is not None:
            item_ativo = self.player.itemAtivo
            ativo_x, ativo_y = 670, 250
            sprite = transform.scale(item_ativo.sprite, (200, 200))
            self.screen.blit(sprite, (ativo_x, ativo_y))

            rect_ativo = Rect(ativo_x, ativo_y, 200, 200)
            if rect_ativo.collidepoint(mouse_x, mouse_y):
                item_hover = item_ativo
                item_hover_pos = (ativo_x, ativo_y)

        # carta de item
         #nao me responsabilizo por isso
        if item_hover:
            # Controle de tempo e fade
            if item_hover == self.item_hover_atual:
                self.tempo_hover += 1
                if self.alpha_hover < 255:
                    self.alpha_hover += 15  # velocidade do fade-in
            else:
                self.item_hover_atual = item_hover
                self.tempo_hover = 0
                self.alpha_hover = 0

            # Impede que vá além
            self.alpha_hover = min(self.alpha_hover, 255)

            # Preparar imagem com alpha
            carta_img = self.carta_imgs.get(item_hover.raridade, self.carta_imgs["comum"]).copy()
            escala = 1.2
            largura = int(carta_img.get_width() * escala)
            altura = int(carta_img.get_height() * escala)
            carta_img = transform.scale(carta_img, (largura, altura))
            carta_img.set_alpha(self.alpha_hover)

            carta_x = 1240 - (largura * (escala - 1)) // 2
            carta_y = 390 - (altura * (escala - 1)) // 2
            self.screen.blit(carta_img, (carta_x, carta_y))

            # Só desenha o conteúdo textual e o ícone se alpha for suficientemente alto
            if self.alpha_hover > 10:
                fonte_nome = font.Font(resource_path('assets/fontes/alagard.ttf'), int(20 * escala))
                fonte_desc = font.Font(resource_path('assets/fontes/alagard.ttf'), int(16 * escala))
                icon_size = int(80 * escala)
                icon = transform.scale(item_hover.sprite, (icon_size, icon_size))
                icon_x = carta_x + (largura - icon_size) // 2
                icon_y = carta_y + int(50 * escala)
                self.screen.blit(icon, (icon_x, icon_y))

                if isinstance(item_hover, ItemAtivo):
                    for x in range(item_hover.usos):
                        draw.rect(self.screen, (0, 255, 0),
                                (icon_x + (x * int(25 * escala)) - 70,
                                icon_y + icon_size + int(10 * escala) + 220,
                                int(20 * escala), int(8 * escala)))

                texto_nome = fonte_nome.render(item_hover.nome, True, (0, 0, 0))
                nome_x = carta_x + (largura - texto_nome.get_width()) // 2
                nome_y = icon_y + icon_size + int(35 * escala)
                self.screen.blit(texto_nome, (nome_x, nome_y))

                descricao = item_hover.descricao
                palavras = descricao.split(" ")
                linhas = []
                linha_atual = ""

                for palavra in palavras:
                    test_line = linha_atual + " " + palavra if linha_atual else palavra
                    if fonte_desc.size(test_line)[0] < 230 * escala:
                        linha_atual = test_line
                    else:
                        linhas.append(linha_atual)
                        linha_atual = palavra
                if linha_atual:
                    linhas.append(linha_atual)

                for i, linha in enumerate(linhas):
                    texto_desc = fonte_desc.render(linha, True, (0, 0, 0))
                    desc_x = carta_x + (largura - texto_desc.get_width()) // 2
                    desc_y = nome_y + int(55 * escala) + i * int(24 * escala)
                    self.screen.blit(texto_desc, (desc_x, desc_y))

    def desenharStats(self, mouse_pos):
        self.screen.blit(self.atributosFundo, (0, 0))
        # --- ATRIBUTOS DO PLAYER ---
        if self.player:
            player = self.player
            fonte_attr = font.Font(resource_path('assets/fontes/alagard.ttf'), 48)
            fonte_custo = font.Font(resource_path('assets/fontes/alagard.ttf'), 32)
            fonte_desc = font.Font(resource_path('assets/fontes/alagard.ttf'), 20)
            fonte_hotkey = font.Font(resource_path('assets/fontes/alagard.ttf'),
                                     24)
            cor_attr = (253, 246, 225)
            cor_desc = (200, 200, 200)

            desc_largura = 300
            desc_altura = 80
            desc_margem = 20

            atributos = [
                f'Força: {round(player.atributos["forca"], 1)}',
                f'Destreza: {round(player.atributos["destreza"], 1)}',
                f'Agilidade: {int(player.atributos["agilidade"])}',
                f'Vigor: {round(player.atributos["vigor"], 1)}',
                f'Resistência: {round(player.atributos["resistencia"], 1)}',
                f'Estamina: {round(player.atributos["estamina"], 1)}',
                f'Sorte: {round(player.atributos["sorte"], 1)}'
            ]

            base_x = 460
            base_y = 300

            nivelCusto = fonte_custo.render(f'{str((10 + (player.nivel * 2)))} almas', True, cor_attr)
            self.screen.blit(nivelCusto, (700, 810))

            nivel = fonte_attr.render(str(player.nivel), True, cor_attr)
            self.screen.blit(nivel, (700, 188))

            almas = fonte_custo.render(f'{str(player.almas)}', True, cor_attr)
            self.screen.blit(almas, (680, 748))

            pontosHabilidade = fonte_custo.render(f'{str(player.pontosHabilidade)}', True, cor_attr)
            self.screen.blit(pontosHabilidade, (790, 873))

            for i, linha in enumerate(atributos):
                texto = fonte_attr.render(linha, True, cor_attr)
                self.screen.blit(texto, (base_x, base_y + i * 60))

            if player.almas >= (10 + (player.nivel * 2)):
                y_pos = 300
                self.botoes_atributos = []

                atributos_ordenados = [
                    "forca",
                    "destreza",
                    "agilidade",
                    "vigor",
                    "resistencia",
                    "estamina",
                    "sorte"
                ]

                for i, atributo in enumerate(atributos_ordenados):
                    if player.atributos[atributo] < 10:
                        botao_mais_rect = Rect(800, y_pos, 32, 32)
                        draw.rect(self.screen,
                                  (0, 200, 0) if botao_mais_rect.collidepoint(mouse_pos) else (0, 150, 0),
                                  botao_mais_rect)
                        mais_texto = fonte_attr.render("+", True, (255, 255, 255))
                        self.screen.blit(mais_texto, (801, y_pos - 5))
                        self.botoes_atributos.append(
                            (atributo, botao_mais_rect))

                    y_pos += 60

            habilidades = list(self.gerenciador_habilidades.habilidades.keys())
            posicoes_botoes = [
                (1094, 820), (1373, 820),
                (998, 660), (1190, 660),
                (998, 500), (1190, 500), (1373, 500),
                (1094, 340), (1277, 340), (1469, 340)
            ]

            fonte_habilidade = font.Font(resource_path('assets/fontes/alagard.ttf'), 16)
            self.botoes_habilidades = []
            

            linhas = (
                "Aperte 1, 2, 3 ou 4 com o cursor em cima de uma\n"
                "habilidade para vinculá-la a essa tecla"
            ).split("\n")

            surfaces = [fonte_habilidade.render(l, True, (243, 236, 215)) for l in linhas]

            largura_max = max(s.get_width() for s in surfaces)

            x = 800   # posição inicial do parágrafo
            y = 1020

            for surface in surfaces:
                offset_x = (largura_max - surface.get_width()) // 2
                self.screen.blit(surface, (x + offset_x, y))
                y += surface.get_height()

            hovered_habilidade = None

            cadeado_img = None
            try:
                cadeado_img = image.load(resource_path('assets/habilidades/cadeado.png')).convert_alpha()
                cadeado_img = transform.scale(cadeado_img, (100, 100))  # Tamanho ajustável
            except Exception as e:
                print(f"Erro ao carregar imagem do cadeado: {e}")

            for i, (pos_x, pos_y) in enumerate(posicoes_botoes):
                if i >= len(habilidades):
                    break

                hab_nome = habilidades[i]
                hab = self.gerenciador_habilidades.habilidades[hab_nome]

                pode_comprar = self.gerenciador_habilidades.pode_desbloquear(self.player, hab_nome)
                ja_comprada = hab_nome in player.habilidades
                cor = self.gerenciador_habilidades.get_cor_botao(player, hab_nome)

                botao_image = None

                if hasattr(hab, 'sprite_path'):
                    try:
                        botao_image = image.load(resource_path(hab.sprite_path)).convert_alpha()
                        botao_image = transform.scale(botao_image, (104, 104))

                        overlay = Surface((104, 104), SRCALPHA)

                        if ja_comprada:
                            overlay.fill((0, 0, 0, 100))
                        elif not pode_comprar:
                            overlay.fill((150, 0, 0, 100))
                            if cadeado_img:
                                cadeado_x = (104 - cadeado_img.get_width()) // 2
                                cadeado_y = (104 - cadeado_img.get_height()) // 2
                                overlay.blit(cadeado_img, (cadeado_x, cadeado_y))

                        botao_image.blit(overlay, (0, 0))
                    except Exception as e:
                        print(f"Error loading skill image {hab.sprite_path}: {e}")
                        botao_surface = Surface((104, 104), SRCALPHA)
                        if not pode_comprar:
                            botao_surface.fill((255, 0, 0, 150))
                            if cadeado_img:
                                cadeado_x = (104 - cadeado_img.get_width()) // 2
                                cadeado_y = (104 - cadeado_img.get_height()) // 2
                                botao_surface.blit(cadeado_img, (cadeado_x, cadeado_y))
                        else:
                            botao_surface.fill(cor)
                else:
                    botao_surface = Surface((104, 104), SRCALPHA)
                    if not pode_comprar:
                        botao_surface.fill((255, 0, 0, 150))
                        if cadeado_img:
                            cadeado_x = (104 - cadeado_img.get_width()) // 2
                            cadeado_y = (104 - cadeado_img.get_height()) // 2
                            botao_surface.blit(cadeado_img, (cadeado_x, cadeado_y))
                    else:
                        botao_surface.fill(cor)

                hotkey_num = None
                for num, habilidade in enumerate(player.hotkeys, 1):
                    if habilidade == hab_nome:
                        hotkey_num = num
                        break

                botao = Botao(
                    image=botao_image if botao_image is not None else botao_surface,
                    pos=(pos_x + 52, pos_y + 52),
                    text_input="",
                    font=fonte_habilidade,
                    base_color=(255, 255, 255),
                    hovering_color=(255, 255, 255),
                    value=hab_nome
                )

                if hotkey_num:
                    hotkey_text = fonte_hotkey.render(str(hotkey_num), True, (255, 255, 255))
                    hotkey_rect = hotkey_text.get_rect(bottomright=(pos_x + 100, pos_y + 100))
                    self.screen.blit(hotkey_text, hotkey_rect)

                if botao.checkForInput(mouse_pos):
                    hovered_habilidade = hab

                botao.changeColor(mouse_pos)
                botao.update(self.screen)
                self.botoes_habilidades.append(botao)

            if hovered_habilidade and hasattr(hovered_habilidade, 'descricao'):
                for botao in self.botoes_habilidades:
                    if botao.value == hovered_habilidade.nome:
                        desc_x = botao.rect.centerx - desc_largura // 2
                        desc_y = botao.rect.bottom + desc_margem - 20

                        desc_fundo = Surface((desc_largura, desc_altura), SRCALPHA)
                        desc_fundo.fill((0, 0, 0, 180))

                        self.screen.blit(desc_fundo, (desc_x, desc_y))

                        palavras = hovered_habilidade.descricao.split(' ')
                        linhas = []
                        linha_atual = ""

                        for palavra in palavras:
                            teste_linha = f"{linha_atual} {palavra}" if linha_atual else palavra
                            if fonte_desc.size(teste_linha)[0] < desc_largura - 20:
                                linha_atual = teste_linha
                            else:
                                linhas.append(linha_atual)
                                linha_atual = palavra
                        if linha_atual:
                            linhas.append(linha_atual)

                        for i, linha in enumerate(linhas):
                            texto_desc = fonte_desc.render(linha, True, cor_desc)
                            texto_x = desc_x + (desc_largura - texto_desc.get_width()) // 2
                            texto_y = desc_y + 10 + i * (fonte_desc.get_height() + 2)
                            self.screen.blit(texto_desc, (texto_x, texto_y))
                        break


    def desenharArma(self, mouse_pos):
        if not self.visible:
            return

        self.screen.blit(self.armasFundo, (0, 0))

        mouse_x, mouse_y = mouse_pos
        arma_hover = None
        arma_hover_pos = (0, 0)
        cores_raridade = {
            "comum": (255, 255, 255, 80),
            "incomum": (0, 255, 0, 80),
            "raro": (128, 0, 128, 80),
            "lendaria": (255, 255, 0, 80)
        }
        cores_raridade_hover = {
            "comum": (150, 150, 150, 80),
            "incomum": (0, 100, 0, 80),
            "raro": (28, 0, 28, 80),
            "lendaria": (150, 150, 0, 80)
        }
        for i, arma in enumerate(self.player.inventario):
            x = 413 + (i % 7) * 107
            y = 647 + (i // 7) * 107

            raridade = getattr(arma, "raridadeStr", "comum")
            cor_fundo = cores_raridade.get(raridade, (255, 255, 255, 80))

            rect_item = Rect(x, y, 100, 100)
            if rect_item.collidepoint(mouse_x, mouse_y):
                arma_hover = arma
                arma_hover_pos = (x, y)
                cor_fundo = cores_raridade_hover.get(raridade, (255, 255, 255, 80))

            fundo = Surface((100, 100), SRCALPHA)
            fundo.fill(cor_fundo)
            self.screen.blit(fundo, (x, y))

            spriteArma = image.load(arma.spriteIcon).convert_alpha()
            sprite = transform.scale(spriteArma, (100, 100))
            self.screen.blit(sprite, (x, y))

        if arma_hover:
            fonte_attr = font.Font(resource_path('assets/fontes/alagard.ttf'), 32)
            cor_attr = (253, 246, 225)

            atributos = [
                f"{arma_hover.tipoDeArma}",
                f"Dano: {round(arma_hover.dano, 1)}",
                f"Rapidez: {round(arma_hover.velocidade, 1)}",
                f"Roubo de Vida: {round(arma_hover.lifeSteal, 1)}",
                f"% Crítico: {round(arma_hover.chanceCritico, 1)}",
                f"Dano Crítico: {round(arma_hover.danoCriticoMod * arma_hover.dano, 1)}",
                f"Mod: {arma_hover.modificador.nome if hasattr(arma_hover, 'modificador') else 'Nenhum'}"
            ]

            base_x = 1250
            base_y = 700

            for i, linha in enumerate(atributos):
                texto = fonte_attr.render(linha, True, cor_attr)
                self.screen.blit(texto, (base_x, base_y + i * 32))

        arma = self.player.arma
        if hasattr(arma, "carta"):
            carta_img = image.load(arma.carta).convert_alpha()
            fator_escala = (self.item_width + 40) / 53
            nova_largura = int(53 * fator_escala)
            nova_altura = int(72 * fator_escala)
            carta_escalada = transform.scale(carta_img, (nova_largura, nova_altura))
            self.screen.blit(carta_escalada, (1263, 190))

        if self.player.arma:
            arma = self.player.arma
            fonte_attr = font.Font(resource_path('assets/fontes/alagard.ttf'), 32)
            fonte_nome = font.Font(resource_path('assets/fontes/alagard.ttf'), 48)
            cor_attr = (253, 246, 225)
            nome = f"{arma.nome}"
            atributos = [
                f"Dano: {round(arma.dano, 1)}",
                f"Rapidez: {round(arma.velocidade, 1)}",
                f"Roubo de Vida: {round(arma.lifeSteal, 1)}",
                f"% Crítico: {round(arma.chanceCritico, 1)}",
                f"Dano Crítico: {round(arma.danoCriticoMod * arma.dano, 1)}",
                f"Mod: {arma.modificador.nome if hasattr(arma, 'modificador') else 'Nenhum'}"
            ]

            base_x = 545 + 60 + 40
            base_y = 270
            textoNome = fonte_nome.render(nome, True, cor_attr)
            self.screen.blit(textoNome, (265 + 120 + 40, 150 + 1 * 48))

            for i, linha in enumerate(atributos):
                texto = fonte_attr.render(linha, True, cor_attr)
                self.screen.blit(texto, (base_x, base_y + i * 48))

    def checar_clique_navegacao(self, eventos, mouse_pos):
        if not self.visible:
            return

        for evento in eventos:
            if evento.type == MOUSEBUTTONDOWN and evento.button == 1:
                for botao in self.botoes_navegacao:
                    if botao.checkForInput(mouse_pos):
                        self.aba_atual = botao.value
                        return True
        return False

    def checar_clique_inventario(self, eventos, mouse_pos):
        if not self.visible or self.aba_atual != -1:
            return False


        for evento in eventos:
            if evento.type == MOUSEBUTTONDOWN and evento.button == 1:
                for atributo, rect in self.botoes_atributos:
                    if rect.collidepoint(mouse_pos):
                        custo = 10 + (self.player.nivel * 2)
                        if (self.player.almas >= custo and
                                self.player.atributos[atributo] < 10):
                            self.player.atributos[atributo] += 1
                            self.player.almas -= custo
                            self.player.atualizar_atributos()
                            self.player.nivel += 1
                            if self.player.nivel % 2 == 0:
                                self.player.pontosHabilidade += 1
                            som.tocar('upgrade_atributo')
                            return True

                for botao in self.botoes_habilidades:
                    if botao.checkForInput(mouse_pos):
                        hab_nome = botao.value
                        return self.gerenciador_habilidades.desbloquear(self.player, hab_nome)

            teclas_para_verificar = [K_1, K_2, K_3, K_4]
            for i in range(4):
                if evento.type == KEYDOWN and evento.key == teclas_para_verificar[i]:
                    for botao in self.botoes_habilidades:
                        if botao.checkForInput(mouse_pos):
                            hab_nome = botao.value
                            if hab_nome in self.player.habilidades and hab_nome not in self.gerenciador_habilidades.passivas:
                                self.player.hotkeys[i] = hab_nome



        return False

    def checar_clique_armas(self, eventos, mouse_pos):
        if not self.visible or self.aba_atual != 0:
            return

        mouse_x, mouse_y = mouse_pos

        for evento in eventos:
            if evento.type == MOUSEBUTTONDOWN and evento.button == 1:
                for i, arma in enumerate(self.player.inventario):
                    x = 413 + (i % 7) * 107
                    y = 647 + (i // 7) * 107
                    rect_item = Rect(x, y, 100, 100)

                    if rect_item.collidepoint(mouse_x, mouse_y):
                        arma_antiga = self.player.arma

                        self.player.arma = arma
                        self.player.inventario[i] = arma_antiga

                        self.player.atualizar_arma()
                        self.hud.atualizar_arma_icon()
                        break

            # Adicionado: Dropar item no chão com botão direito
            if evento.type == MOUSEBUTTONDOWN and evento.button == 3:  # Botão direito do mouse
                for i, arma in enumerate(self.player.inventario):
                    x = 413 + (i % 7) * 107
                    y = 647 + (i // 7) * 107
                    rect_item = Rect(x, y, 100, 100)

                    if rect_item.collidepoint(mouse_x, mouse_y):
                        # Remove do inventário
                        arma_removida = self.player.inventario.pop(i)

                        # Determina a raridade e cores
                        raridade = getattr(arma_removida, 'raridadeStr', 'comum').lower()

                        # Cores baseadas na raridade (usando o mesmo padrão do loot normal)
                        if raridade == "lendaria":
                            cor = (255, 255, 0)
                            hover = (255, 255, 150)
                        elif raridade == "raro":
                            cor = (128, 0, 128)
                            hover = (230, 150, 230)
                        elif raridade == "incomum":
                            cor = (0, 255, 0)
                            hover = (144, 238, 144)
                        else:  # comum
                            cor = (255, 255, 255)
                            hover = (255, 255, 255)

                        # Carrega a imagem da bola correspondente à raridade
                        try:
                            bola_img = transform.scale(
                                image.load(resource_path(f"assets/itens/bola{raridade.capitalize()}.png")),
                                (64, 64)
                            )
                        except:

                            bola_img = None

                        fontinha = font.Font(resource_path('assets/fontes/alagard.ttf'), 18)

                        drop_x = self.player.x + randint(-80, 80)
                        drop_y = self.player.y + randint(-80, 80)

                        drop_x = self.player.x + randint(-50, 50)
                        drop_y = self.player.y + randint(-50, 50) + 100

                        botao = Botao(
                            image=bola_img,
                            pos=(drop_x, drop_y),
                            text_input=arma_removida.nome,
                            font=fontinha,
                            base_color=cor,
                            hovering_color=cor,
                            value=arma_removida
                        )

                        if bola_img:
                            botao.rect = bola_img.get_rect(center=(drop_x, drop_y))
                        else:
                            texto_render = fontinha.render(arma_removida.nome, True, cor)
                            botao.image = texto_render
                            botao.rect = texto_render.get_rect(center=(drop_x, drop_y))

                        if hasattr(self.player, 'sala_atual'):
                            self.player.sala_atual.loots.append((botao, arma_removida))

                            som.tocar("ItemDrop")

                        break