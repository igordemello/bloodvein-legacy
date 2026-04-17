from pygame import *
from pygame.locals import QUIT
import sys
from botao import Botao
from pygame.math import Vector2
import cv2
import numpy as np
from som import GerenciadorDeSom
from som import som
from som import GerenciadorDeMusica
from som import musica
from utils import resource_path 


BASE_W = 1920
BASE_H = 1080


class Config:
    def __init__(self, screen, game):
        self.screen = screen
        self.game = game

        self.resolucoes = [
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1366, 768),
            (1600, 900),
            (1920, 1080),
        ]

        self.indice = 5  # padrão

        self.modo = "fullscreen"  
        # "janela"
        # "fullscreen"

    def desenhar(self):
        fonte = font.SysFont("Arial", 40)
        texto = fonte.render(f"Resolucao: {self.resolucoes[self.indice]}", True, (255,255,255))
        self.screen.blit(texto, (500, 300))

    def proxima_resolucao(self):
        self.indice = (self.indice + 1) % len(self.resolucoes)

    def aplicar(self):
        largura, altura = self.resolucoes[self.indice]

        self.game.largura = largura
        self.game.altura = altura

        flags = DOUBLEBUF | HWSURFACE

        if self.modo == "fullscreen":
            flags |= FULLSCREEN

        display.quit()
        display.init()
        mouse.set_visible(False)

        self.game.window = display.set_mode(
            (largura, altura),
            flags=flags,
            vsync=1
        )

        self.game.scale_x = largura / BASE_W
        self.game.scale_y = altura / BASE_H