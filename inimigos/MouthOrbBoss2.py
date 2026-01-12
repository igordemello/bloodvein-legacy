from pygame import *
import math
import random
from pygame import time
from inimigo import Inimigo
from inimigos.orb import Orb
from utils import resource_path 

class MouthOrb2(Inimigo):
    def __init__(self, x, y, largura, altura, nome="Vovó Orbe", hp=6500, velocidade=5, dano=65):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)

        self.nome = nome
        self.ehboss = True

        self.sprites_idle = image.load(resource_path('./assets/Enemies/MouthOrb-IdleSheet-Sheet2.png')).convert_alpha() #12frames
        self.sprites_ataque = image.load(resource_path('./assets/Enemies/MouthOrb2-AttackSheet.png')).convert_alpha() #4frames
        self.sprites_invocacao = image.load(resource_path('./assets/Enemies/MouthOrb2-SpawnSheet.png')).convert_alpha() #10frames

        self.frame_width = 64
        self.frame_height = 64
        self.animation_speed = 0.10

        self.frames_idle = self.carregar_frames(self.sprites_idle, 12)
        self.frames_ataque = self.carregar_frames(self.sprites_ataque, 4)
        self.frames_invocacao = self.carregar_frames(self.sprites_invocacao, 10)

        self.frames = self.frames_idle

        self.estado = "idle"
        
        self.tipo_colisao = 'voador'

        self.distancia_ataque = 100
        self.cooldown_ataque = 1500
        self.tempo_ultimo_ataque = 0
        self.executando_ataque = False

        self.cooldown_invocacao = 2000
        self.tempo_ultima_invocacao = 0
        self.invocando = False
        self.orbs_instanciados = []
        self.max_orbs = 7


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
            elif novo_estado == "ataque":
                self.frames = self.frames_ataque
            elif novo_estado == "invocacao":
                self.frames = self.frames_invocacao

    def instanciar_orb(self, sala):
        mapa = Rect(248,100,1425,775)

        orb_x = self.x + self.largura // 2 - 32

        centro_vertical_mapa = mapa.y + mapa.height // 2

        if self.y < centro_vertical_mapa:
            orb_y = self.y + self.altura + 10
        else:
            orb_y = self.y - 64 - 10

        orb = Orb(orb_x, orb_y, 64, 64, hp=400)
        orb.nome_base = "Orb"
        sala.adicionar_inimigo(orb)


    def atualizar(self, player_pos, tela, sala):
        if self.esta_atordoado() or self.hp <= 0:
            self.vivo = False
            self.vx = 0
            self.vy = 0
            return

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


        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        distancia = math.hypot(dx, dy)

        # Atacar se estiver perto
        if distancia < self.distancia_ataque and now - self.tempo_ultimo_ataque > self.cooldown_ataque:
            self.trocar_estado("ataque")
            self.tempo_ultimo_ataque = now
            self.executando_ataque = True
            self.vx = self.vy = 0
        # Invocar se cooldown
        elif now - self.tempo_ultima_invocacao > self.cooldown_invocacao and len(self.orbs_instanciados) < self.max_orbs:
            self.trocar_estado("invocacao")
            self.tempo_ultima_invocacao = now
            self.invocando = True
            self.vx = self.vy = 0
        else:
            if self.estado not in ["ataque", "invocacao"]:
                player_x = player_pos[0]
                player_y = player_pos[1]

                self.vx = 0
                self.vy = 0

                if abs(player_x - self.x) > 200:
                    self.vx = self.velocidade if player_x > self.x else -self.velocidade
                if abs(player_y - self.y) > 200:
                    self.vy = self.velocidade if player_y > self.y else -self.velocidade

        # Finalizar ataque/invocação após animação
        if self.estado == "ataque" and self.frame_index == 3: #3 se refere a quantidade de frames de ataque - 1
            self.executando_ataque = False
            center_x = self.x + self.largura // 2
            center_y = self.y + self.altura // 2
            distancia = math.hypot(player_pos[0] - center_x, player_pos[1] - center_y)
            if distancia < 250:
                if hasattr(self, "dar_dano") and callable(self.dar_dano):
                    self.dar_dano()
            self.trocar_estado("idle")


        if self.estado == "invocacao" and self.frame_index == 9: #9 se refere a quantidade de frames de invocação - 1
            self.instanciar_orb(sala)
            self.invocando = False
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

        # draw.rect(tela,(255,0,0), self.get_hitbox(), 1)

    def get_hitbox(self):
        return Rect(self.x+20, self.y+20, self.largura-40, self.altura-40)