from pygame import *
from pygame.math import Vector2
import cv2
from utils import resource_path 
class BotaoAnimado:
    def __init__(self, pos, text_input, font, base_color, hovering_color):
        self.pos = pos
        self.text_input = text_input
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.current_color = base_color
        self.scale = 1.0
        self.target_scale = 1.0
        self.scale_speed = 0.08
        self.update_text()

    def update_text(self):
        self.text = self.font.render(self.text_input, True, self.current_color)
        self.rect = self.text.get_rect(center=self.pos)

    def changeColor(self, mouse_position):
        if self.rect.collidepoint(mouse_position):
            self.target_scale = 1.1
        else:
            self.target_scale = 1.0

    def update(self, screen):
        # Transição de escala
        self.scale += (self.target_scale - self.scale) * self.scale_speed

        # Transição de cor
        r = self.base_color[0] + (self.hovering_color[0] - self.base_color[0]) * (self.scale - 1) * 10
        g = self.base_color[1] + (self.hovering_color[1] - self.base_color[1]) * (self.scale - 1) * 10
        b = self.base_color[2] + (self.hovering_color[2] - self.base_color[2]) * (self.scale - 1) * 10
        self.current_color = (int(r), int(g), int(b))

        # Atualiza texto com nova cor e aplica escala
        self.update_text()
        scaled_text = transform.rotozoom(self.text, 0, self.scale)
        new_rect = scaled_text.get_rect(center=self.pos)
        screen.blit(scaled_text, new_rect)

    def checkForInput(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

class GameOver:
    def __init__(self):
        self.font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 24)

        # Fonte e cores dos botões
        botao_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 72)
        cor_base = (180, 180, 180)
        cor_hover = (255, 255, 255)

        # Botões empilhados verticalmente
        pos_y = 900
        self.botaonovarun = BotaoAnimado((1920 // 2, pos_y-100), "NOVA RUN", botao_font, cor_base, cor_hover)
        self.botaoreiniciar = BotaoAnimado((1920 // 2, pos_y), "REINICIAR", botao_font, cor_base, cor_hover)
        self.botaosair = BotaoAnimado((1920 // 2, pos_y + 100), "SAIR", botao_font, cor_base, cor_hover)
        self.botoes = [self.botaonovarun, self.botaoreiniciar,self.botaosair]

        # Controle do fade-in da imagem
        self.alpha_overlay = 0
        self.max_alpha = 255
        self.velocidade_fade = 30
        self.menu_ativo = False

        # Carrega imagem de fundo do game over
        self.fundo_gameover = image.load(resource_path('assets/ui/gameover.png')).convert_alpha()
        self.fundo_gameover = transform.scale(self.fundo_gameover, (1920, 1080))  # Redimensiona se necessário

    def gameOverFuncionamento(self, tela, mouse_pos):
        self.menu_ativo = True

        # Atualiza a opacidade gradualmente
        if self.alpha_overlay < self.max_alpha:
            self.alpha_overlay = min(self.alpha_overlay + self.velocidade_fade, self.max_alpha)

        # Aplica alpha na imagem e desenha
        fundo_com_alpha = self.fundo_gameover.copy()
        fundo_com_alpha.set_alpha(self.alpha_overlay)
        tela.blit(fundo_com_alpha, (0, 0))

        # Título
        pause_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 96)
        pause_text = pause_font.render("Você Morreu!", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(1920 // 2, 150))
        tela.blit(pause_text, text_rect)

        # Hover e update dos botões
        for botao in self.botoes:
            botao.changeColor(mouse_pos)
            botao.update(tela)

    def checar_clique_pause(self, mouse_pos):
        if not self.menu_ativo:
            return None
        if self.botaonovarun.checkForInput(mouse_pos):
            return "nova run"
        if self.botaoreiniciar.checkForInput(mouse_pos):
            return "reiniciar"
        if self.botaosair.checkForInput(mouse_pos):
            return "sair"
        return None