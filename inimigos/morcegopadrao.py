from pygame import *
import math
from pygame import time
from inimigo import Inimigo
import random
from utils import resource_path 

class MorcegoPadrao(Inimigo):
    def __init__(self, x, y, largura=64, altura=64, hp=80, velocidade=2, dano=20):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)

        self.sprites_idle = image.load(resource_path('./assets/Enemies/morcego_idle.png')).convert_alpha()
        self.sprites_voando = image.load(resource_path('./assets/Enemies/morcego_correr.png')).convert_alpha()
        self.sprites_ataque = image.load(resource_path('./assets/Enemies/morcego_ataque.png'))

        self.frame_width = 27
        self.frame_height = 36
        self.animation_speed = 0.3

        self.frames_idle = [self.get_frame(self.sprites_idle, i) for i in range(4)]
        self.frames_voando = [self.get_frame(self.sprites_voando, i) for i in range(6)]
        self.frames_ataque = [self.get_frame(self.sprites_ataque, i) for i in range(5)]
        self.frames = self.frames_idle
        self.estado = 'idle'

        self.raio_ataque = 50
        self.atacando = False
        self.tempo_ataque = 0
        self.duracao_ataque = 400

        self.tipo_colisao = 'voador'
        self.ultimo_objetivo = None
        self.caminho_atual = []
        self.tile_size_scaled = 32 * 3.25
        self.vivo = True

        # Área de movimento do morcego
        self.area_movimento = Rect(280, 160, 1350, 650)

        # Configurações do movimento em zig-zag
        self.direcao = random.choice([-1, 1])
        self.altura_zigzag = random.randint(40, 80)  # Altura do padrão de zig-zag
        self.contador_zigzag = random.randint(0, 100)
        self.velocidade = velocidade * random.uniform(0.8, 1.2)
        self.frequencia_zigzag = random.uniform(0.08, 0.12)
        self.ponto_inicial = (x, y)  # Ponto onde o morcego começa
        self.velocidade_original = velocidade

    def get_frame(self, spritesheet, index):
        rect = Rect(index * self.frame_width, 0, self.frame_width, self.frame_height)
        frame = Surface((self.frame_width, self.frame_height), SRCALPHA)
        frame.blit(spritesheet, (0, 0), rect)
        return transform.scale(frame, (self.largura, self.altura))

    def atualizar(self, player_pos, tela, matriz_colisao, offset_mapa):
        if self.esta_atordoado() or self.hp <= 0:
            self.vivo = False
            self.vx = 0
            self.vy = 0
            return

        if not self.atacando and self.frames == self.frames_ataque:
            self.frames = self.frames_voando
            self.frame_index = 0
            self.frame_time = 0

        # Verificar knockback primeiro
        now = time.get_ticks()
        if now - self.knockback_time < self.knockback_duration:
            # Aplicar knockback (se houver) e retornar
            self.x += self.vx
            self.y += self.vy
            return

        # Movimento em zig-zag dentro da área definida
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

        # Verifica se está atacando o jogador quando perto
        if not self.atacando:
            player_rect = Rect(player_pos[0], player_pos[1], 64, 64)
            if self.rect.colliderect(player_rect.inflate(self.raio_ataque, self.raio_ataque)):
                self.atacando = True
                self.tempo_ataque = now
                if hasattr(self, "dar_dano") and callable(self.dar_dano):
                    self.dar_dano()
        else:
            if now - self.tempo_ataque > self.duracao_ataque:
                self.atacando = False

        self.estado = 'voando'
        self.frames = self.frames_voando
        self.rect.topleft = (round(self.x), round(self.y))

        if not self.atacando:
            player_rect = Rect(player_pos[0], player_pos[1], 64, 64)
            if self.rect.colliderect(player_rect.inflate(self.raio_ataque, self.raio_ataque)):
                self.atacando = True
                self.tempo_ataque = now
                if hasattr(self, "dar_dano") and callable(self.dar_dano):
                    self.dar_dano()

        if self.atacando:
            self.frames = self.frames_ataque  # Muda para frames de ataque

            if now - self.tempo_ataque > self.duracao_ataque:
                self.atacando = False
                self.frames = self.frames_voando  # Volta para frames normais
        else:
            self.frames = self.frames_voando

        if self.atacando and self.frames != self.frames_ataque:
            self.frames = self.frames_ataque
            self.frame_index = 0  # Reseta o índice
            self.frame_time = 0

        self.atualizar_animacao()

    def atualizar_animacao(self):
        self.frame_time += self.animation_speed
        if self.frame_time >= 1:
            self.frame_time = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def desenhar(self, tela, player_pos, offset=(0, 0), mouse_pos=(0, 0)):
        if not self.vivo or len(self.frames) == 0:
            return

        self.desenha_debuffs(tela)
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela,self.hp,self.hp_max, mouse_pos)


        offset_x, offset_y = offset
        draw_x = round(self.x) + offset_x
        draw_y = round(self.y) + offset_y
        # HIT VERMELHO COLOCAR ISSO EM TODOS OS INIMIGOS NO METODO DESENHAR DE CADA UM
        if self.anima_hit:
            self.frame_index = min(self.frame_index, len(self.frames) - 1)
            frame = self.aplicar_efeito_hit(self.frames[self.frame_index])
        else:
            self.frame_index = min(self.frame_index, len(self.frames) - 1)
            frame = self.frames[self.frame_index]
        tela.blit(frame, (draw_x, draw_y))

        self.desenhar_dano(tela, offset)

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

