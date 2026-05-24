from pygame import *
from pygame.math import Vector2
from som import musica, som
from utils import resource_path
from botao import Botao


class Pause:
    def __init__(self):
        botao_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 72)
        self.cor_base  = (253, 246, 225)
        self.cor_hover = (228, 133, 40)   # âmbar — visível no fundo escuro do pause

        CX = 1920 // 2

        self.botaocontinuar = Botao(None, (CX, 420), "Continuar", botao_font, self.cor_base, self.cor_hover, "continuar")
        self.botaoopcoes    = Botao(None, (CX, 540), "Opções",    botao_font, self.cor_base, self.cor_hover, "opcoes")
        self.botaosair      = Botao(None, (CX, 660), "Sair",      botao_font, self.cor_base, self.cor_hover, "sair")

        self.botoes = [self.botaocontinuar, self.botaoopcoes, self.botaosair]

        self.hover_escala = [Vector2(1.0, 0.0) for _ in self.botoes]
        self.ultimo_hover = -1
        self.index_selecionado = 0

        self.pause_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 100)
        self.menu_ativo = False

    def pauseFuncionamento(self, tela, mouse_pos, imagem_fundo=None):
        try:
            self.menu_ativo = True

            if imagem_fundo:
                tela.blit(imagem_fundo, (0, 0))
                overlay = Surface((1920, 1080), SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                tela.blit(overlay, (0, 0))

            # Título
            sombra = self.pause_font.render("Pausado", True, (30, 30, 30))
            titulo = self.pause_font.render("Pausado", True, (253, 246, 225))
            rect = titulo.get_rect(center=(1920 // 2, 200))
            tela.blit(sombra, (rect.x + 4, rect.y + 4))
            tela.blit(titulo, rect)

            # Botões com lerp igual ao menu
            for i, botao in enumerate(self.botoes):
                is_hovered = botao.rect.collidepoint(mouse_pos) or i == self.index_selecionado

                if is_hovered:
                    if i != self.ultimo_hover:
                        som.tocar("hover")
                        self.ultimo_hover = i
                    self.index_selecionado = i

                alvo = Vector2(1.1, -5) if is_hovered else Vector2(1.0, 0.0)
                self.hover_escala[i] = self.hover_escala[i].lerp(alvo, 0.1)

                sc  = self.hover_escala[i].x
                oy  = self.hover_escala[i].y
                cor = self.cor_hover if is_hovered else self.cor_base

                texto = botao.font.render(botao.text_input, True, cor)
                sombra_t = botao.font.render(botao.text_input, True, (50, 50, 50))
                w = int(texto.get_width()  * sc)
                h = int(texto.get_height() * sc)
                texto   = transform.scale(texto,   (w, h))
                sombra_t = transform.scale(sombra_t, (w, h))

                px = botao.x_pos - w // 2
                py = botao.y_pos - h // 2 + int(oy)

                tela.blit(sombra_t, (px + 3, py + 3))
                tela.blit(texto,    (px,     py))

        except Exception as e:
            print(f"[PAUSE CRASH] {type(e).__name__}: {e}")

    def checar_clique_pause(self, mouse_pos):
        try:
            if not self.menu_ativo:
                return None
            for botao in self.botoes:
                if botao.checkForInput(mouse_pos):
                    if botao.value == "continuar":
                        musica.retomar()
                        self.menu_ativo = False
                    return botao.value
            return None
        except Exception as e:
            print(f"[PAUSE CLICK CRASH] {type(e).__name__}: {e}")
            return None
