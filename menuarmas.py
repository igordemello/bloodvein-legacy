from pygame import *
from pygame.math import Vector2
from efeito import *
from hud import Hud
from itensDic import ConjuntoItens
from random import sample
from botao import Botao
from armas import *
from player import Player
from utils import resource_path 

class MenuArmas:
    def __init__(self, hud):
        self.lista_mods = ListaMods()
        self.hud = hud

        self.estado_hover = Vector2(1.0, 0.0)

        self.atributosFundo = image.load(resource_path('assets/ui/atributo_fundo.png')).convert_alpha()

        self.todas_armas = [
            LaminaDaNoite("comum", self.lista_mods),
            Chigatana("comum", self.lista_mods),
            Karambit("comum", self.lista_mods),
            EspadaDoTita("comum", self.lista_mods),
            MachadoDoInverno("comum", self.lista_mods),
            EspadaEstelar("comum", self.lista_mods),
            MarteloSolar("comum", self.lista_mods),
            Arco("comum", self.lista_mods)
        ]

        for arma in self.todas_armas:
            arma.aplicaModificador()

        self.traits_armas = {
            "Vampira": LaminaDaNoite("comum", self.lista_mods),
            "Ancião": MachadoDoInverno("comum", self.lista_mods),
            "Peçonhento": Karambit("comum", self.lista_mods),
            "Mercúrio": Arco("comum", self.lista_mods),
            "Humano": LaminaDaNoite("comum", self.lista_mods)  # Começa com Lâmina da Noite
        }

        self.traits = list(self.traits_armas.keys())
        self.trait_selecionada = 0
        self.arma_atual = self.traits_armas[self.traits[self.trait_selecionada]]
        self.arma_index_humano = 0
        self.menu_ativo = False

        self.dificuldades = [
            "Fácil",
            "Normal",
            "Criança da Noite",
            "Lua de Sangue"
        ]
        self.dificuldade_selecionada = 1

        screen = display.get_surface()
        self.botao_iniciar = Botao(
            image=None,
            pos=(1500, 150),
            text_input="INICIAR",
            font=font.Font(resource_path('assets/Fontes/alagard.ttf'), 96),
            base_color=(255, 255, 255),
            hovering_color=(200, 200, 200)
        )

    def get_atributos_por_trait(self):
        traits_atributos = {
            "Vampira": {"forca": 5, "destreza": 5, "agilidade": 5, "vigor": 5, "resistencia": 5, "estamina": 5,
                        "sorte": 5},
            "Ancião": {"forca": 3, "destreza": 6, "agilidade": 7, "vigor": 4, "resistencia": 4, "estamina": 6,
                            "sorte": 5},
            "Peçonhento": {"forca": 4, "destreza": 6, "agilidade": 5, "vigor": 6, "resistencia": 3, "estamina": 6,
                           "sorte": 4},
            "Mercúrio": {"forca": 4, "destreza": 7, "agilidade": 7, "vigor": 2, "resistencia": 4, "estamina": 6,
                         "sorte": 2},
            "Humano": {"forca": 3, "destreza": 3, "agilidade": 4, "vigor": 3, "resistencia": 3, "estamina": 3,
                       "sorte": 8}
        }
        return traits_atributos[self.traits[self.trait_selecionada]]

    def desenhar_menu(self, tela):
        tela.blit(self.atributosFundo, (0, 0))

        atributos_bg = Surface((int(tela.get_width() * 0.5), int(tela.get_height() * 0.75)), SRCALPHA)
        atributos_bg.fill((0, 0, 0, 150))
        tela.blit(atributos_bg, atributos_bg.get_rect(center=(665, tela.get_height() // 2 + 100)))

        y_pos = 300
        font_atributos = font.Font(resource_path('assets/Fontes/alagard.ttf'), 48)
        atributos = self.get_atributos_por_trait()

        for nome, valor in atributos.items():
            nome_texto = font_atributos.render(f"{nome.capitalize()}:", True, (255, 255, 255))
            valor_texto = font_atributos.render(str(valor), True, (255, 255, 255))
            tela.blit(nome_texto, (635 - 300, y_pos))
            tela.blit(valor_texto, (635 + 215, y_pos))
            y_pos += 70

        y_pos += 40
        trait_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 32)
        trait_text = trait_font.render(self.traits[self.trait_selecionada], True, (255, 255, 255))
        tela.blit(trait_text, trait_text.get_rect(center=(635, y_pos)))

        seta_esq = image.load(resource_path('assets/UI/seta_esquerda.png')).convert_alpha()
        seta_dir = image.load(resource_path('assets/UI/seta_direita.png')).convert_alpha()

        seta_esq_rect = seta_esq.get_rect(center=(635 - 200, y_pos))
        seta_dir_rect = seta_dir.get_rect(center=(635 + 200, y_pos))

        tela.blit(seta_esq, seta_esq_rect)
        tela.blit(seta_dir, seta_dir_rect)

        y_pos += 70
        dificuldade_titulo = font.Font(resource_path('assets/Fontes/alagard.ttf'), 48).render("DIFICULDADE", True, (255, 255, 255))
        tela.blit(dificuldade_titulo, (635 - dificuldade_titulo.get_width() // 2, y_pos))

        y_pos += 90
        dificuldade_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 32)
        dificuldade_text = dificuldade_font.render(self.dificuldades[self.dificuldade_selecionada], True,
                                                   (255, 255, 255))
        tela.blit(dificuldade_text, dificuldade_text.get_rect(center=(635, y_pos)))

        seta_esq_dif_rect = seta_esq.get_rect(center=(635 - 200, y_pos))
        seta_dir_dif_rect = seta_dir.get_rect(center=(635 + 200, y_pos))
        tela.blit(seta_esq, seta_esq_dif_rect)
        tela.blit(seta_dir, seta_dir_dif_rect)

        self.desenhar_carta_arma(tela)

        if self.traits[self.trait_selecionada] == "Humano":
            seta_esq_arma = image.load(resource_path('assets/UI/seta_esquerda.png')).convert_alpha()
            seta_dir_arma = image.load(resource_path('assets/UI/seta_direita.png')).convert_alpha()
 
            seta_esq_arma_rect = seta_esq_arma.get_rect(center=(1490 - 250, 580))
            seta_dir_arma_rect = seta_dir_arma.get_rect(center=(1490 + 250, 580))

            tela.blit(seta_esq_arma, seta_esq_arma_rect)
            tela.blit(seta_dir_arma, seta_dir_arma_rect)

        self.botao_iniciar.changeColor(mouse.get_pos())
        self.botao_iniciar.update(tela)

        self.pause_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 60)
        self.botaovoltar = Botao(image=None, pos=(100,50), text_input="Voltar", font=self.pause_font, base_color=(255, 255, 255), hovering_color=(200, 200, 200))
        self.botaovoltar.changeColor(mouse.get_pos())
        self.botaovoltar.update(tela)

        return {
            "seta_esquerda": seta_esq_rect,
            "seta_direita": seta_dir_rect,
            "dificuldade_esquerda": seta_esq_dif_rect,
            "dificuldade_direita": seta_dir_dif_rect,
            "seta_arma_esquerda": seta_esq_arma_rect if self.traits[self.trait_selecionada] == "Humano" else None,
            "seta_arma_direita": seta_dir_arma_rect if self.traits[self.trait_selecionada] == "Humano" else None
        }

    def desenhar_carta_arma(self, tela):
        carta_width, carta_height = 375, 500
        scale = 1.0
        mouse_pos = mouse.get_pos()

        if self.traits[self.trait_selecionada] == "Humano":
            self.arma_atual = self.todas_armas[self.arma_index_humano]
        else:
            self.arma_atual = self.traits_armas[self.traits[self.trait_selecionada]]

        carta_rect = Rect(0, 0, carta_width * scale, carta_height * scale)
        carta_rect.center = (1500, 580)

        is_hovered = carta_rect.collidepoint(mouse_pos)
        alvo = Vector2(1.1, -30) if is_hovered else Vector2(1.0, 0)
        self.estado_hover = self.estado_hover.lerp(alvo, 0.1)

        scale = self.estado_hover.x * scale
        deslocamento_y = self.estado_hover.y

        if is_hovered:
            if not self.hud.stats_alpha:
                self.hud.reset_stats_fade()
            self.hud.mostraStatsArma(self.arma_atual)

        width = int(carta_width * scale)
        height = int(carta_height * scale)
        pos_x = 1500 - width // 2
        pos_y = 570 - height // 2 + deslocamento_y

        if hasattr(self.arma_atual, "carta"):
            carta_img = image.load(self.arma_atual.carta).convert_alpha()
            sprite_carta = transform.scale(carta_img, (width, height))
            tela.blit(sprite_carta, (pos_x, pos_y))

    def checar_clique_menu(self, mouse_pos):
        botoes = self.desenhar_menu(display.get_surface())

        if botoes["seta_esquerda"].collidepoint(mouse_pos):
            self.trait_selecionada = (self.trait_selecionada - 1) % len(self.traits)
            return None

        if botoes["seta_direita"].collidepoint(mouse_pos):
            self.trait_selecionada = (self.trait_selecionada + 1) % len(self.traits)
            return None
        
        if self.botaovoltar.checkForInput(mouse_pos):
            return "sair"

        if botoes["dificuldade_esquerda"].collidepoint(mouse_pos):
            self.dificuldade_selecionada = (self.dificuldade_selecionada - 1) % len(self.dificuldades)
            return None

        if botoes["dificuldade_direita"].collidepoint(mouse_pos):
            self.dificuldade_selecionada = (self.dificuldade_selecionada + 1) % len(self.dificuldades)
            return None

        if self.traits[self.trait_selecionada] == "Humano":
            if botoes["seta_arma_esquerda"].collidepoint(mouse_pos):
                self.arma_index_humano = (self.arma_index_humano - 1) % len(self.todas_armas)
                return None

            if botoes["seta_arma_direita"].collidepoint(mouse_pos):
                self.arma_index_humano = (self.arma_index_humano + 1) % len(self.todas_armas)
                return None

        if self.botao_iniciar.checkForInput(mouse_pos):
            self.menu_ativo = False
            return (
                self.arma_atual,
                self.get_atributos_por_trait(),
                self.traits[self.trait_selecionada],
                self.dificuldades[self.dificuldade_selecionada]
            )

        return None