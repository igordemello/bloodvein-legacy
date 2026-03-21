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

class VampiroSol(Inimigo):
    def __init__(self, x, y, largura=32, altura=32, nome="Vampiro Solar", hp=130, velocidade=2.5, dano=45):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        self.nome = nome
        self.tipo_colisao = 'obstaculo'
        self.tile_size_scaled = 32 * 3.25

        self.estado = "rand"
        self.forma = "vampiro"
        self.tempo_ultima_mudanca = time.get_ticks()
        self.tempo_ultimo_ataque = 0
        self.cooldown_entre_ataques = 2000

        self.ultimo_objetivo = None
        self.caminho_atual = []

        self.direcao = "baixo"

        # Sprites
        self.sprite_vampiro_frente = image.load(resource_path('assets/enemies/Vampiro_Sol-Andando.png')).convert_alpha()
        self.sprite_vampiro_costas = image.load(resource_path('assets/enemies/Vampiro_Sol-Andando_costas.png')).convert_alpha()
        self.sprite_vampiro_lado = image.load(resource_path('assets/enemies/Vampiro_Sol-Andando_lado.png')).convert_alpha()
        self.sprite_morcego = image.load(resource_path('assets/enemies/morcego_dovampirosol_correr.png')).convert_alpha()
        self.sprite_ataque = image.load(resource_path('assets/enemies/Vampiro_Sol-Ataque.png')).convert_alpha()

        self.frames_frente = self.carregar_frames(self.sprite_vampiro_frente, 6)
        self.frames_costas = self.carregar_frames(self.sprite_vampiro_costas, 6)
        self.frames_lado = self.carregar_frames(self.sprite_vampiro_lado, 8)
        self.frames_morcego = self.carregar_frames(self.sprite_morcego, 6)
        self.frames_ataque = self.carregar_frames(self.sprite_ataque, 6)
        self.frames = self.frames_frente

        self.frame_index = 0
        self.frame_time = 0
        self.animation_speed = 0.15
        self.flip_horizontal = False

    def carregar_frames(self, spritesheet, total_frames):
        frame_width = spritesheet.get_width() // total_frames
        frame_height = spritesheet.get_height()
        frames = []
        for i in range(total_frames):
            rect = Rect(i * frame_width, 0, frame_width, frame_height)
            frame = Surface((frame_width, frame_height), SRCALPHA)
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
        if self.hp <= 0:
            self.vivo = False
            return

        if self.estado == "cooldown":
            if now - self.tempo_ultimo_ataque > self.cooldown_entre_ataques:
                self.estado = "rand"
                self.forma = "vampiro"
                self.tipo_colisao = "obstaculo"
                self.frames = self.frames_frente
                self.frame_index = 0
            else:
                self.vx = self.vy = 0

        elif self.estado == "rand":
            if now - self.tempo_ultima_mudanca > 1000:
                self.vx = choice([-1, 0, 1]) * self.velocidade
                self.vy = choice([-1, 0, 1]) * self.velocidade
                self.tempo_ultima_mudanca = now

                if abs(self.vx) > abs(self.vy):
                    self.frames = self.frames_lado
                    self.flip_horizontal = self.vx < 0
                else:
                    self.frames = self.frames_frente if self.vy > 0 else self.frames_costas
                self.frame_index = 0

            px, py = player_pos
            dist = math.hypot(self.rect.centerx - px, self.rect.centery - py)
            if dist < 200:
                self.estado = "perseguindo"
                self.forma = "morcego"
                self.tipo_colisao = "voador"
                self.frames = self.frames_morcego
                self.frame_index = 0
                self.rect.inflate_ip(10, 10)  # aumenta a hitbox

        elif self.estado == "perseguindo":
            start = pixel_para_grid(*self.rect.center, offset_mapa, self.tile_size_scaled)
            goal = pixel_para_grid(*player_pos, offset_mapa, self.tile_size_scaled)

            if self.ultimo_objetivo != goal or not self.caminho_atual:
                self.caminho_atual = a_star(matriz_colisao, start, goal)
                self.ultimo_objetivo = goal

            if self.caminho_atual and len(self.caminho_atual) > 1:
                destino = grid_para_pixel(*self.caminho_atual[1], offset_mapa, self.tile_size_scaled)
                dx = destino[0] - self.rect.centerx
                dy = destino[1] - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 5:
                    self.vx = (dx / dist) * self.velocidade * 1.4
                    self.vy = (dy / dist) * self.velocidade * 1.4
                else:
                    self.caminho_atual.pop(0)
            else:
                self.vx = self.vy = 0

            if math.hypot(self.rect.centerx - player_pos[0], self.rect.centery - player_pos[1]) < 50:
                self.estado = "atacando"
                self.frames = self.frames_ataque
                self.frame_index = 0
                self.vx = self.vy = 0

        elif self.estado == "atacando":
            self.vx = self.vy = 0
            if self.frame_index >= len(self.frames) - 1:
                if hasattr(self, "dar_dano"):
                    self.dar_dano()
                self.estado = "cooldown"
                self.tempo_ultimo_ataque = now
                self.frames = self.frames_morcego
                self.frame_index = 0

        if hasattr(self, 'veneno_ativo') and self.veneno_ativo:
            if now >= self.veneno_proximo_tick and self.veneno_ticks > 0:
                self.hp -= self.veneno_dano_por_tick
                self.veneno_ticks -= 1
                self.veneno_proximo_tick = now + self.veneno_intervalo

                # Inicia animação de hit como feedback visual (opcional)
                self.anima_hit = True
                self.time_last_hit_frame = now
                self.ultimo_dano = self.veneno_dano_por_tick
                self.ultimo_dano_tempo = time.get_ticks()

            if self.veneno_ticks <= 0:
                self.veneno_ativo = False

        self.set_velocidade_x(self.vx)
        self.set_velocidade_y(self.vy)
        self.atualizar_animacao()
        self.rect.topleft = (round(self.x), round(self.y))

    def atualizar_animacao(self):
        if not self.frames:
            return

        # Fica parado no primeiro frame quando na forma vampiro e estado rand e sem movimento
        if self.forma == "vampiro" and self.estado == "rand" and self.vx == 0 and self.vy == 0:
            self.frame_index = 0
            return

        self.frame_time += self.animation_speed
        if self.frame_time >= 1:
            self.frame_time = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def desenhar(self, tela, playerpos, offset=(0, 0), mouse_pos=(0, 0)):
        if not self.vivo or not self.frames:
            return

        self.desenha_debuffs(tela)
        offset_x, offset_y = offset
        draw_x = self.rect.x + offset_x
        draw_y = self.rect.y + offset_y

        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max, mouse_pos)


        frame = self.frames[min(self.frame_index, len(self.frames) - 1)]
        if self.anima_hit:
            frame = self.aplicar_efeito_hit(frame)
        if self.frames == self.frames_lado and self.flip_horizontal:
            frame = transform.flip(frame, True, False)

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

            # Desenhar o nome centralizado
            fonte = font.Font(resource_path('assets/Fontes/alagard.ttf'), 24)
            texto = fonte.render(str(self.nome), True, (255, 255, 255))
            texto_rect = texto.get_rect(
                center=(barra_x - 20 + largura_barra / 2, barra_y + 30 + 25))  # 25 = altura/2 da barra
            tela.blit(texto, texto_rect)

        self.desenhar_dano(tela, offset)
