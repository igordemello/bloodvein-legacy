from pygame import *
import math
from random import choice
from inimigo import Inimigo
from utils import resource_path
from pathfinding import a_star

def pixel_para_grid(x, y, offset, tile_size_scaled):
    return int((x - offset[0]) / tile_size_scaled), int((y - offset[1]) / tile_size_scaled)

def grid_para_pixel(grid_x, grid_y, offset, tile_size_scaled):
    x = offset[0] + (grid_x * tile_size_scaled) + (tile_size_scaled / 2)
    y = offset[1] + (grid_y * tile_size_scaled) + (tile_size_scaled / 2)
    return x, y

class RatoDeSangue(Inimigo):
    def __init__(self, x, y, largura=24, altura=24, nome="Rato de Sangue", hp=60, velocidade=2.5, dano=12):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        self.rect.inflate_ip(10, 10)
        self.nome = nome

        self.tipo_colisao = 'obstaculo'
        self.frame_width = 32
        self.frame_height = 32
        self.animation_speed = 0.2
        self.tile_size_scaled = 32 * 3.25

        self.sprite_andando = image.load(resource_path('assets/enemies/RatoDeSangue-Andando.png')).convert_alpha()
        self.sprite_ataque = image.load(resource_path('assets/enemies/RatoDeSangue-Ataque.png')).convert_alpha()

        self.frames_andando = self.carregar_frames(self.sprite_andando, 7)
        self.frames_ataque = self.carregar_frames(self.sprite_ataque, 6)
        self.frames = self.frames_andando

        self.estado = "rand"
        self.ultimo_objetivo = None
        self.caminho_atual = []
        self.direcao_atual = [0, 0]
        self.tempo_ultima_mudanca = time.get_ticks()

        self.cooldown_ataque = 600
        self.tempo_ultimo_ataque = 0
        self.em_cooldown = False

    def carregar_frames(self, spritesheet, total_frames):
        frames = []
        for i in range(total_frames):
            rect = Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            frame = Surface((self.frame_width, self.frame_height), SRCALPHA)
            frame.blit(spritesheet, (0, 0), rect)
            frame = transform.scale(frame, (self.largura, self.altura))
            frames.append(frame)
        return frames

    def atualizar(self, player_pos, tela, matriz_colisao, offset_mapa):
        if self.esta_atordoado() or self.hp <= 0:
            self.vivo = False
            self.vx = 0
            self.vy = 0
            return
        now = time.get_ticks()
        if self.esta_atordoado() or self.hp <= 0:
            self.vx = self.vy = 0
            self.vivo = False
            return

        if now - self.knockback_time < self.knockback_duration:
            return

        px, py = player_pos
        centro_rato = self.rect.center
        distancia = math.hypot(px - centro_rato[0], py - centro_rato[1])

        if distancia < 80:
            self.estado = "atacando"
        elif distancia < 300:
            self.estado = "perseguindo"
        else:
            self.estado = "rand"

        if self.estado == "rand":
            if now - self.tempo_ultima_mudanca > 800:
                self.direcao_atual = [choice([-1, 0, 1]), choice([-1, 0, 1])]
                self.tempo_ultima_mudanca = now

            self.vx = self.direcao_atual[0] * self.velocidade
            self.vy = self.direcao_atual[1] * self.velocidade
            self.frames = self.frames_andando

        elif self.estado == "perseguindo":
            start = pixel_para_grid(*self.rect.center, offset_mapa, self.tile_size_scaled)
            goal = pixel_para_grid(px, py, offset_mapa, self.tile_size_scaled)

            if self.ultimo_objetivo != goal or not self.caminho_atual:
                self.caminho_atual = a_star(matriz_colisao, start, goal)
                self.ultimo_objetivo = goal

            if self.caminho_atual and len(self.caminho_atual) > 1:
                destino = grid_para_pixel(*self.caminho_atual[1], offset_mapa, self.tile_size_scaled)
                dx = destino[0] - self.rect.centerx
                dy = destino[1] - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 5:
                    self.vx = (dx / dist) * self.velocidade
                    self.vy = (dy / dist) * self.velocidade
                else:
                    self.caminho_atual.pop(0)
            else:
                self.vx = self.vy = 0
            self.frames = self.frames_andando

        elif self.estado == "atacando":
            self.vx = self.vy = 0
            self.frames = self.frames_ataque
            if not self.em_cooldown:
                self.frame_index = 0
                self.tempo_ultimo_ataque = now
                self.em_cooldown = True
                area_ataque = self.rect.inflate(self.rect.width * 0.5, self.rect.height * 0.5)
                if hasattr(self, "dar_dano") and callable(self.dar_dano):
                    try:
                        self.dar_dano(area_ataque, None)
                    except TypeError:
                        self.dar_dano()

        if self.em_cooldown and now - self.tempo_ultimo_ataque > self.cooldown_ataque:
            self.em_cooldown = False

        if hasattr(self, 'veneno_ativo') and self.veneno_ativo:
            if now >= self.veneno_proximo_tick and self.veneno_ticks > 0:
                self.hp -= self.veneno_dano_por_tick
                self.veneno_ticks -= 1
                self.veneno_proximo_tick = now + self.veneno_intervalo

                self.anima_hit = True
                self.time_last_hit_frame = now
                self.ultimo_dano = self.veneno_dano_por_tick
                self.ultimo_dano_tempo = time.get_ticks()

            if self.veneno_ticks <= 0:
                self.veneno_ativo = False

        self.set_velocidade_x(self.vx)
        self.set_velocidade_y(self.vy)
        self.atualizar_animacao()

    def desenhar(self, tela, playerpos, offset=(0, 0), mouse_pos=(0, 0)):
        if not self.vivo or not self.frames:
            return

        offset_x, offset_y = offset
        draw_x = self.rect.x + offset_x
        draw_y = self.rect.y + offset_y

        self.desenha_debuffs(tela)
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max, mouse_pos)


        frame = self.frames[self.frame_index % len(self.frames)]

        if abs(self.vx) > abs(self.vy):
            if self.vx > 0:
                frame = transform.rotate(frame, 90)
            else:
                frame = transform.rotate(frame, -90)

        if self.anima_hit:
            frame = self.aplicar_efeito_hit(frame)

        tela.blit(frame, (draw_x, draw_y))

        vida_maxima = getattr(self, "hp_max", 100)
        largura_barra = 500
        porcentagem = max(0, min(self.hp / vida_maxima, 1))
        largura_hp = porcentagem * largura_barra

        barra_x = 980 - (largura_barra / 2)
        barra_y = 0

        if hasattr(self, 'ultimo_dano') and time.get_ticks() - self.ultimo_dano_tempo < 2500:
            draw.rect(tela, (10, 10, 10), (barra_x - 20, barra_y + 30, largura_barra, 50))
            draw.rect(tela, (150, 0, 0), (barra_x - 20, barra_y + 30, largura_hp, 50))
            draw.rect(tela, (255, 255, 255), (barra_x - 20, barra_y + 30, largura_barra, 50), 1)

            fonte = font.Font(resource_path('assets/Fontes/alagard.ttf'), 24)
            texto = fonte.render(str(self.nome), True, (255, 255, 255))
            texto_rect = texto.get_rect(center=(barra_x - 20 + largura_barra / 2, barra_y + 30 + 25))
            tela.blit(texto, texto_rect)

        self.desenhar_dano(tela, offset)
