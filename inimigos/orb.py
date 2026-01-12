from pygame import *
import sys
from pygame.locals import QUIT
import math
from inimigo import Inimigo
from random import uniform, randint
from utils import resource_path 
from projectile_light import ProjectileLight

class Orb(Inimigo):
    def __init__(self, x, y, largura, altura, nome="Orb", hp=100, velocidade=2, dano=25):
        super().__init__(x, y, largura, altura, hp, velocidade, dano)
        self.spritesheet = image.load(resource_path('./assets/Enemies/EyeOrbSprite.png')).convert_alpha()
        self.nome = nome
        self.frame_width = 32
        self.frame_height = 32
        self.total_frames = 16
        self.usar_indices = list(range(0, self.total_frames, 2))
        self.carregar_sprites()

        self.radius = 70
        self.hitbox_arma = (70, 100)
        self.orbital_size = (40, 20)
        self.hitboxArma = (70, 100)

        self.sprite_hit = image.load(resource_path('assets/Enemies/orbTomandoDano.png')).convert_alpha()
        self.frames_hit = []
        self.total_frames_hit = 4
        self.hit_frame_duration = 100
        self.frame_hit_index = 0
        self.time_last_hit_frame = 0
        self.anima_hit = False

        self.tipo_colisao = 'obstaculo'

        self.attack_spritesheet = image.load(resource_path('assets/Enemies/EyeOrbSprite-AttackSheet.png')).convert_alpha()
        self.attack_frames = []
        self.attack_total_frames = 6
        self.attack_frame_index = 0
        self.attack_animando = False
        self.attack_frame_duration = 80  # ms por frame
        self.attack_ultimo_frame = 0
        self.carregar_attack_sprites()

        # Atributos para ataque com projéteis
        self.projeteis = []
        self.ultimo_ataque = 0
        self.cooldown_ataque = 1000  # 2 segundos entre ataques
        self.distancia_ideal = 300  # Distância que o Orb tenta manter do jogador
        self.trail_projetil_max = 5
        self.trail_projetil_fade = 25

    def carregar_attack_sprites(self):
        for i in range(self.attack_total_frames):
            rect = Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            frame = Surface((self.frame_width, self.frame_height), SRCALPHA)
            frame.blit(self.attack_spritesheet, (0, 0), rect)
            frame = transform.scale(frame, (self.largura, self.altura))
            self.attack_frames.append(frame)

    def desenhar(self, tela, player_pos, offset=(0, 0)):
        now = time.get_ticks()
        offset_x, offset_y = offset
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y
        self.desenha_debuffs(tela)
        self.detalhesElite(tela)
        self.desenhar_outline_mouseover(tela, self.hp, self.hp_max)


        if self.anima_hit:
            now = time.get_ticks()
            if now - self.time_last_hit_frame > self.hit_frame_duration:
                self.time_last_hit_frame = now
                self.frame_hit_index += 1
                if self.frame_hit_index >= len(self.frames_hit):
                    self.frame_hit_index = 0
                    self.anima_hit = False
                    return


        if self.attack_animando and self.attack_frames:
            frame = self.attack_frames[self.attack_frame_index]
        elif self.anima_hit:
            frame = self.frames[self.frame_index]  # Obtém o frame normal
            frame = self.aplicar_efeito_hit(frame)  # Aplica o efeito de hit se necessário
            tela.blit(frame, (draw_x, draw_y))
        elif self.frames:
            frame = self.frames[self.frame_index]
        else:
            corpo = Rect(draw_x, draw_y, self.largura, self.altura)
            draw.rect(tela, (255, 0, 0), corpo)
            frame = None

        if frame:
            tela.blit(frame, (draw_x, draw_y))
            if self.congelado:
                frozen_sprite = frame.copy()
                frozen_sprite.fill((165, 242, 255, 100), special_flags=BLEND_MULT)
                tela.blit(frozen_sprite, (draw_x, draw_y))

        # Desenha projéteis
        for projetil in self.projeteis:
            # Desenha o rastro
            for part in projetil["trail"]:
                s = Surface((part["tamanho"], part["tamanho"]), SRCALPHA)
                draw.circle(s, part["cor"],
                            (part["tamanho"] // 2, part["tamanho"] // 2),
                            part["tamanho"] // 2)
                s.set_alpha(part["alpha"])
                tela.blit(s, (part["x"] - part["tamanho"] // 2 + offset_x,
                              part["y"] - part["tamanho"] // 2 + offset_y))

            # Desenha o projétil principal
            s = Surface((projetil["tamanho"], projetil["tamanho"]), SRCALPHA)
            draw.circle(s, projetil["cor"],
                        (projetil["tamanho"] // 2, projetil["tamanho"] // 2),
                        projetil["tamanho"] // 2)
            tela.blit(s, (projetil["x"] - projetil["tamanho"] // 2 + offset_x,
                          projetil["y"] - projetil["tamanho"] // 2 + offset_y))


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

        rot_rect, rot_surf = self.get_hitbox_ataque((player_pos[0] + offset_x, player_pos[1] + offset_y))
        tela.blit(rot_surf, rot_rect)

        self.desenhar_dano(tela, offset)

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

    def get_hitbox_ataque(self, player_pos):
        if not hasattr(self, '_last_angle') or self._last_pos != player_pos:
            player_x, player_y = player_pos
            dx = (player_x + 32) - (self.x + 32)
            dy = (player_y + 32) - (self.y + 32)
            self._last_angle = math.atan2(dy, dx)
            self._last_pos = player_pos

        angulo = self._last_angle

        orb_x = self.x + 32 + math.cos(angulo) * (self.radius + 15)
        orb_y = self.y + 32 + math.sin(angulo) * (self.radius + 15)

        Orb_rect = Rect(0, 0, *(self.orbital_size))
        Orb_rect.center = (orb_x, orb_y)

        orb_surf = Surface(self.hitboxArma, SRCALPHA)
        rot_surf = transform.rotate(orb_surf, -math.degrees(angulo))
        rot_rect = rot_surf.get_rect(center=Orb_rect.center)

        return rot_rect, rot_surf

    def atualizar(self, player_pos, tela):
        if self.esta_atordoado():
            return

        if hasattr(self, 'stun_ativo') and self.stun_ativo:
            self.stun_ativo = False
        now = time.get_ticks()

         # Atualiza projéteis
        for projetil in self.projeteis[:]:
            # Adiciona partículas ao rastro
            if len(projetil["trail"]) < self.trail_projetil_max or uniform(0, 1) < 0.4:
                projetil["trail"].append({
                    "x": projetil["x"],
                    "y": projetil["y"],
                    "alpha": randint(150, 200),
                    "cor": (255, 100 + randint(0, 50), 100 + randint(0, 50)),
                    "tamanho": randint(10, 15),
                    "lifetime": randint(200, 255)
                })

            # Atualiza partículas existentes
            for part in projetil["trail"][:]:
                part["alpha"] = max(0, part["alpha"] - self.trail_projetil_fade)
                if part["alpha"] <= 0:
                    projetil["trail"].remove(part)

            # Move o projétil
            projetil["x"] += projetil["vx"]
            projetil["y"] += projetil["vy"]
            projetil["lifetime"] -= 1

            # Remove se expirar
            if projetil["lifetime"] <= 0:
                self.projeteis.remove(projetil)

        if now - self.knockback_time < self.knockback_duration:
            return
        else:
            self.knockback_x = 0
            self.knockback_y = 0
            self.set_velocidade_x(0)
            self.set_velocidade_y(0)

        self.old_x = self.x
        self.old_y = self.y

        if self.hp <= 0:
            self.vivo = False
            self.alma_coletada = False
            self.vx = 0
            self.vy = 0
            self.rect.topleft = (self.x, self.y)
            return

        player_x, player_y = player_pos
        self.vx = 0
        self.vy = 0

        # Calcula distância até o jogador
        distancia = math.sqrt((player_x - self.x) ** 2 + (player_y - self.y) ** 2)

        # Comportamento de movimento
        if distancia > self.distancia_ideal + 50:
            # Se estiver muito longe, se aproxima
            self.vx = self.velocidade if player_x > self.x else -self.velocidade
            self.vy = self.velocidade if player_y > self.y else -self.velocidade
        elif distancia < self.distancia_ideal - 50:
            # Se estiver muito perto, se afasta
            self.vx = -self.velocidade if player_x > self.x else self.velocidade
            self.vy = -self.velocidade if player_y > self.y else self.velocidade
        else:
            # Se estiver na distância ideal, fica parado e atira
            if now - self.ultimo_ataque > self.cooldown_ataque:
                self.atirar_projetil(player_pos)
                self.ultimo_ataque = now

        # Atualiza posição usando o sistema de colisão
        # (O sistema de colisão já está configurado em colisao.py)
        # Apenas defina a velocidade e a colisão será tratada automaticamente
        self.set_velocidade_x(self.vx)
        self.set_velocidade_y(self.vy)

        if self.attack_animando:
            now = time.get_ticks()
            if now - self.attack_ultimo_frame >= self.attack_frame_duration:
                self.attack_frame_index += 1
                self.attack_ultimo_frame = now
                if self.attack_frame_index >= len(self.attack_frames):
                    self.attack_animando = False

        self.atualizar_animacao()

        if hasattr(self, 'veneno_ativo') and self.veneno_ativo:
            if now >= self.veneno_proximo_tick and self.veneno_ticks > 0:
                self.hp -= self.veneno_dano_por_tick
                self.veneno_ticks -= 1
                self.veneno_proximo_tick = now + self.veneno_intervalo
                self.anima_hit = True
                self.time_last_hit_frame = now
            if self.veneno_ticks <= 0:
                self.veneno_ativo = False

    def carregar_hit_sprites(self):
        for i in range(self.total_frames_hit):
            rect = Rect(i * self.frame_width, 0, self.frame_width, self.frame_height)
            frame = Surface((self.frame_width, self.frame_height), SRCALPHA)
            frame.blit(self.sprite_hit, (0, 0), rect)
            frame = transform.scale(frame, (self.largura, self.altura))
            self.frames_hit.append(frame)

    def atirar_projetil(self, player_pos):
        """Cria um novo projétil direcionado ao jogador"""
        player_x = player_pos[0] + 32
        player_y = player_pos[1] + 50
        angle = math.atan2(player_y - (self.y + self.altura / 2),
                           player_x - (self.x + self.largura / 2))

        projetil = {
            "x": self.x + self.largura / 2,
            "y": self.y + self.altura / 2,
            "vx": math.cos(angle) * 12,  # Velocidade aumentada
            "vy": math.sin(angle) * 12,  # Velocidade aumentada
            "dano": self.dano,
            "lifetime": 1000,  # 1 segundo de vida
            "raio_hitbox": 10,
            "cor": (255, 100, 100),  # Vermelho claro
            "tamanho": 20,
            "trail": [],  # Partículas de rastro
            "luz": ProjectileLight(
                    color=(255, 50, 50),
                    radius=70,
                    intensity=255,
                    steps=16
                )
        }
        self.attack_animando = True
        self.attack_frame_index = 0
        self.attack_ultimo_frame = time.get_ticks()
        self.projeteis.append(projetil)