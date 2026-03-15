from pygame import *
from pygame.math import Vector2
from efeito import *
from itensDic import ConjuntoItens
from random import sample
from botao import Botao
from random import choices
from utils import resource_path 
class Bau:
    def __init__(self, conjunto: ConjuntoItens, posx, posy):
        self.itensDisp = conjunto
        self.ids_disponiveis = list(conjunto.itens_por_id)

        raridade_pesos = {
            "comum": 60,
            "rara": 30,
            "lendaria": 10,
            "ativo": 35
        }

        ids_restantes = self.ids_disponiveis.copy()
        self.ids_sorteados = []

        for _ in range(3):
            pesos = []
            for id_ in ids_restantes:
                item = self.itensDisp.itens_por_id[id_]
                pesos.append(raridade_pesos.get(item.raridade, 10))
            escolhido = choices(ids_restantes, weights=pesos, k=1)[0]
            self.ids_sorteados.append(escolhido)
            ids_restantes.remove(escolhido)

        self.itens_sorteados = [self.itensDisp.itens_por_id[id_] for id_ in self.ids_sorteados]
        self.font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 24)
        self.fontDesc = font.Font(resource_path('assets/Fontes/alagard.ttf'), 24)

        self.botoes = []
        self.estados_hover = [Vector2(1.0, 0.0) for _ in self.itens_sorteados]

        self.image_fundo = Surface((375, 500), SRCALPHA)
        self.image_fundo.fill((0, 0, 0, 0))


        for i in range(len(self.itens_sorteados)):
            x = 350 + 400 * i + 375 // 2
            y = 400 + 500 // 2
            botao = Botao(
                image=self.image_fundo,
                pos=(x, y),
                text_input="",
                font=self.font,
                base_color=(255, 255, 255),
                hovering_color=(0, 0, 0)
            )
            self.botoes.append(botao)

        self.botaosair = Botao(image=None, pos=(200,980), text_input="Sair", font=font.Font(resource_path('assets/Fontes/alagard.ttf'), 32), base_color=(244,26,43), hovering_color=(202, 56, 68))
        
        #
        self.escala = 3
        self.spritesheet = image.load(resource_path('assets/bau_sheet.png')).convert_alpha()
        self.frames = self._carregar_frames()
        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(posx, posy))

        self.aberto = False
        self.animando = False
        self.tempo_ultimo_frame = time.get_ticks()
        self.duracao_frame = 150  #ms por frame
        self.menu_ativo = False
        self.item_escolhido = None

    def _carregar_frames(self):
        largura = self.spritesheet.get_width() // 4
        altura = self.spritesheet.get_height()
        return [
            transform.scale(
                self.spritesheet.subsurface(Rect(i * largura, 0, largura, altura)),
                (largura * self.escala, altura * self.escala)
            ) for i in range(4)
        ]
    
    def abrir(self):
        if not self.aberto and not self.animando:
            self.animando = True
            self.frame_index = 0
            self.tempo_ultimo_frame = time.get_ticks()

    
    def update(self, player_hitbox=None):
        if self.animando:
            agora = time.get_ticks()
            if agora - self.tempo_ultimo_frame > self.duracao_frame:
                self.tempo_ultimo_frame = agora
                self.frame_index += 1
                if self.frame_index >= len(self.frames):
                    self.frame_index = len(self.frames) - 1
                    self.animando = False
                    self.aberto = True
                    self.menu_ativo = True
                self.image = self.frames[self.frame_index]

        


    def bauEscolherItens(self, tela, mouse_pos):
        overlay = Surface(tela.get_size(), SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

    

        for pos, item in enumerate(self.itens_sorteados):
            base_x = 350 + 400 * pos
            base_y = 300
            carta_width, carta_height = 375, 500
            carta_rect = Rect(base_x, base_y, carta_width, carta_height)

            # Detecta hover e faz interpolação
            is_hovered = carta_rect.collidepoint(mouse_pos)
            alvo = Vector2(1.1, -30) if is_hovered else Vector2(1.0, 0.0)
            self.estados_hover[pos] = self.estados_hover[pos].lerp(alvo, 0.1)

            scale = self.estados_hover[pos].x
            deslocamento_y = self.estados_hover[pos].y

            width = int(carta_width * scale)
            height = int(carta_height * scale)
            pos_x = base_x + carta_width // 2 - width // 2
            pos_y = base_y + deslocamento_y

            sprite_raridade = image.load(resource_path(f'assets/itens/carta_{item.raridade}.png')).convert_alpha()
            sprite_carta = transform.scale(sprite_raridade, (width, height))
            tela.blit(sprite_carta, (pos_x, pos_y))

            sprite_item = transform.scale(item.sprite, (int(128 * scale), int(128 * scale)))
            item_center_x = pos_x + width // 2 - sprite_item.get_width() // 2
            tela.blit(sprite_item, (item_center_x, pos_y + int(40 * scale)))

            # Nome centralizado e mais próximo do item
            titulo = self.font.render(item.nome, True, (0, 0, 0))
            titulo_rect = titulo.get_rect(center=(pos_x + width // 2, pos_y + 20 + int(height * 0.42)))
            tela.blit(titulo, titulo_rect)

            # Descrição centralizada linha por linha (ajustada para não passar das margens)
            max_largura_texto = width - 70
            descricao_linhas = self.quebrar_texto_em_linhas(item.descricao, self.fontDesc, max_largura_texto)
            y_base = pos_y + int(height * 0.52)
            for i, linha in enumerate(descricao_linhas):
                texto = self.fontDesc.render(linha, True, (0, 0, 0))
                texto_rect = texto.get_rect(center=(pos_x + width // 2, y_base + 50+ i * 24))
                tela.blit(texto, texto_rect)

        self.botaosair.changeColor(mouse_pos)
        self.botaosair.update(tela)
        for botao in self.botoes:
            botao.changeColor(mouse_pos)
            botao.update(tela)

    def quebrar_texto_em_linhas(self, texto, fonte, largura_max):
        palavras = texto.split()
        linhas = []
        linha_atual = ""

        for palavra in palavras:
            teste = linha_atual + (" " if linha_atual else "") + palavra
            if fonte.size(teste)[0] <= largura_max:
                linha_atual = teste
            else:
                linhas.append(linha_atual)
                linha_atual = palavra

        if linha_atual:
            linhas.append(linha_atual)

        return linhas

    def checar_clique_bau(self, mouse_pos):
        if not self.menu_ativo:
            return None
        for i, botao in enumerate(self.botoes):
            if self.botaosair.checkForInput(mouse_pos):
                self.menu_ativo = False
                return 'sair'
            if botao.checkForInput(mouse_pos):
                item_escolhido = self.itens_sorteados[i]
                print(f"Item escolhido: {item_escolhido.nome}")
                self.menu_ativo = False
                return item_escolhido
        return None