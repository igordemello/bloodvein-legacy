from pygame import *
import sys
from pygame.locals import QUIT
import math
from inimigo import Inimigo
import random
from utils import resource_path 

class Espectro(Inimigo):
    def __init__(self, x, y, largura, altura, hp, nome="Espectro", velocidade=3, dano=20):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        
        self.estado = "idle"
        self.ultima_mudanca_estado = time.get_ticks()
        self.tempo_idle = 1000
        self.duracao_ataque = 250 
        self.tempo_cooldown = 200 
        self.tempo_teleporte = 500

        self.nome = nome
        self.teleportando = False
        
        self.sprites_idle = image.load(resource_path('./assets/Enemies/fantasmaTP_idle.png')).convert_alpha()
        self.sprites_run = image.load(resource_path('./assets/Enemies/fantasmaTP_run.png')).convert_alpha()
        self.sprites_ataque = image.load(resource_path('./assets/Enemies/fantasmaTP_ataque.png')).convert_alpha()
        
        self.frame_width = 32
        self.frame_height = 32
        self.animation_speed = 0.30
        
        self.idle_frames = 4
        self.run_frames = 6
        self.ataque_frames = 5
        self.costas_frames = 6
        
        self.frames_idle = self.carregar_frames(self.sprites_idle, self.idle_frames)
        self.frames_run = self.carregar_frames(self.sprites_run, self.run_frames)
        self.frames_ataque = self.carregar_frames(self.sprites_ataque, self.ataque_frames)
        
        self.frames = self.frames_idle
        self.frame_index = 0
        self.ultimo_frame_tempo = time.get_ticks()
        
        self.tipo_colisao = 'voador'
        self.raio_ataque = 70
        self.raio_perseguicao = 500
        self.tempo_ultimo_ataque = 0
        self.intervalo_ataque = 1000
        
        mapa = Rect(310.5, 162.5, 1250, 550)
        self.limite_x_min = mapa.x
        self.limite_x_max = mapa.x + mapa.width
        self.limite_y_min = mapa.y
        self.limite_y_max = mapa.y + mapa.height

    def carregar_frames(self, spritesheet, num_frames):
        frames = []
        for i in range(num_frames):
            rect = Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            frame = Surface((self.frame_width, self.frame_height), SRCALPHA)
            frame.blit(spritesheet, (0, 0), rect)
            frame = transform.scale(frame, (self.largura, self.altura))
            frames.append(frame)
        return frames

    def mudar_estado(self, novo_estado):
        if self.estado != novo_estado:
            self.estado = novo_estado
            self.ultima_mudanca_estado = time.get_ticks()
            self.frame_index = 0
            
            if novo_estado == "idle":
                self.frames = self.frames_idle
            elif novo_estado == "perseguindo":
                self.frames = self.frames_run
            elif novo_estado == "atacando":
                self.frames = self.frames_ataque


    def atualizar_animacao(self):
        agora = time.get_ticks()
        if agora - self.ultimo_frame_tempo > self.animation_speed * 1000:
            self.ultimo_frame_tempo = agora
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def teleportar(self): 
        novo_x, novo_y = random.randint(self.limite_x_min,self.limite_x_max),random.randint(self.limite_y_min,self.limite_y_max)
        self.x = novo_x
        self.y = novo_y
        self.rect.topleft = (round(novo_x), round(novo_y))

    def atualizar(self, player_pos, tela):
        if self.esta_atordoado():
            return

        agora = time.get_ticks()
        
        if agora - self.knockback_time < self.knockback_duration:
            return
        
        if self.hp <= 0:
            self.vivo = False
            self.alma_coletada = False
            self.vx = 0
            self.vy = 0
            self.rect.topleft = (self.x, self.y)
            return


        if self.estado == "idle":
            if agora - self.ultima_mudanca_estado > self.tempo_idle:
                self.mudar_estado("perseguindo")
                
        elif self.estado == "perseguindo":
            player_x, player_y = player_pos
            dx = player_x - (self.x + self.largura/2)
            dy = player_y - (self.y + self.altura/2)
            distancia = math.sqrt(dx*dx + dy*dy)
            

            if distancia < self.raio_ataque:
                self.mudar_estado("atacando")
            elif distancia > self.raio_perseguicao:
                self.mudar_estado("idle")
            else:
                if distancia > 0:
                    dx /= distancia
                    dy /= distancia
                
                self.vx = dx * self.velocidade
                self.vy = dy * self.velocidade
                
                self.x += self.vx
                self.y += self.vy
                
                self.x = max(self.limite_x_min, min(self.x, self.limite_x_max - self.largura))
                self.y = max(self.limite_y_min, min(self.y, self.limite_y_max - self.altura))
                
        elif self.estado == "atacando":
            if agora - self.tempo_ultimo_ataque > self.intervalo_ataque:
                player_rect = Rect(player_pos[0], player_pos[1], 64, 64)
                if self.rect.colliderect(player_rect.inflate(self.raio_ataque, self.raio_ataque)):
                    if hasattr(self, "dar_dano") and callable(self.dar_dano):
                        self.dar_dano()
                    self.tempo_ultimo_ataque = agora
            
            if agora - self.ultima_mudanca_estado > self.duracao_ataque:
                self.mudar_estado("teleportando")
                
        elif self.estado == "teleportando":
            if agora - self.ultima_mudanca_estado > self.tempo_cooldown:
                self.teleportar()
                self.mudar_estado("idle")

        # self.rect.topleft = (round(self.x), round(self.y))
        self.atualizar_animacao()

    def desenhar(self, tela, player_pos, offset=(0, 0), mouse_pos=(0, 0)):
        if not self.vivo or not self.frames:
            return
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max, mouse_pos)

        offset_x, offset_y = offset
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y

        if self.anima_hit:
            frame = self.aplicar_efeito_hit(self.frames[self.frame_index])
        else:
            frame = self.frames[self.frame_index]
        tela.blit(frame, (draw_x, draw_y))

        self.desenha_debuffs(tela)
        self.desenhar_dano(tela, offset)


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

        now = time.get_ticks()
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