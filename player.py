from pygame import *
import sys
from pygame.locals import QUIT
import math
from efeito import *
import time as t

from habilidades import GerenciadorHabilidades
from sala import *
from armas import *
from random import *
from sistemaparticulas import *
from screen_shake import screen_shaker
from som import som
from som import GerenciadorDeMusica
from som import musica
from dificuldade import dificuldade_global

class Player():
    def __init__(self, x, y, largura, altura,hud=None, hp=100, st=100, velocidadeMov=2, sprite=resource_path('assets/player/hero.png'), arma=None):
        # animaçõesd
        self.hit_landed = None
        self.animacoes = {
            "baixo": self.carregar_animacao(resource_path('assets/Player/vampira_andando_frente.png')),
            "cima": self.carregar_animacao(resource_path('assets/Player/vampira_andando_tras.png')),
            "D_cima": self.carregar_animacao(resource_path('assets/Player/dash_costas.png')),
            "D_baixo": self.carregar_animacao(resource_path('assets/Player/dash_frente.png')),
            "D_direita": self.carregar_animacao(resource_path('assets/Player/dash _lado.png')),
            "D_esquerda": [transform.flip(img, True, False) for img in
                           self.carregar_animacao(resource_path('assets/Player/dash _lado.png'))],
            "direita": self.carregar_animacao(resource_path('assets/Player/LADOANDAR-Sheet.png')),
            "esquerda": [transform.flip(img, True, False) for img in
                         self.carregar_animacao(resource_path('assets/Player/LADOANDAR-Sheet.png'))],
            "idle": self.carregar_animacao(resource_path('assets/Player/IDLE.png')),
            "idle_costas": self.carregar_animacao(resource_path('assets/Player/IDLE_COSTAS.png')),
            "idle_lado1": self.carregar_animacao(resource_path('assets/Player/IDLE_LADO.png')),
            "idle_lado2": [transform.flip(img, True, False) for img in
                           self.carregar_animacao(resource_path('assets/Player/IDLE_LADO.png'))],
        }

        self.atributos = {
            "forca": 5,  # influencia DANO DA ARMA, DANO DO CRÍTICO
            "destreza": 5,  # influencia VELOCIDADE DE ATAQUE DA ARMA
            "agilidade": 5,  # influencia VELOCIDADE DE MOVIMENTO DO PERSONAGEM
            "vigor": 5,  # influencia VELOCIDADE DO DECAIMENTO
            "resistencia": 5,  # influencia DANO RECEBIDO
            "estamina": 5,  # influencia COOLDOWN DE DASH, GASTO E COOLDOWN STAMINA
            "sorte": 5,  # influencia CHANCE DE CRÍTICO E UM POUCO DE TUDO
        }

        self.pontosHabilidade = 0
        self.habilidades = []
        self.hotkeys = [0,0,0,0]
        self.nevascaAtivada = False
        self.trovaoAtivado = False
        self.venenoDano = 40

        self.lista_mods = ListaMods()

        self.gerenciador_habilidades = GerenciadorHabilidades()
        '''
        self.inventario = [
            LaminaDaNoite("comum", self.lista_mods),
            Chigatana("incomum", self.lista_mods),
            Karambit("incomum", self.lista_mods),
            EspadaDoTita("raro", self.lista_mods),
            MachadoDoInverno("raro", self.lista_mods),
            EspadaEstelar("lendaria", self.lista_mods),
            MarteloSolar("lendaria", self.lista_mods),
            Arco("lendaria", self.lista_mods)
        ]
        for i in self.inventario: i.aplicaModificador()
        '''
        self.inventario = []
        self.nivel = 1
        self.hp = hp
        self.hpMax = hp

        self.pocoesHp = 0
        self.pocoesMp = 0


        self.mpModificador = 1

        self.efeitos = []

        self.corrente_eletrica_ativa = False
        self.trail_eletrico = []  # Lista de retângulos que representam a corrente elétrica
        self.trail_timer = 0  # Timer para remover o trail após 4 segundos
        self.dash_start_pos = None  # Posição inicial do dash

        self.tipo_colisao = 'obstaculo'

        # ARMA
        self.sistemaparticulas = ParticleSystem()
        self.lista_mods = ListaMods()
        self.arma = arma if arma else EspadaEstelar("comum", self.lista_mods)

        self.base_dano = self.arma.dano
        self.base_danoCriticoMod = self.arma.danoCriticoMod
        self.base_velocidade = self.arma.velocidade
        self.base_chanceCritico = self.arma.chanceCritico
        self.base_rate = 0
        self.base_rateSt = 1
        self.base_velocidadeMov = 0.5
        self.base_custoDash = 0
        self.base_modificadorDanoRecebido = 1
        self.base_invencibilidade = 500
        self.base_cooldown_st = 3222.22
        self.base_dash_cooldown_max = 1000
        self.base_dash_duration_max = 150

        self.gameOver = False

        self.animacoes_principais = 'esquerdadireitabaixocima'
        self.anim_direcao = "baixo"
        self.anim_frame = 0
        self.tempo_animacao = 0
        self.tempo_por_frame = 100
        self.frame_atual = self.animacoes[self.anim_direcao][self.anim_frame]
        self.rastros = []

        self.macarronada = 0

        self.telaSangue = image.load(resource_path('assets/UI/sangueTelaDano.png')).convert_alpha()
        self.telaSangue_alpha = 0
        self.telaSangue_surface = None

        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.ultimo_uso = 0
        self.revives = 0
        self.ultimo_dano = 0
        self.foi_atingido = False
        self.tempo_atingido = 0

        self.itens = {}
        # só comentar isso daqui em baixo e volta ao normal:
        #conjunto = ConjuntoItens()
        #itens_iniciais_ids = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        #for item_id in itens_iniciais_ids:
        #    item = conjunto.itens_por_id[item_id]
        #    self.adicionarItem(item)

        self.itemAtivo = None
        #self.itemAtivo = conjunto.itens_por_id[19]
        self.salaAtivoUsado = None
        self.itemAtivoEsgotado = None
        self.mpMaximo = 100
        self.mp = self.mpMaximo
        self.staminaMaximo = 100
        self.stamina = self.staminaMaximo


        self.almas = 0

        self.old_x = x
        self.old_y = y
        self.vx = 0
        self.vy = 0
        self.atrito = 0.92
        self.radius = self.arma.radius - 50
        self.orbital_size = (40, 20)
        self.hitbox_arma = self.arma.range
        self.atacou = False
        self.hits = 0
        self.tempo_ultimo_hit = 0
        self.tempo_max_combo = 2500
        self.dash_cooldown = 0
        self.dash_duration = 0

        self.is_dashing = False
        self.last_dash_time = 0
        self.dash_direcao = None
        self.parado_desde = 0
        self.ativo_ultimo_uso = 0

        self.sword = transform.scale(transform.flip(image.load(self.arma.sprite).convert_alpha(), True, True),
                                     (self.arma.size))
        self.sword_pivot = self.arma.pivot
        self.sword_angle = 0
        self.attacking = False
        self.attack_start_time = 0
        self.attack_direction = 1
        self.attack_progress = 0
        self.base_sword_angle = 0
        self.sword_arc = 210
        self.sword_start_angle = -105

        # Sistema de rastro melhorado
        self.sword_trail_particles = []
        self.trail_max_particles = 50
        self.trail_fade_speed = 15
        self.trail_size_variation = 0
        self.trail_spawn_rate = 1
        self.trail_start_alpha = 130

        self.projetil_trail_particles = []
        self.trail_projetil_max = 5
        self.trail_projetil_fade = 25

        self.last_attack_direction = -1

        self.dano_recebido_tempo = 0

        self.projeteis = []
        self.aoe = None
        self.aoeVeneno = None
        self.claraoDano = None
        self.nuvemAtivado = False
        self.claraoAtivado = False
        self.hits_projetil = 0
        self.tempo_ultimo_hit_projetil = 0

        self.cooldown_ataque_base = self.arma.cooldown
        self.ultimo_ataque = 0
        self.sprite_dano = self.frame_atual.copy()
        self.sprite_dano.fill((255, 255, 255), special_flags=BLEND_RGB_ADD)

        clock = time.Clock()
        self.dt = clock.get_time()
        self.player_img = self.frame_atual
        self.player_rect = Rect(self.x, self.y, 60, 120)
        self.dx = 0
        self.dy = 0

        self.travado = False

        self.proibir_dash_ate = 0
        self.som_dash = True

        self.trait = None

        self.velocidade_base = self.base_velocidadeMov
        self.em_espinhos = False
        self.tempo_ultimo_dano_espinhos = 0
        self.cooldown_dano_espinhos = 1000

        self.velocidadeMov = self.base_velocidadeMov

        self.hud = hud

        self.duracao_lentidao = 0
        self.lentidao_ativa = False
        self.tempo_lentidao = 0
        self.velocidadeOld = self.velocidadeMov

        self.envenenado = False
        self.tempo_veneno = 0
        self.duracao_veneno = 0
        self.intervalo_veneno = 1000  # tempo entre cada dano em ms
        self.proximo_tick_veneno = 0

    def set_hud(self, hud):
        self.hud = hud

    def carregar_animacao(self, caminho):
        frame_largura = 32
        frame_altura = 48
        escala = 3
        folha = transform.scale(image.load(caminho).convert_alpha(), (
            image.load(caminho).convert_alpha().get_width() * escala,
            image.load(caminho).convert_alpha().get_height() * escala))
        num_frames = int(folha.get_width() // (frame_largura * escala))

        return [
            folha.subsurface((i * frame_largura * escala, 0, frame_largura * escala, frame_altura * escala))
            for i in range(num_frames)
        ]

    def _dash(self, dt, teclas, direcao):
        current_time = time.get_ticks()
        if current_time < self.proibir_dash_ate:
            return

        if (current_time - self.last_dash_time > self.dash_cooldown_max and not self.is_dashing and teclas[K_SPACE]):
            if self.stamina < self.custoDash:
                self.hud.mensagem_sem_stamina = True
                self.hud.tempo_mensagem_stamina = current_time
                return

            # Verificar se a habilidade Corrente Elétrica está ativa
            self.corrente_eletrica_ativa = "Corrente Elétrica" in self.habilidades

            if self.corrente_eletrica_ativa:
                self.dash_start_pos = (self.x, self.y)  # Guarda posição inicial

            self.last_dash_time = current_time
            self.is_dashing = True
            self.dash_direcao = direcao
            self.dash_duration = 0

        if self.is_dashing:
            if self.corrente_eletrica_ativa:
                # Atualiza o timer do trail
                self.trail_timer += dt
                if self.trail_timer >= 4000:  # 4 segundos
                    if self.trail_eletrico:
                        self.trail_eletrico.pop(0)  # Remove o segmento mais antigo
                    self.trail_timer = 0

        self.ultimo_uso = current_time

    def usarItemAtivo(self, sala_atual: Sala):
        if isinstance(self.itemAtivo, ItemAtivo):
            if hasattr(self, 'itemAtivoEsgotado') and self.itemAtivoEsgotado:
                self.itemAtivoEsgotado.remover_efeitos(self)
            if self.itemAtivo.afetaIni:
                self.itemAtivo.listaInimigos = sala_atual.inimigos
            else:
                self.itemAtivo.player = self

            self.itemAtivo.aplicar_em()
            self.itemAtivo.usos -= 1
            self.salaAtivoUsado = sala_atual

            if self.itemAtivo.usos <= 0:
                self.itemAtivoEsgotado = self.itemAtivo
                self.itemAtivo = None

    def atualizar(self, dt, teclas):
        current_time = time.get_ticks()
        if hasattr(self, 'tempo_descongelar') and current_time >= self.tempo_descongelar:
            self.travado = False
            if hasattr(self, 'tempo_descongelar'):
                del self.tempo_descongelar
        self.fonte_arcana()
        self.escudo()
        # print(f'HP: {self.hp}, Stamina: {self.stamina}, Mana: {self.mp}')

        if self.pocoesMp > 4: self.pocoesMp = 4
        if self.pocoesHp > 4: self.pocoesHp = 4

        if self.travado:
            self.vx = 0
            self.vy = 0
            return

        if not hasattr(self, 'dash_timer'):
            self.dash_timer = 0

        self.dt = dt
        current_time = time.get_ticks()
        self.old_x = self.x
        self.old_y = self.y
        self.x, self.y = self.player_rect.topleft

        speed = self.velocidadeMov * dt
        move_input = False

        if teclas[K_a]:
            self.vx -= speed
            self.anim_direcao = "esquerda"
            move_input = True
        if teclas[K_d]:
            self.vx += speed
            self.anim_direcao = "direita"
            move_input = True
        if teclas[K_w]:
            self.vy -= speed
            self.anim_direcao = "cima"
            move_input = True
        if teclas[K_s]:
            self.vy += speed
            self.anim_direcao = "baixo"
            move_input = True

        self.vx *= self.atrito
        self.vy *= self.atrito

        # Limiar para zerar a velocidade (evita deslize infinito)
        limiar_parada = 2
        if abs(self.vx) < limiar_parada:
            self.vx = 0
        if abs(self.vy) < limiar_parada:
            self.vy = 0

        # Limita a velocidade máxima
        max_vel = self.velocidadeMov * 10
        self.vx = max(-max_vel, min(self.vx, max_vel))
        self.vy = max(-max_vel, min(self.vy, max_vel))

        if teclas[K_d]:
            self._dash(dt, teclas, 'd')
        elif teclas[K_a]:
            self._dash(dt, teclas, 'a')
        elif teclas[K_w]:
            self._dash(dt, teclas, 'w')
        elif teclas[K_s]:
            self._dash(dt, teclas, 's')

        if self.is_dashing:
            if self.som_dash == True:
                som.tocar('dash')
                self.som_dash = False
            self.rastros.append({
                "imagem": self.frame_atual.copy(),
                "pos": self.player_rect.topleft,
                "tempo": 200
            })

            dash_speed = self.velocidadeMov * dt * 2.5
            direcao = self.dash_direcao
            if direcao == 'a':
                self.vx = -dash_speed
                self.anim_direcao = "D_esquerda"
            elif direcao == 'd':
                self.vx = dash_speed
                self.anim_direcao = "D_direita"
            elif direcao == 'w':
                self.vy = -dash_speed
                self.anim_direcao = "D_cima"
            elif direcao == 's':
                self.vy = dash_speed
                self.anim_direcao = "D_baixo"

            self.dash_duration += dt
            if self.dash_duration >= self.dash_duration_max:
                if self.som_dash == False:
                    self.som_dash = True
                self.is_dashing = False
                self.anim_frame = 0

                if self.dash_direcao == 'a':
                    self.anim_direcao = 'esquerda'
                elif self.dash_direcao == 'd':
                    self.anim_direcao = 'direita'
                elif self.dash_direcao == 'w':
                    self.anim_direcao = 'cima'
                elif self.dash_direcao == 's':
                    self.anim_direcao = 'baixo'

        for rastro in self.rastros:
            rastro["tempo"] -= dt
        self.rastros = [r for r in self.rastros if r["tempo"] > 0]

        if self.is_dashing or move_input:
            self.tempo_por_frame = 100
            self.tempo_animacao += dt
            if self.tempo_animacao > self.tempo_por_frame:
                self.tempo_animacao = 0
                self.anim_frame += 1
                if self.anim_frame >= len(
                        self.animacoes[self.anim_direcao]) and self.anim_direcao in self.animacoes_principais:
                    self.anim_frame = 4
        else:
            angulo = self.calcular_angulo(mouse.get_pos())
            angulo_deg = math.degrees(angulo) % 360

            if 45 < angulo_deg <= 135:
                self.anim_direcao = "idle"
            elif 135 < angulo_deg <= 225:
                self.anim_direcao = "idle_lado2"
            elif 225 < angulo_deg <= 315:
                self.anim_direcao = "idle_costas"
            else:
                self.anim_direcao = "idle_lado1"

            self.tempo_animacao += dt
            self.tempo_por_frame = 200
            if self.tempo_animacao > self.tempo_por_frame:
                self.tempo_animacao = 0
                self.anim_frame += 1
                if self.anim_frame >= len(
                        self.animacoes[self.anim_direcao]) and self.anim_direcao in self.animacoes_principais:
                    self.anim_frame = 0

        self.hp -= 0.05 * self.rate

        if current_time - self.last_dash_time >= self.cooldown_st:
            self.stamina += 0.7 * self.rateSt
        if self.stamina > self.staminaMaximo:
            self.stamina = self.staminaMaximo

        if self.is_dashing and self.corrente_eletrica_ativa:
            self.atualizar_trail_eletrico()

            # Atualiza os timers dos trails existentes
        for trail in self.trail_eletrico[:]:
            trail['timer'] -= dt
            if trail['timer'] <= 0:
                self.trail_eletrico.remove(trail)

        if self.hp < 0:
            self.hp = 0
        if self.hp > self.hpMax:
            self.hp = self.hpMax
        if self.mp < 0:
            self.mp = 0
        if self.mp > self.mpMaximo:
            self.mp = self.mpMaximo

        if self.hp == 0:
            if self.revives <= 0:
                self.gameOver = True
                musica.tocar(resource_path("BloodVein SCORE/OST/Game Over.mp3"))
            else:
                self.hp += self.hpMax / 2
                self.revives -= 1

        if self.attacking:
            self.atualizar_ataque(dt)

        if self.anim_direcao in self.animacoes:
            animacao = self.animacoes[self.anim_direcao]
            self.anim_frame %= len(animacao)
            self.frame_atual = animacao[self.anim_frame]
        else:
            self.frame_atual = self.animacoes["baixo"][0]

        self.player_rect = self.get_hitbox()
        self.sistemaparticulas.update(dt)

        if self.hits > 0 and time.get_ticks() - self.tempo_ultimo_hit > self.tempo_max_combo:
            self.hits = 0
            self.arma.comboMult = 1

        if self.hits_projetil > 0 and time.get_ticks() - self.tempo_ultimo_hit_projetil > self.tempo_max_combo:
            self.hits_projetil = 0
            self.arma.comboMult = 1

        for projetil in self.projeteis[:]:
            if len(projetil["trail"]) < self.trail_projetil_max or random() < 0.4:
                projetil["trail"].append({
                    "x": projetil["x"],
                    "y": projetil["y"],
                    "alpha": randint(150, 200),  # Variação de transparência
                    "angle": projetil["angulo"] + randint(-5, 5),  # Pequena variação angular
                    "lifetime": randint(200, 255),  # Variação de tempo de vida
                    "scale": 0.5 + random() * 0.5  # Variação de escala
                })

            for part in projetil["trail"][:]:
                part["alpha"] = max(0, part["alpha"] - self.trail_projetil_fade)
                if part["alpha"] <= 0:
                    projetil["trail"].remove(part)

            projetil["x"] += projetil["vx"] * dt
            projetil["y"] += projetil["vy"] * dt
            projetil["lifetime"] -= dt
            if projetil["lifetime"] <= 0:
                self.projeteis.remove(projetil)
        if move_input:
            for _ in range(1):  # duas partículas
                offset_x = randint(-10, 5)
                offset_y = randint(-5, 5)
                self.sistemaparticulas.add_particle(
                    self.player_rect.centerx + offset_x,
                    self.player_rect.centery + offset_y + 40,  # um pouco mais pra baixo
                    (255, 255, 255),  # cor branca
                    (uniform(-0.05, 0.05), uniform(-0.05, 0.05)),  # leve movimento
                    lifetime=200,  # vida curta (ms)
                    size=3  # tamanho da partícula
                )

        self.atualizar_lentidao()
        self.atualizar_veneno()


    def tratar_eventos(self, eventos):
        for ev in eventos:
            # Libera a paralisia do grito
            if ev.type == USEREVENT + 11:
                self.travado = False

            # Restaura a velocidade após o grito
            elif ev.type == USEREVENT + 12:
                if hasattr(self, 'velocidade_original_grito'):
                    self.velocidadeMov = self.velocidade_original_grito
                    del self.velocidade_original_grito



    def atualizar_ataque(self, dt):
        current_time = time.get_ticks()
        attack_duration = 300 / self.arma.velocidade
        self.attack_progress = min(1.0, (current_time - self.attack_start_time) / attack_duration)

        if self.attack_progress >= 1.0:
            self.attacking = False
            self.sword_trail_particles = []
            return

        angle = self.calcular_angulo(mouse.get_pos())
        centro_jogador = (self.player_rect.centerx, self.player_rect.centery)
        base_x = centro_jogador[0] + math.cos(angle) * (self.radius - 5)
        base_y = centro_jogador[1] + math.sin(angle) * (self.radius - 5)

        # Adiciona nova partícula ao rastro
        if (len(self.sword_trail_particles) < self.trail_max_particles and
                random() < self.trail_spawn_rate):
            size_variation = 1 + (random() - 0.5) * self.trail_size_variation
            self.sword_trail_particles.append({
                'x': base_x,
                'y': base_y,
                'angle': self.sword_angle,
                'size': size_variation,
                'alpha': self.trail_start_alpha,  # Usando o valor definido no init
                'lifetime': 255,
                'color_mod': (min(255, 200 + randint(0, 55)),
                              min(255, 200 + randint(0, 55)),
                              min(255, 200 + randint(0, 55)))
            })

        for particle in self.sword_trail_particles[:]:
            particle['alpha'] = max(0, particle['alpha'] - self.trail_fade_speed)
            particle['lifetime'] -= self.trail_fade_speed
            if particle['lifetime'] <= 0:
                self.sword_trail_particles.remove(particle)

        swing_angle = self.sword_start_angle + self.sword_arc * self.attack_progress
        self.sword_angle = self.base_sword_angle + swing_angle * self.attack_direction

    def adicionarItem(self, item):
        if isinstance(item, Item):
            item.aplicar_em(self)
            if item not in self.itens:
                self.itens[item] = 1
            else:
                pass
        else:
            self.itemAtivo = item

    def criar_projetil(self, mouse_pos, dano, cor, sprite=None, tamanho=10, velocidade=0.8, lifetime=1000,
                       angulo_personalizado=None):
        angle = self.calcular_angulo(mouse_pos)
        centro_jogador = (self.player_rect.centerx, self.player_rect.centery)

        if angulo_personalizado is not None:
            angle = angulo_personalizado

        if sprite:
            distancia = self.radius + sprite.get_width() // 2
            sprite_original = sprite
        else:
            distancia = self.radius + tamanho // 2
            sprite_original = None

        start_x = centro_jogador[0] + math.cos(angle) * distancia
        start_y = centro_jogador[1] + math.sin(angle) * distancia

        projetil = {
            "x": start_x,
            "y": start_y,
            "vx": math.cos(angle) * velocidade,
            "vy": math.sin(angle) * velocidade,
            "dano": dano,
            "lifetime": lifetime,
            "raio_hitbox": tamanho // 2 if not sprite else max(sprite.get_width(), sprite.get_height()) // 2,
            "trail": [],  # Partículas de rastro para este projétil
            "sprite_original": sprite_original,
            "angulo": math.degrees(angle) - 90  # Ângulo em graus para rotação
        }

        if sprite:
            projetil["sprite"] = sprite
        else:
            projetil["cor"] = cor
            projetil["tamanho"] = tamanho

        self.projeteis.append(projetil)

    def criarAOE(self, mouse_pos, tamanho):
        sala = Rect(325, 325, 1275, 600)
        if not sala.collidepoint(mouse_pos):
            return None
        mouse_x, mouse_y = mouse_pos
        rect = Rect(0, 0, tamanho, tamanho)
        rect.center = (mouse_x, mouse_y)
        s = Surface((tamanho, tamanho), SRCALPHA)
        tempoCriacao = time.get_ticks()
        return s, rect, tamanho, tempoCriacao

    def calcular_angulo(self, mouse_pos):
        mouse_x, mouse_y = mouse_pos
        dx = mouse_x - (self.x + 32)
        dy = mouse_y - (self.y + 32)
        return math.atan2(dy, dx)

    def get_rotated_rect_ataque(self, mouse_pos):
        angle = self.calcular_angulo(mouse_pos)
        centro_jogador = (self.player_rect.centerx, self.player_rect.centery)
        base_x = centro_jogador[0] + math.cos(angle) * (self.radius + 15)
        base_y = centro_jogador[1] + math.sin(angle) * (self.radius + 15)

        hitbox_surf = Surface(self.hitbox_arma, SRCALPHA)
        draw.rect(hitbox_surf, (255, 0, 0), hitbox_surf.get_rect(), width=1)

        # Rotação idêntica à da espada
        temp_surface = Surface((hitbox_surf.get_width() * 2, hitbox_surf.get_height() * 2), SRCALPHA)
        temp_surface.blit(hitbox_surf, (temp_surface.get_width() // 2 - self.sword_pivot[0],
                                        temp_surface.get_height() // 2 - self.sword_pivot[1]))

        rotated_hitbox = transform.rotate(temp_surface, -self.sword_angle)
        rotated_rect = rotated_hitbox.get_rect(center=(base_x, base_y))

        return rotated_hitbox, rotated_rect

    def desenhar(self, tela, mouse_pos):
        angle = self.calcular_angulo(mouse_pos)
        centro_jogador = (self.player_rect.centerx, self.player_rect.centery)
        base_x = centro_jogador[0] + math.cos(angle) * (self.radius - 5)
        base_y = centro_jogador[1] + math.sin(angle) * (self.radius - 5)

        if self.aoe is not None:
            s, rectAoe, tamanho, tempoCriacao = self.aoe
            tempo_atual = time.get_ticks()

            if tempo_atual - tempoCriacao < 500:
                s.fill((0, 0, 0, 0))
                draw.rect(s, (255, 228, 76, 50), s.get_rect(), border_radius=int(tamanho / 2))
                tela.blit(s, rectAoe.topleft)
            else:
                self.aoe = None
                self.travado = False

                if hasattr(self, 'claraoAtivado') and self.claraoAtivado:
                    self.claraoAtivado = False
                    self.claraoDano = None
                    if hasattr(self, 'inimigos_atingidos_este_clarao'):
                        del self.inimigos_atingidos_este_clarao
        if self.aoeVeneno is not None:
            s, rectAoe, tamanho, tempoCriacao = self.aoeVeneno
            tempo_atual = time.get_ticks()

            rectAoe.center = self.player_rect.center

            if tempo_atual - tempoCriacao < 5000:
                s.fill((0, 0, 0, 0))
                draw.rect(s, (0, 228, 0, 50), s.get_rect(), border_radius=int(tamanho / 2))
                tela.blit(s, rectAoe.topleft)
            else:
                self.aoeVeneno = None
                self.nuvemAtivado = False

        self.desenhar_escudo(tela)

        if not self.attacking:
            self.base_sword_angle = math.degrees(angle) - 90
            self.sword_angle = self.base_sword_angle

        for particle in sorted(self.sword_trail_particles, key=lambda p: p['alpha']):
            alpha = particle['alpha']
            if alpha <= 0:
                continue

            sword_copy = transform.scale(self.sword,
                                         (int(self.sword.get_width() * particle['size']),
                                          int(self.sword.get_height() * particle['size'])))

            colored_sword = Surface(sword_copy.get_size(), SRCALPHA)
            colored_sword.blit(sword_copy, (0, 0))
            colored_sword.fill(particle['color_mod'], special_flags=BLEND_MULT)
            colored_sword.set_alpha(alpha)

            temp_surface = Surface((colored_sword.get_width() * 2, colored_sword.get_height() * 2), SRCALPHA)
            temp_surface.blit(colored_sword,
                              (temp_surface.get_width() // 2 - self.sword_pivot[0],
                               temp_surface.get_height() // 2 - self.sword_pivot[1]))

            rotated_surface = transform.rotate(temp_surface, -particle['angle'])
            final_rect = rotated_surface.get_rect(center=(particle['x'], particle['y']))
            tela.blit(rotated_surface, final_rect.topleft)

        self.sistemaparticulas.draw(tela)

        # sword_img = self.sword.copy()
        # temp_surface = Surface((sword_img.get_width() * 2, sword_img.get_height() * 2), SRCALPHA)
        # temp_surface.blit(sword_img, (temp_surface.get_width() // 2 - self.sword_pivot[0],
        #                               temp_surface.get_height() // 2 - self.sword_pivot[1]))
        # rotated_surface = transform.rotate(temp_surface, -self.sword_angle)
        # final_rect = rotated_surface.get_rect(center=(base_x, base_y))

        # # Aplicar transparência à espada se o efeito fantasma estiver ativo
        # if 'fantasma' in self.efeitos:
        #     rotated_surface.set_alpha(150)  # 150 de 255 (cerca de 60% de opacidade)
        # tela.blit(rotated_surface, final_rect.topleft)

        angulo_graus = math.degrees(angle) % 360
        desenhar_arma_na_frente = (angulo_graus<=180)

        

        if not desenhar_arma_na_frente:
            self._desenhar_arma(tela, mouse_pos)


        frame = self.frame_atual.copy()
        if self.foi_atingido and time.get_ticks() - self.tempo_atingido < self.invencibilidade:
            frame.fill((255, 255, 255), special_flags=BLEND_RGB_ADD)

        # Aplicar transparência ao jogador se o efeito fantasma estiver ativo
        if 'fantasma' in self.efeitos:
            frame.set_alpha(150)  # 150 de 255 (cerca de 60% de opacidade)

        img_rect = frame.get_rect(center=self.player_rect.center)
        tela.blit(frame, img_rect.topleft)

        if desenhar_arma_na_frente:
            self._desenhar_arma(tela, mouse_pos)

        # projeteis
        for projetil in self.projeteis:
            for part in projetil["trail"]:
                if "sprite" in projetil:
                    trail_sprite = projetil["sprite_original"].copy()
                    trail_sprite.set_alpha(part["alpha"])
                    trail_sprite = transform.scale(projetil["sprite_original"],
                                                   (int(projetil["sprite_original"].get_width() * part["scale"]),
                                                    int(projetil["sprite_original"].get_height() * part["scale"])))

                    rotated = transform.rotate(trail_sprite, -part["angle"])
                    rect = rotated.get_rect(center=(part["x"], part["y"]))
                    tela.blit(rotated, rect.topleft)

            if "sprite" in projetil:
                sprite_rotacionado = transform.rotate(projetil["sprite_original"], -projetil["angulo"])
                rect = sprite_rotacionado.get_rect(center=(projetil["x"], projetil["y"]))
                tela.blit(sprite_rotacionado, rect.topleft)
            else:
                s = Surface((projetil["tamanho"], projetil["tamanho"]), SRCALPHA)
                draw.circle(s, projetil["cor"],
                            (projetil["tamanho"] // 2, projetil["tamanho"] // 2),
                            projetil["tamanho"] // 2)
                tela.blit(s, (projetil["x"] - projetil["tamanho"] // 2,
                              projetil["y"] - projetil["tamanho"] // 2))

        # Hitbox de ataque (debug)
        rotated_hitbox, rotated_rect = self.get_rotated_rect_ataque(mouse_pos)
        # tela.blit(rotated_hitbox, rotated_rect)

        if self.corrente_eletrica_ativa and self.trail_eletrico:
            for trail in self.trail_eletrico:
                # Suaviza a transparência
                alpha = min(200, trail['timer'] / 4000 * 200)

                # Cria surface com transparência
                trail_surface = Surface((trail['rect'].width, trail['rect'].height), SRCALPHA)

                # Adiciona partículas aleatórias para efeito
                for _ in range(3):
                    px = randint(0, trail['rect'].width - 1)
                    py = randint(0, trail['rect'].height - 1)
                    size = randint(1, 3)
                    brightness = randint(200, 255)
                    draw.circle(trail_surface,
                                (brightness, brightness, 255, alpha),
                                (px, py), size)

                tela.blit(trail_surface, trail['rect'].topleft)

        if hasattr(self, 'dano_recebido') and time.get_ticks() - self.dano_recebido_tempo < 500:
            if self.telaSangue_alpha > 0:
                self.telaSangue_alpha = max(0, 255 - (time.get_ticks() - self.dano_recebido_tempo) * 1.02)
                self.telaSangue_surface.set_alpha(int(self.telaSangue_alpha))
                tela.blit(self.telaSangue_surface, (0, 0))

            cor = (255, 0, 0)
            tamanho_fonte = 48
            fonte_atual = font.Font(resource_path('assets/Fontes/KiwiSoda.ttf'), tamanho_fonte)
            texto_str = f"-{self.dano_recebido:.1f}"

            pos_x = 108
            pos_y = 200 - ((time.get_ticks() - self.dano_recebido_tempo) / 4)

            outline_color = (0, 0, 0)
            outline_size = 1
            for x_offset in [-outline_size, 0, outline_size]:
                for y_offset in [-outline_size, 0, outline_size]:
                    if x_offset == 0 and y_offset == 0:
                        continue
                    outline_text = fonte_atual.render(texto_str, True, outline_color)
                    tela.blit(outline_text, (pos_x - outline_text.get_width() / 2 + x_offset, pos_y + y_offset))

            dano_text = fonte_atual.render(texto_str, True, cor)
            tela.blit(dano_text, (pos_x - dano_text.get_width() / 2, pos_y))

    def _desenhar_arma(self, tela, mouse_pos):
        angle = self.calcular_angulo(mouse_pos)
        centro_jogador = (self.player_rect.centerx, self.player_rect.centery)
        base_x = centro_jogador[0] + math.cos(angle) * (self.radius - 5)
        base_y = centro_jogador[1] + math.sin(angle) * (self.radius - 5)

        sword_img = self.sword.copy()
        temp_surface = Surface((sword_img.get_width() * 2, sword_img.get_height() * 2), SRCALPHA)
        temp_surface.blit(sword_img, (temp_surface.get_width() // 2 - self.sword_pivot[0],
                                    temp_surface.get_height() // 2 - self.sword_pivot[1]))
        rotated_surface = transform.rotate(temp_surface, -self.sword_angle)
        final_rect = rotated_surface.get_rect(center=(base_x, base_y))

        if 'fantasma' in self.efeitos:
            rotated_surface.set_alpha(150)
        tela.blit(rotated_surface, final_rect.topleft)
    
    def get_hitbox(self):
        return self.player_rect

    def get_velocidade(self):
        return (self.vx, self.vy)

    def set_velocidade_x(self, vx):
        self.vx = vx

    def set_velocidade_y(self, vy):
        self.vy = vy

    def mover_se(self, pode_x, pode_y, dx, dy):
        if pode_x:
            self.player_rect.x += dx
        if pode_y:
            self.player_rect.y += dy
        self.x, self.y = self.player_rect.topleft

    # def infoArma(self):
    #     print(
    #         f'Dano: {self.arma.dano}\nRapidez: {self.arma.velocidade}\nLife steal: {self.arma.lifeSteal}\nChance de Crítico: {self.arma.chanceCritico}\nDano do Crítico: {self.arma.danoCriticoMod * self.arma.dano}')
    #     print("Nome: ", self.arma.nome)
    #     print(self.atributos["forca"])

    def criar_efeito_sangue(self, x, y):
        for _ in range(5):
            angle = uniform(0, math.pi * 2)
            speed = uniform(1, 1)
            self.sistemaparticulas.add_particle(
                x, y,
                (200, 0, 0),
                (math.cos(angle) * speed, math.sin(angle) * speed),
                500,
                randint(8, 10)
            )

    def ataque_espadaPrincipal(self, inimigos, mouse_pos, dt):
        if hasattr(self, 'tempo_descongelar'):
            return
        current_time = time.get_ticks()
        if self.arma.velocidade <= 0:
            self.arma.velocidade = 1
        cooldown = self.cooldown_ataque_base / self.arma.velocidade
        self.hit_landed = False

        if current_time - self.ultimo_ataque < cooldown:
            return

        if self.arma.ataqueTipo != "ranged":
            self.ultimo_ataque = current_time
            self.attacking = True
            self.attack_start_time = current_time
            self.attack_progress = 0
            angle = self.calcular_angulo(mouse_pos)
            self.base_sword_angle = math.degrees(angle) - 90

            self.last_attack_direction *= -1
            self.attack_direction = self.last_attack_direction

            _, hitbox_espada = self.get_rotated_rect_ataque(mouse_pos)

            if self.arma.tipoDeArma == 'Adaga':
                som.tocar(choice(['faca1', 'faca2']))

            elif self.arma.tipoDeArma == 'Martelo Solar':
                som.tocar('Martelo')

            else:
                som.tocar(choice(['espada1', 'espada2', 'espada3']))

            if current_time - self.tempo_ultimo_hit > self.tempo_max_combo:
                self.hits = 0
                self.arma.comboMult = 1.0

            for inimigo in inimigos:
                if inimigo.vivo and inimigo.get_hitbox().colliderect(hitbox_espada):
                    self.hit_landed = True

                    screen_shaker.start(intensity=9, duration=150)

                    inimigo.anima_hit = True
                    inimigo.time_last_hit_frame = time.get_ticks()
                    self.hits += 1
                    self.tempo_ultimo_hit = current_time
                    self.arma.comboMult = 1.0 + 0.2 * math.log2(self.hits + 1)
                    self.arma.ataquePrincipal(inimigo)
                    inimigo.ultimo_dano_tempo = current_time
                    self.hp = min(self.hp + self.arma.lifeSteal, self.hpMax)

                    dx = inimigo.x - self.x
                    dy = inimigo.y - self.y
                    inimigo.aplicar_knockback(dx, dy, intensidade=0.8)

                    self.criar_efeito_sangue(hitbox_espada.centerx, hitbox_espada.centery)

                    # efeitos
                    for i in self.efeitos:
                        if i == ("lentidao"):
                            inimigo.velocidade *= 0.4
                        elif i == ("veneno"):
                            inimigo.envenenar(5, self.arma.dano)

                    display.flip()

            if not self.hit_landed and current_time - self.tempo_ultimo_hit > self.tempo_max_combo:
                self.hits = 0
                self.arma.comboMult = 1.0
        else:
            som.tocar('arco')
            self.arma.ataquePrincipal(self, mouse_pos)
            self.ultimo_ataque = current_time

    def ataque_espadaSecundario(self, inimigos, mouse_pos, dt):
        current_time = time.get_ticks()
        if hasattr(self, 'tempo_descongelar'):
            return
        if self.arma.velocidade <= 0:
            self.arma.velocidade = 1
        cooldown = self.cooldown_ataque_base / self.arma.velocidade

        if current_time - self.ultimo_ataque < cooldown:
            return
        if self.arma.secEhAtaque:
            if not self.arma.ehRanged:
                self.ultimo_ataque = current_time
                self.attacking = True
                self.attack_start_time = current_time
                self.attack_progress = 0
                angle = self.calcular_angulo(mouse_pos)
                self.base_sword_angle = math.degrees(angle) - 90
                self.attack_direction = 1 if random() > 0.5 else -1

                _, hitbox_espada = self.get_rotated_rect_ataque(mouse_pos)
                for inimigo in inimigos:
                    if inimigo.vivo:
                        if inimigo.get_hitbox().colliderect(hitbox_espada):
                            inimigo.anima_hit = True
                            self.arma.ataqueSecundario(inimigo, self)
                            dx = inimigo.x - self.x
                            dy = inimigo.y - self.y
                            inimigo.aplicar_knockback(dx, dy, intensidade=0.5)

            elif self.arma.ehAOE:
                self.aoe = self.arma.ataqueSecundario(self, mouse_pos)
                self.ultimo_ataque = current_time
                self.attacking = True
                self.attack_start_time = current_time
                self.attack_progress = 0
                angle = self.calcular_angulo(mouse_pos)
                self.base_sword_angle = math.degrees(angle) - 90
                self.attack_direction = 1 if random() > 0.5 else -1

            else:
                if self.arma.ataqueTipo == "melee":
                    self.attacking = True
                    self.attack_start_time = current_time
                    self.attack_progress = 0
                    angle = self.calcular_angulo(mouse_pos)
                    self.base_sword_angle = math.degrees(angle) - 90
                    self.attack_direction = 1 if random() > 0.5 else -1
                self.ultimo_ataque = current_time
                self.arma.ataqueSecundario(self, mouse_pos)
        else:
            self.arma.ataqueSecundario(self)

    def tomar_dano(self, valor):
        now = time.get_ticks()
        if now - self.ultimo_dano < self.invencibilidade:
            return
        self.ultimo_dano = now
        som.tocar(choice(['Dano1', 'Dano2', 'Dano3']))

        valor *= dificuldade_global.mult_dano_jogador
        self.hp -= valor
        self.foi_atingido = True
        self.tempo_atingido = now

        self.dano_recebido_tempo = now
        self.dano_recebido = valor * self.modificadorDanoRecebido
        self.telaSangue_alpha = 255
        screen_shaker.start(intensity=4, duration=150)
        if self.telaSangue_surface is None:
            self.telaSangue_surface = self.telaSangue.copy()

    def atualizar_arma(self):
        self.sword = transform.scale(transform.flip(image.load(self.arma.sprite).convert_alpha(), True, True),
                                     (self.arma.size))
        self.sword_pivot = self.arma.pivot
        self.cooldown_ataque_base = self.arma.cooldown
        self.radius = self.arma.radius - 50
        self.hitbox_arma = self.arma.range

    def atualizar_traits(self, trait):
        '''
        Ancião - Todo ataque aplica lentidão (lista de efeitos no jogador, aplica cada um se nao for vazio)
        Nojento - Todo ataque aplica veneno (lista de efeitos no jogador, aplica cada um se nao for vazio)
        Mercúrio - Mais velocidade, Menos dano
        Humano - Vida não decai, mas tem menos dano e menos life steal
        Translûcido - Não tem colisão com caixa (SFC)
        '''
        if trait == "Mercúrio":
            self.velocidadeMov += 0.08
            self.arma.dano -= 6
        elif trait == "Humano":
            self.base_rate = 0
            self.rate = 0
            self.arma.dano -= 6
            self.arma.lifeSteal /= 1.6
        elif trait == "Ancião":
            self.efeitos.append("lentidao")
        elif trait == "Peçonhento":
            self.efeitos.append("veneno")
        elif trait == "Translúcido":
            self.tipo_colisao = 'voador'
            self.efeitos.append('fantasma')
            self.arma.dano -= 13

    def atualizar_atributos(self):
        if self.macarronada == 0:
            self.base_dano = self.arma.dano
            self.base_danoCriticoMod = self.arma.danoCriticoMod
            self.base_velocidade = self.arma.velocidade
            self.base_chanceCritico = self.arma.chanceCritico
            self.macarronada += 1

        self.base_rate = 0.5
        self.base_rateSt = 1
        self.base_velocidadeMov = 0.5
        self.base_custoDash = 2.75
        self.base_modificadorDanoRecebido = 1
        self.base_invencibilidade = 500
        self.base_cooldown_st = 3222.22
        self.base_dash_cooldown_max = 1000
        self.base_dash_duration_max = 150

        self.arma.dano = max(1,self.base_dano * (1 + (self.atributos["forca"] - 5) / 5))
        self.arma.lifeSteal = self.arma.dano/self.arma.lifeStealMod
        self.arma.danoCriticoMod = self.base_danoCriticoMod * (1 + (self.atributos["forca"] - 5) / 5)
        self.arma.velocidade = max(0.2,self.base_velocidade * (1 + ((self.atributos["destreza"] - 5) / 5) * 0.5))
        self.arma.chanceCritico = max(1,self.base_chanceCritico * (1 + ((self.atributos["sorte"] - 5) / 5) * 3))
        self.rate = self.base_rate - (self.atributos["vigor"] - 5) / 20
        self.rateSt = self.base_rateSt + ((self.atributos["estamina"] - 5) / 5) * 0.6
        self.velocidadeMov = self.base_velocidadeMov + ((self.atributos["agilidade"] - 5) / 5) * 0.5
        self.custoDash = self.base_custoDash - ((self.atributos["estamina"] - 5) / 5) * 0.75
        self.modificadorDanoRecebido = self.base_modificadorDanoRecebido - (
                (self.atributos["resistencia"] - 5) / 5) * 0.5
        self.invencibilidade = int(self.base_invencibilidade + ((self.atributos["resistencia"] - 5) / 5) * 500)
        self.cooldown_st = round(self.base_cooldown_st - (self.atributos["estamina"] - 5) * 444.44)
        self.dash_cooldown_max = int(self.base_dash_cooldown_max - ((self.atributos["estamina"] - 5) / 5) * 750)
        self.dash_duration_max = int(self.base_dash_duration_max + ((self.atributos["estamina"] - 5) / 5) * 250)

    def get_save_data(self):
        return {
            'position': [self.x, self.y],
            'stats': {
                'hp': self.hp,
                'hpMax': self.hpMax,
                'mp': self.mp,
                'almas': self.almas,
                'velocidadeMov': self.velocidadeMov,
                'atributos': self.atributos
            },
            'itens': [item.id for item in self.itens],
            'itemAtivo': self.itemAtivo.id if self.itemAtivo else None,
            'arma': self.arma.get_save_data() if hasattr(self.arma, 'get_save_data') else None,
            'inventario': [x.get_save_data() for x in self.inventario],
            'trait': self.trait,
            'habilidades': self.habilidades,
            'hotkeys': self.hotkeys,
            'pocoes': {'hp': self.pocoesHp, 'mp': self.pocoesMp},
            'revives': self.revives,
        }

    def load_save_data(self, data, conjunto_itens, lista_mods):
        self.x, self.y = data['position']
        self.player_rect.topleft = self.x, self.y

        stats = data['stats']
        self.hp = stats['hp']
        self.hpMax = stats['hpMax']
        self.mp = stats['mp']
        self.almas = stats['almas']
        self.velocidadeMov = stats['velocidadeMov']
        self.atributos = stats['atributos']

        self.itens = {}
        # self.inventario = data["inventario"] resolver isso depois
        for item_id in data['itens']:
            if item_id == 2:
                self.atributos['agilidade'] -= 0.3
            item = conjunto_itens.itens_por_id[item_id]
            self.adicionarItem(item)

        if data['itemAtivo']:
            self.itemAtivo = conjunto_itens.itens_por_id[data['itemAtivo']]

        if data['arma']:
            arma_class = globals().get(data['arma']['tipo'])
            if arma_class:
                self.arma = arma_class(data['arma']['raridade'], lista_mods)
                self.arma.load_save_data(data['arma'], lista_mods)
                # self.arma.aplicaModificador()  # Adicione esta linha
                self.atualizar_arma()

        if 'inventario' in data:
            self.inventario = []
            for arma_data in data['inventario']:
                arma_class = globals().get(arma_data['tipo'])
                if arma_class:
                    arma = arma_class(arma_data['raridade'], lista_mods)
                    arma.load_save_data(arma_data, lista_mods)
                    # arma.aplicaModificador()
                    self.inventario.append(arma)
                    self.atualizar_arma()

        if 'trait' in data:
            self.trait = data['trait']
            self.atualizar_traits(self.trait)

        if 'habilidades' in data:
            self.habilidades = data['habilidades']

        if 'hotkeys' in data:
            self.hotkeys = data['hotkeys']

        if 'pocoes' in data:
            self.pocoesHp = data['pocoes'].get('hp', 0)
            self.pocoesMp = data['pocoes'].get('mp', 0)

        if 'revives' in data:
            self.revives = data['revives']

        self.atualizar_atributos()

    def resetar_estado_temporario(self):
        self.vx = 0
        self.vy = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.travado = False
        self.direcao = "baixo"  # ou o que quiser como default
        self.rect = self.player_rect

    #------pocoes-------
    def usar_pocao_mana(self):
        self.hud.mark_potion_pressed(1)
        if self.pocoesMp <= 0:
            return
        self.pocoesMp -= 1
        if "Estomago de Mana" not in self.habilidades:
            self.mp += 30
            return
        else:
            self.mp = self.mpMaximo

    def usar_pocao_vida(self):
        self.hud.mark_potion_pressed(0)
        if self.pocoesHp <= 0:
            return
        self.pocoesHp -= 1
        self.hp += 15


    # ---------HABILIDADES---------

    def bola_de_fogo(self):
        if "Bola de Fogo" not in self.habilidades:
            return
        mouse_pos = mouse.get_pos()
        sprite_projetil = image.load(resource_path('assets/player/bola_de_fogo.png')).convert_alpha()
        current_time = time.get_ticks()
        custoHabilidade = 30 * self.mpModificador
        if self.mp < custoHabilidade:
            # Ativa mensagem de sem mana no HUD
            self.hud.mensagem_sem_mana = True
            self.hud.tempo_mensagem_mana = current_time
            return
        if self.mp - custoHabilidade <= 0:
            return
        else:
            self.criar_projetil(mouse_pos, dano=20, cor=None, sprite=sprite_projetil)
            self.mp -= custoHabilidade
            self.last_dash_time = current_time

    def clarao(self):
        if "Clarão" not in self.habilidades:
            return
        current_time = time.get_ticks()
        custoHabilidade = 75*self.mpModificador
        if self.mp < custoHabilidade:
            # Ativa mensagem de sem mana no HUD
            self.hud.mensagem_sem_mana = True
            self.hud.tempo_mensagem_mana = current_time
            return
        if self.mp < custoHabilidade:
            return

        if hasattr(self, 'ultimo_clarao') and current_time - self.ultimo_clarao < 4000:
            return

        if hasattr(self, 'claraoAtivado') and self.claraoAtivado:
            return

        self.claraoDano = 70
        self.claraoAtivado = True
        self.travado = True

        tamanho_aoe = 300
        centro_x = self.player_rect.centerx
        centro_y = self.player_rect.centery
        self.aoe = self.criarAOE((centro_x, centro_y), tamanho_aoe)
        if self.aoe is None:
            return

        self.inimigos_atingidos_este_clarao = []
        self.ultimo_clarao = current_time

        self.mp -= custoHabilidade
        self.last_dash_time = current_time

    def nevasca(self):
        if "Nevasca" not in self.habilidades:
            return
        self.nevascaAtivada = True
        mouse_pos = mouse.get_pos()
        sprite_projetil = image.load(resource_path('assets/player/bola_de_gelo.png')).convert_alpha()
        current_time = time.get_ticks()
        custoHabilidade = 30*self.mpModificador
        if self.mp < custoHabilidade:
            # Ativa mensagem de sem mana no HUD
            self.hud.mensagem_sem_mana = True
            self.hud.tempo_mensagem_mana = current_time
            return
        if self.mp - custoHabilidade <= 0:
            return
        else:
            self.criar_projetil(mouse_pos, dano=30, cor=None, sprite=sprite_projetil)
            self.mp -= custoHabilidade
            self.last_dash_time = current_time

    def trovao(self):
        if "Trovão" not in self.habilidades:
            return
        self.trovaoAtivado = True
        mouse_pos = mouse.get_pos()
        sprite_projetil = image.load(resource_path('assets/player/Raio.png')).convert_alpha()
        current_time = time.get_ticks()
        custoHabilidade = 40*self.mpModificador
        if self.mp < custoHabilidade:
            # Ativa mensagem de sem mana no HUD
            self.hud.mensagem_sem_mana = True
            self.hud.tempo_mensagem_mana = current_time
            return
        if self.mp - custoHabilidade <= 0:
            return
        else:
            self.criar_projetil(mouse_pos, dano=65, cor=None, sprite=sprite_projetil)
            self.mp -= custoHabilidade
            self.last_dash_time = current_time

    def nuvem_de_veneno(self):
        if "Núvem de Veneno" not in self.habilidades:
            return
        current_time = time.get_ticks()
        custoHabilidade = 75*self.mpModificador
        if self.mp < custoHabilidade:
            # Ativa mensagem de sem mana no HUD
            self.hud.mensagem_sem_mana = True
            self.hud.tempo_mensagem_mana = current_time
            return
        if self.mp < custoHabilidade:
            return

        if hasattr(self, 'ultimo_clarao') and current_time - self.ultimo_clarao < 4000:
            return

        if hasattr(self, 'claraoAtivado') and self.claraoAtivado:
            return

        self.nuvemAtivado = True

        tamanho_aoe = 300
        centro_x = self.player_rect.centerx
        centro_y = self.player_rect.centery
        self.aoeVeneno = self.criarAOE((centro_x, centro_y), tamanho_aoe)
        if self.aoeVeneno is None:
            return
        self.ultimo_clarao = current_time

        self.mp -= custoHabilidade
        self.last_dash_time = current_time

    def fonte_arcana(self):
        if "Fonte Arcana" not in self.habilidades:
            return
        if not self.mp >= self.mpMaximo: self.mp += 0.15

    def escudo(self):
        if "Escudo" not in self.habilidades:
            return
        self.mpMaximo = 75
        self.base_modificadorDanoRecebido = 0.75

        # Adiciona um atributo para controlar o estado do escudo
        self.escudo_ativado = True

    def eficiencia_arcana(self):
        if "Eficiência Arcana" not in self.habilidades:
            return
        self.mpModificador = 0.5

    def ativar_habilidade(self, nome_habilidade):
        for i, hab in enumerate(self.hotkeys):
            if hab == nome_habilidade:
                self.hud.mark_hotkey_pressed(i)
                break
        if nome_habilidade == "Bola de Fogo":
            self.bola_de_fogo()
        elif nome_habilidade == "Clarão":
            self.clarao()
        elif nome_habilidade == "Nevasca":
            self.nevasca()
        elif nome_habilidade == "Trovão":
            self.trovao()
        elif nome_habilidade == "Núvem de Veneno":
            self.nuvem_de_veneno()
        elif nome_habilidade == "Fonte Arcana":
            self.fonte_arcana()
        elif nome_habilidade == "Escudo":
            self.escudo()
        elif nome_habilidade == "Eficiência Arcana":
            self.eficiencia_arcana()

    def desenhar_escudo(self, tela):
        if hasattr(self, 'escudo_ativado') and self.escudo_ativado:
            # Cria uma superfície transparente para o escudo
            escudo_surface = Surface((120, 120), SRCALPHA)

            # Desenha um círculo azul translúcido
            draw.circle(escudo_surface, (200, 200, 255, 20),  # Cor azul com transparência
                        (60, 60),  # Centro da superfície
                        60)  # Raio do círculo

            # Posiciona o escudo centrado no jogador
            escudo_rect = escudo_surface.get_rect(center=self.player_rect.center)
            tela.blit(escudo_surface, escudo_rect.topleft)



    def aplicar_lentidao(self, mult, duracao):
        self.duracao_lentidao = duracao
        if not self.lentidao_ativa:
            self.velocidadeOld = self.velocidadeMov
            self.lentidao_ativa = True
            self.velocidadeMov *= mult
            self.tempo_lentidao = pygame.time.get_ticks()

    def atualizar_lentidao(self):
        if self.lentidao_ativa:
            if pygame.time.get_ticks() - self.tempo_lentidao > self.duracao_lentidao:
                self.lentidao_ativa = False
                self.velocidadeMov = self.velocidadeOld

    def aplicar_veneno(self, duracao):
        self.envenenado = True
        self.duracao_veneno = duracao
        self.tempo_veneno = pygame.time.get_ticks()
        self.proximo_tick_veneno = self.tempo_veneno + self.intervalo_veneno

    def atualizar_veneno(self):
        if self.envenenado:
            agora = pygame.time.get_ticks()
            if agora >= self.proximo_tick_veneno:
                self.proximo_tick_veneno += self.intervalo_veneno
                self.hp -= self.venenoDano / 10  # Aplica dano periódico
                if self.hp < 1:
                    self.hp = 1  # evita que morra pelo veneno
            if agora - self.tempo_veneno > self.duracao_veneno:
                self.envenenado = False

    def congelar(self, duracao):
        """Congela o jogador por uma determinada duração em milissegundos."""
        current_time = time.get_ticks()
        self.travado = True
        self.proibir_dash_ate = current_time + duracao  # Impede dash durante o congelamento
        self.tempo_descongelar = current_time + duracao  # Armazena quando deve descongelar

    def atualizar_trail_eletrico(self):
        if not self.corrente_eletrica_ativa or not self.is_dashing:
            return

        # Cria um novo segmento do trail
        segment_width = 20  # Largura da linha elétrica
        segment = Rect(self.x - segment_width / 2, self.y, segment_width, self.altura)

        # Adiciona à lista de trails
        self.trail_eletrico.append({
            'rect': segment,
            'timer': 4000  # 4 segundos de duração
        })