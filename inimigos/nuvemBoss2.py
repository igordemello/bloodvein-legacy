from pygame import *
import math
import random
from pygame import time
from inimigo import Inimigo
from utils import resource_path 
from projectile_light import ProjectileLight
class NuvemBoss2(Inimigo):
    def __init__(self, x, y, largura, altura, nome="Visão Ácida", hp=8000, velocidade=4, dano=75):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)

        self.nome = nome
        self.ehboss = True

        self.sprites_idle = image.load(resource_path('./assets/Enemies/nuvem2_idle.png')).convert_alpha() #4frames
        self.sprites_raio = image.load(resource_path('./assets/Enemies/nuvem2_raio.png')).convert_alpha() #4frames
        self.sprites_campo_forca = image.load(resource_path('./assets/Enemies/nuvem_campo_de_força2.png')).convert_alpha() #5frames

        self.frame_width = 200
        self.frame_height = 200
        self.animation_speed = 0.10

        self.asset_raio_frame_width = 200
        self.asset_raio_frame_height = 200

        self.asset_orb = image.load(resource_path('./assets/Enemies/bola_de_ataque_nuvem.png')).convert_alpha()
        self.asset_orb_size = 32

        self.frames_idle = self.carregar_frames(self.sprites_idle, 4)
        self.frames_raio = self.carregar_frames(self.sprites_raio, 4)
        self.frames_campo_forca = self.carregar_frames(self.sprites_campo_forca, 5)


        self.frames = self.frames_idle

        self.estado = "idle"
        
        self.tipo_colisao = 'voador'


        self.cooldown_ataque = 3000 #ms

        self.estado_ataque = "esperando"  # pode ser: esperando, campo_forca, raio
        self.inicio_ataque = 0
        self.invulneravel = False
        self.projeteis = []
        self.cooldown_entre_ataques = 1000
        self.ultimo_ataque = 0
        
        self.tempo_ataque_campo = 3000
        self.tempo_ataque_raio = 2000
        self.raio_atual = 0
        self.raio_maximo = 200
        self.frame_raio_index = 0

        # Área de movimento do morcego
        self.area_movimento = Rect(280, 160, 1350, 650)

        # Configurações do movimento em zig-zag
        self.direcao = random.choice([-1, 1])
        self.altura_zigzag = random.randint(20, 100)  # Altura do padrão de zig-zag
        self.contador_zigzag = random.randint(0, 100)
        self.velocidade = velocidade * random.uniform(0.8, 1.2)
        self.frequencia_zigzag = random.uniform(0.08, 0.12)
        self.ponto_inicial = (x, y)  # Ponto onde o morcego começa
        self.velocidade_original = velocidade
        
    def carregar_frames(self, spritesheet, num_frames):
        frames = []
        for i in range(num_frames):
            rect = Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            frame = Surface((self.frame_width, self.frame_height), SRCALPHA)
            frame.blit(spritesheet, (0, 0), rect)
            frame = transform.scale(frame, (self.largura, self.altura))
            frames.append(frame)
        return frames
    
    def atualizar_animacao(self):
        self.frame_time += self.animation_speed
        if self.frame_time >= 1:
            self.frame_time = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def trocar_estado(self, novo_estado):
        if self.estado != novo_estado:
            self.estado = novo_estado
            self.frame_index = 0
            self.frame_time = 0

            if novo_estado == "idle":
                self.frames = self.frames_idle
            elif novo_estado == "raio":
                self.frames = self.frames_raio
            elif novo_estado == "chuva":
                self.frames = self.frames_chuva
            elif novo_estado == "campo_forca":
                self.frames = self.frames_campo_forca

    def atualizar(self, player_pos, tela, player):
        if self.esta_atordoado() or self.hp <= 0:
            self.vivo = False
            self.vx = 0
            self.vy = 0
            return
        
        for projetil in self.projeteis[:]:
            # Atualiza direção em tempo real (teleguiado)
            dx = player_pos[0] - projetil["x"]
            dy = player_pos[1] - projetil["y"]
            distancia = math.hypot(dx, dy)

            if distancia != 0:
                dx /= distancia
                dy /= distancia

            velocidade = 8

            projetil["vx"] = dx * velocidade
            projetil["vy"] = dy * velocidade

            projetil["x"] += projetil["vx"]
            projetil["y"] += projetil["vy"]
            projetil["lifetime"] -= 1

            if projetil["lifetime"] <= 0:
                self.projeteis.remove(projetil)
        
        now = time.get_ticks()
        # Knockback
        if now - self.knockback_time < self.knockback_duration:
            self.x += self.vx
            self.y += self.vy
            self.rect.topleft = (self.x, self.y)
            return
        else:
            self.knockback_x = 0
            self.knockback_y = 0
            self.set_velocidade_x(0)
            self.set_velocidade_y(0)
        

        
        distancia_player = math.hypot(player_pos[0] - self.x, player_pos[1] - self.y)

        # Movimento zig-zag
        self.vx = self.velocidade * self.direcao

        # Cálculo do movimento vertical (zig-zag)
        self.contador_zigzag += 1
        if self.contador_zigzag > random.randint(80, 120):  # Ajuste este valor para mudar a frequência do zig-zag
            self.contador_zigzag = 0
            self.altura_zigzag = random.randint(40, 80)  # Varia a altura do zig-zag

        # Usando seno para criar o padrão de zig-zag suave
        self.vy = math.sin(self.contador_zigzag * self.frequencia_zigzag) * 2

        # Atualiza posição
        self.x += self.vx
        self.y += self.vy

        # Verifica os limites da área de movimento
        if self.x < self.area_movimento.left:
            self.direcao = 1
            self.x = self.area_movimento.left
        elif self.x > self.area_movimento.right - self.largura:
            self.direcao = -1
            self.x = self.area_movimento.right - self.largura

        if self.y < self.area_movimento.top:
            self.y = self.area_movimento.top
            self.vy = abs(self.vy)
        elif self.y > self.area_movimento.bottom - self.altura:
            self.y = self.area_movimento.bottom - self.altura
            self.vy = -abs(self.vy)

        if self.estado_ataque == "esperando":
            if now - self.ultimo_ataque > self.cooldown_entre_ataques:
                self.estado_ataque = random.choice(["campo_forca", "raio"])
                self.inicio_ataque = now

                if self.estado_ataque == "campo_forca":
                    self.invulneravel = True
                    self.trocar_estado("campo_forca")

                elif self.estado_ataque == "raio":
                    self.invulneravel = False
                    self.trocar_estado("raio")
                    self.raio_atual = 0

        elif self.estado_ataque == "campo_forca":
            if now - self.inicio_ataque > self.tempo_ataque_campo:
                self.estado_ataque = "esperando"
                self.ultimo_ataque = now
                self.invulneravel = False
                self.trocar_estado("idle")
            else:
                # Disparar orbes perseguidoras
                if now % 500 < 50:  # a cada ~500ms
                    self.atirar_orbe(player_pos)

        elif self.estado_ataque == "raio":
            f1 = Rect(self.x + 100, self.y + 120, self.largura - 200, self.altura - 240)
            f2 = Rect(self.x + 66, self.y + 86, self.largura - 132, self.altura - 172)
            f3 = Rect(self.x + 33, self.y + 53, self.largura - 66, self.altura - 106)
            f4 = Rect(self.x, self.y + 20, self.largura, self.altura - 40)

            if now - self.inicio_ataque < self.tempo_ataque_raio:
                # Cresce o raio
                t = (now - self.inicio_ataque) / self.tempo_ataque_raio
                self.raio_atual = self.raio_maximo * t

                hitbox_player = player.get_hitbox()

                if self.frame_index == 0 and f1.colliderect(hitbox_player):
                    if hasattr(self, "dar_dano") and callable(self.dar_dano):
                        self.dar_dano()
                elif self.frame_index == 1 and f2.colliderect(hitbox_player):
                    if hasattr(self, "dar_dano") and callable(self.dar_dano):
                        self.dar_dano()
                elif self.frame_index == 2 and f3.colliderect(hitbox_player):
                    if hasattr(self, "dar_dano") and callable(self.dar_dano):
                        self.dar_dano()
                elif self.frame_index == 3 and f4.colliderect(hitbox_player):
                    if hasattr(self, "dar_dano") and callable(self.dar_dano):
                        self.dar_dano()

            else:
                self.estado_ataque = "esperando"
                self.ultimo_ataque = now
                self.raio_atual = 0
                self.trocar_estado("idle")


        
        

        self.atualizar_animacao()


    def desenhar(self, tela, playerpos, offset=(0, 0)):
        if not self.vivo or not self.frames:
            return
        
        if self.frame_index >= len(self.frames):
            self.frame_index = 0

        offset_x, offset_y = offset
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y

        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max)

        frame = self.frames[self.frame_index]

        # Aplica efeito de hit, se necessário
        if self.anima_hit:
            frame = self.aplicar_efeito_hit(frame)

        tela.blit(frame, (draw_x, draw_y))
        self.desenhar_dano(tela, offset)

        # Desenhar projéteis
        for projetil in self.projeteis:
            proj_sprite = transform.scale(self.asset_orb, (projetil["tamanho"], projetil["tamanho"]))
            draw_x = projetil["x"] - projetil["tamanho"] // 2 + offset[0]
            draw_y = projetil["y"] - projetil["tamanho"] // 2 + offset[1]
            tela.blit(proj_sprite, (draw_x, draw_y))

        # draw.rect(tela,(255,0,0), self.get_hitbox(),1)
        


    def get_hitbox(self):
        return Rect(self.x+100, self.y+120, self.largura-200, self.altura-240)
    
    def atirar_orbe(self, player_pos):
        angle = math.atan2(player_pos[1] - self.y, player_pos[0] - self.x)
        projetil = {
            "x": self.x + self.largura // 2,
            "y": self.y + self.altura // 2,
            "vx": math.cos(angle) * 10,
            "vy": math.sin(angle) * 10,
            "dano": self.dano/2,
            "lifetime": 100,
            "tamanho": self.asset_orb_size,
            "trail": [],
            "luz": ProjectileLight(
                    color=(30, 30, 200),
                    radius=70,
                    intensity=255,
                    steps=16
                )
        }
        self.projeteis.append(projetil)