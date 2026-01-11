import time

from pygame import *
import sys
from pygame.locals import QUIT
import math
from inimigo import Inimigo
import random
from utils import resource_path 

class Furacao(Inimigo):
    def __init__(self, x, y, largura, altura, hp, nome="Furacao",velocidade=4, dano=25):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        
        # Estados do inimigo
        self.estado = "idle"  # Pode ser "idle" ou "ataque"
        self.ultima_mudanca_estado = time.get_ticks()
        self.cooldown_idle = 2000  # 3 segundos em idle
        self.duracao_ataque = 5000  # 5 segundos em ataque

        self.nome = nome
        
        # Controle de velocidade progressiva
        self.velocidade_base = velocidade
        self.velocidade_atual = 0
        self.velocidade_max = 10
        self.aceleracao = 0.1
        self.desaceleracao = 0.08
        
        # Spritesheets com dimensões específicas
        self.spritesheet_idle = image.load(resource_path('./assets/Enemies/furacão_idle.png')).convert_alpha()
        self.spritesheet_ataque = image.load(resource_path('./assets/Enemies/furação_ataque.png')).convert_alpha()
        self.spritesheet = self.spritesheet_idle  # Começa com idle

        # Configuração de animação
        self.frame_width = 32
        self.frame_height = 38  # Altura ajustada
        
        # Configurações específicas para cada estado
        self.idle_frames = 4
        self.ataque_frames = 7
        self.animation_speed = 0.15
        
        # Carrega os frames iniciais (idle)
        self.usar_indices = list(range(self.idle_frames))
        self.carregar_sprites()
        self.frame_index = 0

        # Configurações específicas do Furacão
        self.tipo_colisao = 'voador'
        self.dano_area = self.dano
        self.raio_dano = 60
        self.tempo_ultimo_dano = 0
        self.intervalo_dano = 1000

        # Configurações de movimento
        self.direcao = self.gerar_direcao()
        self.ultimo_frame = time.get_ticks()

        # Limites do mapa
        mapa = Rect(310.5,162.5,1250,550)
        self.limite_x_min = mapa.x
        self.limite_x_max = mapa.x + mapa.width
        self.limite_y_min = mapa.y
        self.limite_y_max = mapa.y + mapa.height

    def gerar_direcao(self):
        """Gera uma direção aleatória normalizada"""
        angulo = random.uniform(0, 2 * math.pi)
        return [math.cos(angulo), math.sin(angulo)]

    def carregar_sprites(self):
        """Carrega os frames de animação da spritesheet atual"""
        if self.spritesheet:
            self.frames = [self.get_frame(i) for i in self.usar_indices]
            if not self.frames:  # Se não carregou frames, cria um fallback
                self.frames = [Surface((self.largura, self.altura), SRCALPHA)]

    def mudar_estado(self, novo_estado):
        """Muda o estado do inimigo entre idle e ataque"""
        if self.estado != novo_estado:
            self.estado = novo_estado
            self.ultima_mudanca_estado = time.get_ticks()
            self.frame_index = 0  # Reseta o frame index
            
            # Configura a animação conforme o estado
            if novo_estado == "ataque":
                self.spritesheet = self.spritesheet_ataque
                self.usar_indices = list(range(self.ataque_frames))
                self.velocidade_atual = self.velocidade_base * 0.5
                self.direcao = self.gerar_direcao()
            else:
                self.spritesheet = self.spritesheet_idle
                self.usar_indices = list(range(self.idle_frames))
                self.velocidade_atual = 0
            
            self.carregar_sprites()

    def atualizar_animacao(self):
        """Atualiza a animação do inimigo com comportamentos diferentes por estado"""
        agora = time.get_ticks()
        if agora - self.ultimo_frame > self.animation_speed * 1000:
            self.ultimo_frame = agora
            
            if self.estado == "idle":
                # Animação idle (cicla normalmente)
                self.frame_index = (self.frame_index + 1) % len(self.frames)
            elif self.estado == "ataque":
                # Animação ataque (não volta para o primeiro frame)
                if self.frame_index < len(self.frames) - 1:
                    self.frame_index += 1

    def atualizar(self, player_pos, tela):
        if self.esta_atordoado():
            return

        if hasattr(self, 'stun_ativo') and self.stun_ativo:
            self.stun_ativo = False
        now = time.get_ticks()
        
        # Verifica se precisa mudar de estado
        if self.estado == "idle" and now - self.ultima_mudanca_estado > self.cooldown_idle:
            self.mudar_estado("ataque")
        elif self.estado == "ataque" and now - self.ultima_mudanca_estado > self.duracao_ataque:
            self.mudar_estado("idle")

        # Knockback - não se move durante knockback
        if now - self.knockback_time < self.knockback_duration:
            return
        
        # Inimigo morrendo
        if self.hp <= 0:
            self.vivo = False
            self.alma_coletada = False
            self.vx = 0
            self.vy = 0
            self.rect.topleft = (self.x, self.y)
            return

        # Controle de velocidade durante o ataque
        if self.estado == "ataque":
            tempo_decorrido = now - self.ultima_mudanca_estado
            
            # Fases do ataque:
            # 0-30%: aceleração
            # 30-70%: velocidade máxima
            # 70-100%: desaceleração
            if tempo_decorrido < self.duracao_ataque * 0.3:
                self.velocidade_atual = min(
                    self.velocidade_atual + self.aceleracao,
                    self.velocidade_max
                )
            elif tempo_decorrido < self.duracao_ataque * 0.7:
                self.velocidade_atual = self.velocidade_max
            else:
                self.velocidade_atual = max(
                    self.velocidade_atual - self.desaceleracao,
                    self.velocidade_base * 0.5
                )

            # Movimento
            self.vx = self.direcao[0] * self.velocidade_atual
            self.vy = self.direcao[1] * self.velocidade_atual

            self.x += self.vx
            self.y += self.vy

            # Rebate nas paredes
            rebateu = False
            if self.x < self.limite_x_min or self.x > self.limite_x_max:
                self.direcao[0] *= -1
                rebateu = True
            if self.y < self.limite_y_min or self.y > self.limite_y_max:
                self.direcao[1] *= -1
                rebateu = True
                
            if rebateu:
                # Aumenta um pouco a velocidade ao rebater
                self.velocidade_atual = min(
                    self.velocidade_atual * 1.1,
                    self.velocidade_max
                )
                self.vx = self.direcao[0] * self.velocidade_atual
                self.vy = self.direcao[1] * self.velocidade_atual

            # Mantém dentro dos limites
            self.x = max(self.limite_x_min, min(self.x, self.limite_x_max))
            self.y = max(self.limite_y_min, min(self.y, self.limite_y_max))
        
        # Atualiza a posição do retângulo de colisão
        self.rect.topleft = (round(self.x), round(self.y))

        # Dano por proximidade (só durante o ataque)
        if self.estado == "ataque":
            player_rect = Rect(player_pos[0], player_pos[1], 64, 64)
            if self.rect.colliderect(player_rect.inflate(self.raio_dano, self.raio_dano)):
                if now - self.tempo_ultimo_dano > self.intervalo_dano:
                    if hasattr(self, "dar_dano") and callable(self.dar_dano):
                        self.dar_dano()
                    self.tempo_ultimo_dano = now 

        self.atualizar_animacao()

    def desenhar(self, tela, player_pos, offset=(0, 0)):
        if not self.vivo or not self.frames:
            return

        self.desenha_debuffs(tela)
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max)


        offset_x, offset_y = offset
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y

        # Desenha o frame atual
        #HIT VERMELHO COLOCAR ISSO EM TODOS OS INIMIGOS NO METODO DESENHAR DE CADA UM
        if self.anima_hit:
            frame = self.aplicar_efeito_hit(self.frames[min(self.frame_index, len(self.frames) - 1)])
        else:
            frame = self.frames[min(self.frame_index, len(self.frames) - 1)]
        tela.blit(frame, (draw_x, draw_y))

        self.desenhar_dano(tela, offset)

        # Desenha a barra de vida se tomou dano recentemente
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
