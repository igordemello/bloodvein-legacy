from pygame import *
import math
import random
from inimigo import Inimigo
from utils import resource_path

class AranhaDoSol(Inimigo):
    def __init__(self, x, y, largura=48, altura=48, hp=110, velocidade=2, dano=25):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        self.nome = "Aranha do Sol"
        self.tipo_colisao = 'voador'
        self.vivo = True

        # Sprites
        self.sprites_andando = image.load(resource_path('assets/enemies/AranhaSolar-Andar.png')).convert_alpha()
        self.sprites_ataque = image.load(resource_path('assets/enemies/AranhaSolar-Ataque.png')).convert_alpha()
        self.frames_andando = self.carregar_frames(self.sprites_andando, 4)
        self.frames_ataque = self.carregar_frames(self.sprites_ataque, 2)
        self.frames = self.frames_andando
        self.estado = 'andando'

        self.frame_index = 0
        self.frame_time = 0
        self.animation_speed = 0.2

        # Movimento aleatório
        self.direcao_timer = 0
        self.direcao_intervalo = 1000
        self.definir_nova_direcao()

        # Projéteis
        self.projeteis = []
        self.cooldown_ataque = 2000
        self.ultimo_ataque = time.get_ticks()

    def carregar_frames(self, spritesheet, num_frames):
        frames = []
        frame_width = spritesheet.get_width() // num_frames
        frame_height = spritesheet.get_height()
        for i in range(num_frames):
            rect = Rect(i * frame_width, 0, frame_width, frame_height)
            frame = Surface((frame_width, frame_height), SRCALPHA)
            frame.blit(spritesheet, (0, 0), rect)
            frame = transform.scale(frame, (self.largura, self.altura))
            frames.append(frame)
        return frames

    def definir_nova_direcao(self):
        angulo = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angulo) * self.velocidade
        self.vy = math.sin(angulo) * self.velocidade

    def atualizar(self, player_pos, tela, matriz_colisao, offset_mapa):
        if self.esta_atordoado() or self.hp <= 0:
            self.vivo = False
            self.vx = 0
            self.vy = 0
            return
        now = time.get_ticks()

        if self.hp <= 0:
            self.vivo = False
            self.vx = self.vy = 0
            return

        if now - self.knockback_time < self.knockback_duration:
            self.x += self.vx
            self.y += self.vy
            return

        if now - self.direcao_timer > self.direcao_intervalo:
            self.definir_nova_direcao()
            self.direcao_timer = now

        self.x += self.vx
        self.y += self.vy
        self.rect.topleft = (round(self.x), round(self.y))

        if now - self.ultimo_ataque >= self.cooldown_ataque:
            self.estado = 'atacando'
            self.frames = self.frames_ataque
            self.frame_index = 0
            self.atirar_projeteis()
            self.ultimo_ataque = now
        else:
            self.estado = 'andando'
            self.frames = self.frames_andando

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

        self.atualizar_projeteis()
        self.atualizar_animacao()

    def atualizar_animacao(self):
        self.frame_time += self.animation_speed
        if self.frame_time >= 1:
            self.frame_time = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def atirar_projeteis(self):
        centro_x = self.x + self.largura // 2
        centro_y = self.y + self.altura // 2
        sprite_bola = image.load(resource_path("assets/enemies/Bola_de_Fogo_Ataque.png")).convert_alpha()

        for direcao in [-8, 8]:  # Mais rápido: antes era -6 e 6
            self.projeteis.append({
                "x": centro_x,
                "y": centro_y,
                "vx": 0,
                "vy": direcao,
                "dano": self.dano,
                "raio_hitbox": 10,
                "lifetime": 80,
                "cor": (255, 100, 0),
                "tamanho": 20,  # Maior: antes era 16
                "sprite": sprite_bola
            })

    def atualizar_projeteis(self):
        for p in self.projeteis[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["lifetime"] -= 1
            if p["lifetime"] <= 0:
                self.projeteis.remove(p)

    def desenhar(self, tela, player_pos, offset=(0, 0)):
        if not self.vivo or not self.frames:
            return

        self.desenha_debuffs(tela)
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max)

        draw_x = self.x + offset[0]
        draw_y = self.y + offset[1]
        frame = self.frames[self.frame_index]

        # Gira o sprite 90° se estiver indo lateralmente
        if abs(self.vx) > abs(self.vy):
            if self.vx > 0:
                frame = transform.rotate(frame, -90)
            else:
                frame = transform.rotate(frame, 90)

        if self.anima_hit:
            frame = self.aplicar_efeito_hit(frame)

        tela.blit(frame, (draw_x, draw_y))

        for p in self.projeteis:
            proj_frame = transform.scale(p["sprite"], (p["tamanho"], p["tamanho"]))
            tela.blit(proj_frame, (p["x"] + offset[0] - p["tamanho"] // 2,
                                   p["y"] + offset[1] - p["tamanho"] // 2))

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

    def get_hitbox(self):
        return Rect(self.x + 5, self.y + 5, self.largura - 10, self.altura - 10)
