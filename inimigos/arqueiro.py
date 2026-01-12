from pygame import *
import math
import random
from inimigo import Inimigo
from utils import resource_path

class Arqueiro(Inimigo):
    def __init__(self, x, y, largura=48, altura=48, hp=85, velocidade=1.5, dano=18):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        self.nome = "Arqueiro"
        self.tipo_colisao = 'obstaculo'
        self.vivo = True

        # Sprites
        self.sprite_ataque = image.load(resource_path('assets/enemies/arqueiro_ataque.png')).convert_alpha()
        self.sprite_lado = image.load(resource_path('assets/enemies/arqueiro_Andando_Lado.png')).convert_alpha()
        self.sprite_costas = image.load(resource_path('assets/enemies/arqueiro_andando_costas.png')).convert_alpha()
        self.sprite_frente = image.load(resource_path('assets/enemies/arqueiro_Andando.png')).convert_alpha()

        self.frames_frente = self.carregar_frames(self.sprite_frente, 6)
        self.frames_costas = self.carregar_frames(self.sprite_costas, 6)
        self.frames_lado = self.carregar_frames(self.sprite_lado, 8)
        self.frames_ataque_direita = self.carregar_frames(self.sprite_ataque, 6)
        self.frames_ataque_esquerda = [transform.flip(f, True, False) for f in self.frames_ataque_direita]
        self.frames = self.frames_frente

        self.frame_index = 0
        self.frame_time = 0
        self.animation_speed = 0.15

        self.estado = 'andando'
        self.destino = self._escolher_canto()
        self.posicao_anterior = (self.x, self.y)
        self.tempo_parado = 0
        self.limite_parado = 1500

        self.projeteis = []
        self.cooldown_ataque = 1500
        self.ultimo_ataque = time.get_ticks()
        self.animando_ataque = False
        self.direcao = 'baixo'
        self.ataque_para_direita = True

    def carregar_frames(self, spritesheet, num_frames):
        frames = []
        frame_width = spritesheet.get_width() // num_frames
        for i in range(num_frames):
            rect = Rect(i * frame_width, 0, frame_width, spritesheet.get_height())
            frame = Surface((frame_width, spritesheet.get_height()), SRCALPHA)
            frame.blit(spritesheet, (0, 0), rect)
            frame = transform.scale(frame, (self.largura, self.altura))
            frames.append(frame)
        return frames

    def _escolher_canto(self):
        opcoes = [(64, 64), (64, 600), (1000, 64), (1000, 600)]
        return min(opcoes, key=lambda c: (c[0] - self.x)**2 + (c[1] - self.y)**2)

    def atualizar(self, player_pos, tela, matriz_colisao, offset):
        if self.esta_atordoado() or self.hp <= 0:
            self.vivo = False
            self.vx = 0
            self.vy = 0
            return
        now = time.get_ticks()

        if self.hp <= 0:
            self.vivo = False
            return

        dx = self.destino[0] - self.x
        dy = self.destino[1] - self.y
        dist = math.hypot(dx, dy)

        if self.estado == 'andando':
            if dist < 2:
                self.estado = 'sentinela'
                self.set_velocidade_x(0)
                self.set_velocidade_y(0)
                self.frame_index = 0
            else:
                self.vx = dx / dist * self.velocidade
                self.vy = dy / dist * self.velocidade
                self.set_velocidade_x(self.vx)
                self.set_velocidade_y(self.vy)

                if abs(self.x - self.posicao_anterior[0]) < 0.5 and abs(self.y - self.posicao_anterior[1]) < 0.5:
                    self.tempo_parado += now - getattr(self, 'ultimo_tempo', now)
                    if self.tempo_parado > self.limite_parado:
                        self.estado = 'sentinela'
                        self.set_velocidade_x(0)
                        self.set_velocidade_y(0)
                        self.frame_index = 0
                else:
                    self.tempo_parado = 0
                    self.posicao_anterior = (self.x, self.y)

                self.ultimo_tempo = now
                self.frames = self._get_direcao_frames()

        if self.estado == 'sentinela':
            self.set_velocidade_x(0)
            self.set_velocidade_y(0)
            if self.animando_ataque:
                if self.frame_index >= len(self.frames) - 1:
                    self.animando_ataque = False
                    self.frames = self.frames_frente
                    self.frame_index = 0
            elif now - self.ultimo_ataque > self.cooldown_ataque:
                self.ultimo_ataque = now
                self.animando_ataque = True
                self.frames = self.frames_ataque_direita if self.ataque_para_direita else self.frames_ataque_esquerda
                self.frame_index = 0
                self._atirar(player_pos)

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

        self.rect.topleft = (round(self.x), round(self.y))
        self.atualizar_animacao()
        self._atualizar_projeteis(player_pos)

    def _get_direcao_frames(self):
        if abs(self.vx) > abs(self.vy):
            self.direcao = 'direita' if self.vx > 0 else 'esquerda'
            base = self.frames_lado
            return base if self.vx > 0 else [transform.flip(f, True, False) for f in base]
        else:
            self.direcao = 'baixo' if self.vy > 0 else 'cima'
            return self.frames_frente if self.vy > 0 else self.frames_costas

    def _atirar(self, player_pos):
        centro = (self.x + self.largura // 2, self.y + self.altura // 2)
        dx = player_pos[0] - centro[0]
        dy = player_pos[1] - centro[1]
        angulo = math.atan2(dy, dx)
        self.ataque_para_direita = dx > 0

        velocidade = 6
        sprite_flecha = image.load(resource_path('assets/enemies/felha_do_arqueiro.png')).convert_alpha()
        tamanho = 22
        self.projeteis.append({
            "x": centro[0],
            "y": centro[1],
            "vx": math.cos(angulo) * velocidade,
            "vy": math.sin(angulo) * velocidade,
            "dano": self.dano,
            "lifetime": 300,
            "sprite": sprite_flecha,
            "tamanho": tamanho,
            "angulo": math.degrees(angulo),
            "raio_hitbox": tamanho // 2
        })

    def _atualizar_projeteis(self, player_pos):
        for p in self.projeteis[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["lifetime"] -= 1
            if p["lifetime"] <= 0:
                self.projeteis.remove(p)

    def atualizar_animacao(self):
        if self.estado == 'sentinela' and not self.animando_ataque:
            self.frame_index = 0
            self.frames = self.frames_frente
            return

        self.frame_time += self.animation_speed
        if self.frame_time >= 1:
            self.frame_time = 0
            if self.frames:
                self.frame_index = (self.frame_index + 1) % len(self.frames)
            else:
                self.frame_index = 0

    def desenhar(self, tela, player_pos, offset=(0, 0)):
        if not self.vivo:
            return

        self.desenha_debuffs(tela)
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max)
        draw_x = self.x + offset[0]
        draw_y = self.y + offset[1]

        if not self.frames:
            frame = Surface((self.largura, self.altura), SRCALPHA)
        else:
            frame = self.frames[min(self.frame_index, len(self.frames) - 1)]

        if self.anima_hit:
            frame = self.aplicar_efeito_hit(frame)

        tela.blit(frame, (draw_x, draw_y))

        for p in self.projeteis:
            sprite_rotacionado = transform.rotate(p["sprite"], -p["angulo"])
            sprite_resized = transform.scale(sprite_rotacionado, (p["tamanho"], p["tamanho"]))
            tela.blit(sprite_resized, (p["x"] + offset[0], p["y"] + offset[1]))

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
