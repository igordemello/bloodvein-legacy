from pygame import *
import sys
from pygame.locals import QUIT
import math
from random import randint
from modificadores_inimigos import *
from screen_shake import screen_shaker
from pygame.mask import from_surface as mask_from_surface
from utils import resource_path 
class Inimigo:
    def __init__(self, x, y, largura, altura, hp, velocidade=2, dano=0):
        self.alma_coletada = None
        self.loot_coletado = None
        self.pocao_coletada = None
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.velocidade = velocidade

        self.particulas_dano = []

        self.ultimo_dano_tempo = 0
        self.fonte_dano = font.Font(resource_path('assets/Fontes/KiwiSoda.ttf'), 20)

        self.knockback_x = 0
        self.knockback_y = 0
        self.knockback_time = 0
        self.knockback_duration = 200

        self.old_x = x
        self.old_y = y

        self.hp = hp
        self.hp_max = hp
        self.modificadorDanoRecebido = 1
        self.vivo = True
        self.dano = dano
        self.ultimo_dano_critico = False
        self.congelado = False

        self.pode_congelar = False
        self.pode_sangramento = False
        self.pode_envenenar = False
        self.pode_critar = False
        self.pode_enfraquecer = False

        self.spritesheet = None
        self.frame_width = 32
        self.frame_height = 32
        self.total_frames = 1
        self.usar_indices = [0]
        self.frames = []
        self.frame_index = 0
        self.frame_time = 0
        self.animation_speed = 0.10

        self.vy = 0
        self.vx = 0
        self.dx = 0
        self.dy = 0

        self.rect = self.get_hitbox()

        self.ultimo_dano = 0
        self.ultimo_dano_tempo = 0
        self.ultimo_dano_critico = False

        # Adicionando atributos para animação de hit
        self.anima_hit = False
        self.hit_frame_duration = 500  # ms
        self.time_last_hit_frame = 0
        self.hit_alpha = 200  # Transparência do efeito de hit (0-255)
        self.hit_color = (255, 0, 0)  # Cor vermelha para o efeito de hit

    def tomar_dano(self, valor, critico=False):
        if getattr(self, 'invulneravel', False):
            return
        self.hp -= valor
        self.anima_hit = True
        self.time_last_hit_frame = time.get_ticks()

        # Atributos para o texto flutuante
        self.ultimo_dano = valor
        self.ultimo_dano_tempo = time.get_ticks()
        self.ultimo_dano_critico = critico  # Se o dano foi crítico

    def aplicar_efeito_hit(self, frame):
        """Aplica um efeito vermelho temporário ao frame quando o inimigo leva dano"""
        if self.anima_hit:
            now = time.get_ticks()
            if now - self.time_last_hit_frame > self.hit_frame_duration:
                self.anima_hit = False
                return frame

            hit_frame = frame.copy()
            overlay = Surface((frame.get_width(), frame.get_height()), SRCALPHA)
            overlay.fill((255, 50, 50, 180))  # Vermelho com alta opacidade (180/255)
            hit_frame.blit(overlay, (0, 0), special_flags=BLEND_MULT)
            return hit_frame
        return frame

    def get_velocidade(self):
        return (self.vx, self.vy)

    def set_velocidade_x(self, vx):
        self.vx = vx

    def set_velocidade_y(self, vy):
        self.vy = vy

    def mover_se(self, pode_x, pode_y, dx, dy):
        if pode_x:
            self.rect.x += dx
        if pode_y:
            self.rect.y += dy

        self.x, self.y = self.rect.topleft

    def carregar_sprites(self):
        if self.spritesheet:
            self.frames = [self.get_frame(i) for i in self.usar_indices]

    def get_frame(self, index):
        rect = Rect(index * self.frame_width, 0, self.frame_width, self.frame_height)
        frame = Surface((self.frame_width, self.frame_height), SRCALPHA)
        frame.blit(self.spritesheet, (0, 0), rect)
        return transform.scale(frame, (self.largura, self.altura))

    def atualizar_animacao(self):
        self.frame_time += self.animation_speed
        if self.frame_time >= 1:
            self.frame_time = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def aplicar_knockback(self, direcao_x, direcao_y, intensidade):
        angulo = math.atan2(direcao_y, direcao_x)
        self.knockback_x = math.cos(angulo) * intensidade
        self.knockback_y = math.sin(angulo) * intensidade
        self.knockback_time = time.get_ticks()

        self.set_velocidade_x(self.knockback_x)
        self.set_velocidade_y(self.knockback_y)

    def envenenar(self, duracao_em_segundos, dano_total):
        self.veneno_dano_por_tick = dano_total // 2
        self.veneno_ticks = 5
        self.veneno_intervalo = (duracao_em_segundos * 1000) // 5
        self.veneno_proximo_tick = time.get_ticks() + self.veneno_intervalo
        self.veneno_ativo = True

    def stunar(self, duracao_em_segundos):
        if self.hp <= 0:
            return
        self.stun_inicio = time.get_ticks()
        self.stun_duracao = duracao_em_segundos * 1000
        self.stun_ativo = True

        self.vx = 0
        self.vy = 0

    def esta_atordoado(self):
        if not hasattr(self, 'stun_ativo') or not self.stun_ativo:
            return False
        return time.get_ticks() - self.stun_inicio < self.stun_duracao

    def get_hitbox(self):
        return Rect(self.x, self.y, self.largura, self.altura)

    def aplicar_modificadores(self, elite=False):
        gerenciador = GerenciadorModificadores()
        gerenciador.aplicar_modificadores(self, elite)
        if elite==True:
            self.elite = True

    def desenhar_outline_mouseover(self, tela, hp, hpMax):
        mouse_pos = mouse.get_pos()

        if not hasattr(self, 'tempo_mouseover'):
            self.tempo_mouseover = 0

        if self.rect.collidepoint(mouse_pos):
            vida_maxima = getattr(self, "hp_max", 100)
            largura_barra = 500
            porcentagem = max(0, min(self.hp / vida_maxima, 1))
            largura_hp = porcentagem * largura_barra

            barra_x = 980 - (largura_barra / 2)
            barra_y = 0

            self.tempo_mouseover = time.get_ticks()
            if not self.frames:
                return

            try:
                sprite = self.frames[self.frame_index]
                mask = mask_from_surface(sprite)
            except:
                self.frame_index = 0
                sprite = self.frames[self.frame_index]
                mask = mask_from_surface(sprite)

            outline_size = 1
            outline_surf = Surface(
                (sprite.get_width() + 2 * outline_size, sprite.get_height() + 2 * outline_size), SRCALPHA)

            outline_mask = mask.to_surface(setcolor=(255, 0, 0), unsetcolor=(0, 0, 0, 0))

            for dx in range(-outline_size, outline_size + 1):
                for dy in range(-outline_size, outline_size + 1):
                    if dx == 0 and dy == 0:
                        continue
                    outline_surf.blit(outline_mask, (dx + outline_size, dy + outline_size))

            outline_pos = (self.rect.x - outline_size, self.rect.y - outline_size)
            tela.blit(outline_surf, outline_pos)

        if time.get_ticks() - self.tempo_mouseover < 3000:
            vida_maxima = getattr(self, "hp_max", 100)
            largura_barra = 500
            porcentagem = max(0, min(self.hp / vida_maxima, 1))
            largura_hp = porcentagem * largura_barra

            barra_x = 980 - (largura_barra / 2)
            barra_y = 0

            # Desenha a barra de vida
            draw.rect(tela, (10, 10, 10), (barra_x - 20, barra_y + 30, largura_barra, 50))
            draw.rect(tela, (150, 0, 0), (barra_x - 20, barra_y + 30, largura_hp, 50))
            if hasattr(self,'ehboss'):
                draw.rect(tela, (255, 200, 0), (barra_x - 20, barra_y + 30, largura_barra, 50), 1)
            else:
                draw.rect(tela, (255, 255, 255), (barra_x - 20, barra_y + 30, largura_barra, 50), 1)

            fonte = font.Font(resource_path('assets/Fontes/alagard.ttf'), 24)
            texto = fonte.render(str(self.nome), True, (255, 255, 255))
            texto_rect = texto.get_rect(center=(barra_x - 20 + largura_barra / 2, barra_y + 30 + 25))
            tela.blit(texto, texto_rect)





    def desenhar_dano(self, tela, offset=(0, 0)):
        """Desenha o valor do último dano recebido acima do inimigo."""
        if not hasattr(self, 'ultimo_dano') or time.get_ticks() - self.ultimo_dano_tempo >= 400:
            return

        offset_x, offset_y = offset
        draw_x = self.x + offset_x + self.largura / 2
        draw_y = self.y + offset_y - 5

        if getattr(self, 'ultimo_dano_critico', False):
            cor = (255, 215, 0)
            tamanho_fonte = 28
            texto_sufixo = "!"
        else:
            cor = (253, 246, 245)
            tamanho_fonte = 24
            texto_sufixo = ""

        fonte = font.Font(resource_path('assets/Fontes/KiwiSoda.ttf'), tamanho_fonte)
        texto_str = f"{self.ultimo_dano:.1f}{texto_sufixo}"

        offset_y_text = (time.get_ticks() - self.ultimo_dano_tempo) / 4
        pos_y = draw_y - offset_y_text

        outline_color = (0, 0, 0)
        outline_size = 1
        for dx in [-outline_size, 0, outline_size]:
            for dy in [-outline_size, 0, outline_size]:
                if dx == 0 and dy == 0:
                    continue
                outline_text = fonte.render(texto_str, True, outline_color)
                tela.blit(outline_text, (draw_x - outline_text.get_width() / 2 + dx, pos_y + dy))

        texto = fonte.render(texto_str, True, cor)
        tela.blit(texto, (draw_x - texto.get_width() / 2, pos_y))

    def desenha_debuffs(self, tela):
        # Posição abaixo do sprite do inimigo (ajuste os valores conforme necessário)
        icon_y = self.y + self.altura + 10  # 10 pixels abaixo do sprite
        icon_x = self.x + 20+self.largura // 2 - 60  # Centralizado horizontalmente (ajuste conforme necessário)
        icon_spacing = 40  # Espaço entre ícones

        # Ícone de veneno se estiver envenenado
        if hasattr(self, 'veneno_ativo') and self.veneno_ativo:
            try:
                veneno_img = image.load(
                    resource_path('assets/Efeitos_Atributos_Classes/veneno.png')).convert_alpha()
                veneno_img = transform.scale(veneno_img, (16, 16))
                tela.blit(veneno_img, (icon_x, icon_y))
                icon_x += icon_spacing  # Move para a próxima posição
            except:
                pass  # Caso a imagem não carregue, não faz nada

        # Ícone de stun se estiver atordoado
        if hasattr(self, 'stun_ativo') and self.stun_ativo:
            try:
                stun_img = image.load(resource_path('assets/Efeitos_Atributos_Classes/stun.png')).convert_alpha()
                stun_img = transform.scale(stun_img, (16, 16))
                tela.blit(stun_img, (icon_x, icon_y))
                icon_x += icon_spacing  # Move para a próxima posição
            except:
                pass  # Caso a imagem não carregue, não faz nada

        # Ícone de congelado se estiver congelado
        if hasattr(self, 'congelado') and self.congelado:
            try:
                frozen_img = image.load(resource_path('assets/Efeitos_Atributos_Classes/congela1.png')).convert_alpha()
                frozen_img = transform.scale(frozen_img, (16, 16))
                tela.blit(frozen_img, (icon_x, icon_y))
            except:
                pass  # Caso a imagem não carregue, não faz nada
        if hasattr(self, 'sangrando') and self.sangrando:
            try:
                blood_img = image.load(resource_path('assets/Efeitos_Atributos_Classes/bleed.png')).convert_alpha()
                blood_img = transform.scale(blood_img, (16, 16))
                tela.blit(blood_img, (icon_x, icon_y))
            except:
                pass  # Caso a imagem não carregue, não faz nada

    def detalhesElite(self, tela):
        if not hasattr(self, "elite"):
            return

        if not self.frames:
            return

        # 🔒 CLAMP ABSOLUTO (OBRIGATÓRIO)
        if self.frame_index < 0:
            self.frame_index = 0
        elif self.frame_index >= len(self.frames):
            self.frame_index = len(self.frames) - 1

        sprite = self.frames[self.frame_index]
        mask = mask_from_surface(sprite)

        outline_size = 3
        outline_surf = Surface(
            (sprite.get_width() + 2 * outline_size, sprite.get_height() + 2 * outline_size),
            SRCALPHA
        )

        outline_mask = mask.to_surface(
            setcolor=(255, 200, 0, 20),
            unsetcolor=(0, 0, 0, 0)
        )

        for dx in range(-outline_size, outline_size + 1):
            for dy in range(-outline_size, outline_size + 1):
                if dx == 0 and dy == 0:
                    continue
                outline_surf.blit(outline_mask, (dx + outline_size, dy + outline_size))

        outline_pos = (self.rect.x - outline_size, self.rect.y - outline_size)
        tela.blit(outline_surf, outline_pos)