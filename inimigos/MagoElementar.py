from pygame import *
import math
import random
from inimigo import Inimigo
from utils import resource_path

class MagoElementar(Inimigo):
    def __init__(self, x, y, largura=48, altura=48, hp=200, velocidade=2, dano=22):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        self.nome = "Mago Elementar"
        self.tipo_colisao = 'obstaculo'
        self.vivo = True

        self.sprite_frente = image.load(resource_path('assets/enemies/Mago_andando.png')).convert_alpha()
        self.sprite_costas = image.load(resource_path('assets/enemies/Mago_andando_Costas.png')).convert_alpha()
        self.sprite_direita = image.load(resource_path('assets/enemies/Mago_andando_ladodireito.png')).convert_alpha()
        self.sprite_ataque_fogo = image.load(resource_path('assets/enemies/Mago_ataque_fogo.png')).convert_alpha()
        self.sprite_ataque_gelo = image.load(resource_path('assets/enemies/Mago_ataque_gelo.png')).convert_alpha()

        self.frames_frente = self.carregar_frames(self.sprite_frente, 6)
        self.frames_costas = self.carregar_frames(self.sprite_costas, 6)
        self.frames_direita = self.carregar_frames(self.sprite_direita, 8)
        self.frames_direita_flip = [transform.flip(frame, True, False) for frame in self.frames_direita]
        self.frames_ataque_fogo = self.carregar_frames(self.sprite_ataque_fogo, 4)
        self.frames_ataque_gelo = self.carregar_frames(self.sprite_ataque_gelo, 4)

        self.frames = self.frames_frente
        self.direcao = "baixo"

        self.frame_index = 0
        self.frame_time = 0
        self.animation_speed = 0.15

        self.tempo_ultima_mudanca = time.get_ticks()
        self.direcao_atual = [0, 0]

        self.estado = "andando"
        self.projeteis = []
        self.cooldown_gelo = 4000
        self.cooldown_fogo = 5000
        self.ultimo_gelo = 0
        self.ultimo_fogo = 0

        self.sprite_gelo = image.load(resource_path('assets/enemies/Bola_de_Gelo.png')).convert_alpha()
        self.sprite_fogo = image.load(resource_path('assets/enemies/Bola_de_Fogo.png')).convert_alpha()

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

        if self.estado == "andando":
            if now - self.tempo_ultima_mudanca > 1000:
                self.direcao_atual = [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])]
                self.tempo_ultima_mudanca = now

            dx = self.x - player_pos[0]
            dy = self.y - player_pos[1]
            dist = math.hypot(dx, dy)
            if dist < 250:
                dx, dy = dx / dist, dy / dist
                self.vx = dx * self.velocidade
                self.vy = dy * self.velocidade
            else:
                self.vx = self.direcao_atual[0] * self.velocidade
                self.vy = self.direcao_atual[1] * self.velocidade

            if abs(self.vx) > abs(self.vy):
                nova_frames = self.frames_direita if self.vx > 0 else self.frames_direita_flip
            else:
                nova_frames = self.frames_frente if self.vy > 0 else self.frames_costas

            if self.frames != nova_frames:
                self.frames = nova_frames
                self.frame_index = 0

            if self.vx == 0 and self.vy == 0:
                self.frame_index = 0  # animação parada

            if now - self.ultimo_gelo >= self.cooldown_gelo:
                self.estado = "atacando_gelo"
                self.frames = self.frames_ataque_gelo
                self.frame_index = 0
            elif now - self.ultimo_fogo >= self.cooldown_fogo:
                self.estado = "atacando_fogo"
                self.frames = self.frames_ataque_fogo
                self.frame_index = 0

        elif self.estado == "atacando_gelo":
            if self.frame_index >= len(self.frames) - 1:
                self.atacar_gelo(player_pos)
                self.estado = "andando"
                self.ultimo_gelo = now
                self.frames = self.frames_frente
                self.frame_index = 0
            self.vx = self.vy = 0

        elif self.estado == "atacando_fogo":
            if self.frame_index >= len(self.frames) - 1:
                self.atacar_fogo()
                self.estado = "andando"
                self.ultimo_fogo = now
                self.frames = self.frames_frente
                self.frame_index = 0
            self.vx = self.vy = 0

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

        self.atualizar_projeteis()
        self.atualizar_animacao()

    def atacar_gelo(self, player_pos):
        angulo = math.atan2(player_pos[1] - self.y, player_pos[0] - self.x)
        self.projeteis.append({
            "x": self.x + self.largura // 2,
            "y": self.y + self.altura // 2,
            "vx": math.cos(angulo) * 6,
            "vy": math.sin(angulo) * 6,
            "dano": self.dano,
            "congelar": True,
            "sprite": self.sprite_gelo,
            "lifetime": 999,
            "raio_hitbox": 12
        })

    def atacar_fogo(self):
        centro = (self.x + self.largura // 2, self.y + self.altura // 2)
        for direcao in [-1, 1]:
            self.projeteis.append({
                "x": centro[0],
                "y": centro[1],
                "vx": direcao * 6,
                "vy": 0,
                "dano": self.dano,
                "congelar": False,
                "sprite": self.sprite_fogo,
                "lifetime": 999,
                "raio_hitbox": 12
            })

    def atualizar_projeteis(self):
        for p in self.projeteis[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["lifetime"] -= 1
            if p["lifetime"] <= 0:
                self.projeteis.remove(p)

    def desenhar(self, tela, player_pos, offset=(0, 0)):
        offset_x, offset_y = offset
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y
        self.desenha_debuffs(tela)
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max)


        if self.frames:
            frame_index = min(self.frame_index, len(self.frames) - 1)
            frame = self.frames[frame_index]
        else:
            frame = Surface((self.largura, self.altura))

        frame = self.aplicar_efeito_hit(frame)
        tela.blit(frame, (draw_x, draw_y))

        for p in self.projeteis:
            if "sprite" in p:
                tela.blit(p["sprite"], (p["x"] + offset_x, p["y"] + offset_y))


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
