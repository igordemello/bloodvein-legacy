from pygame import *
from pygame.locals import QUIT
import sys
from random import sample
from botao import Botao
from itensDic import ConjuntoItens
from pygame.math import Vector2
import math
from som import GerenciadorDeSom
from som import som
from som import GerenciadorDeMusica
from som import musica
from utils import resource_path 
class Loja():
    def __init__(self, conjunto: ConjuntoItens, player,ids_sorteados=None, comprado=None, no_grafo=None):
        self.personagem_img = transform.scale(transform.flip(image.load(resource_path('assets/iko.png')).convert_alpha(), True, False),(1183, 1092))
        self.fundo = image.load(resource_path('assets/loja.png')).convert_alpha()
        
        self.itensDisp = conjunto

        self.ids_disponiveis = list(conjunto.itens_por_id)
        if ids_sorteados is None:
            self.ids_sorteados = sample(self.ids_disponiveis, 3)
        else:
            self.ids_sorteados = ids_sorteados
        self.itens_sorteados = [self.itensDisp.itens_por_id[id_] for id_ in self.ids_sorteados]
        
        self.precos = {
            "comum": 10,
            "rara": 20,
            "lendaria": 30,
            "ativo": 15
        }
        
        self.player = player
        self.tempo = 0  # Para animação

        self.font_titulo = font.Font(resource_path('assets/Fontes/alagard.ttf'), 30,)
        self.font_desc = font.Font(resource_path('assets/Fontes/alagard.ttf'), 20)
        self.font_preco = font.Font(resource_path('assets/Fontes/alagard.ttf'), 35, )
        self.font_chata = font.Font(resource_path('assets/Fontes/alagard.ttf'), 20, )

        self.musica = 0


    

        self.estados_hover = [Vector2(1.0, 0.0) for _ in self.itens_sorteados]
        self.descricao_visivel = [False] * 3
        
        self.botoes = []
        self.item_width, self.item_height = 260, 270
        
    
        # Carregar imagens de cartas por raridade
        self.carta_imgs = {
            "comum": transform.scale(image.load(resource_path('assets/itens/carta_comum_loja.png')).convert_alpha(), (self.item_width + 40, self.item_height + 130)),
            "rara": transform.scale(image.load(resource_path('assets/itens/carta_rara_loja.png')).convert_alpha(), (self.item_width + 40, self.item_height + 130)),
            "lendaria": transform.scale(image.load(resource_path('assets/itens/carta_lendaria_loja.png')).convert_alpha(), (self.item_width + 40, self.item_height + 130)),
            "ativo": transform.scale(image.load(resource_path('assets/itens/carta_ativo_loja.png')).convert_alpha(), (self.item_width + 40, self.item_height + 130))
        }
            
        for i in range(3):
                base_x = 25
                base_y = 75 + i * 320
                botao = Botao(
                    image=Surface((self.item_width, self.item_height), SRCALPHA),
                    pos=(base_x + self.item_width//2, base_y + self.item_height//2),
                    text_input="",
                    font=self.font_titulo,
                    base_color=(255, 255, 255, 0),
                    hovering_color=(255, 255, 255, 0)
                )
                self.botoes.append(botao)

        self.botaosair = Botao(image=None, pos=(100,1030),text_input="Sair",font=self.alagard(48), base_color=(117,6,30), hovering_color=(155,26,54))
        

        self.comprado = comprado
        self.no_grafo = no_grafo
        

    def img_alma(self,tam):
        return transform.scale(image.load(resource_path('assets/Itens/alma.png')).convert_alpha(),(tam,tam))

    def alagard(self, tam):
        return font.Font(resource_path('assets/Fontes/alagard.ttf'), tam)
    

    def desenhar_loja(self, tela):
        self.musica = 1
        musica.tocar(resource_path("BloodVein SCORE/OST/Loja.mp3"))
        tela.fill((0, 0, 0))
        tela.blit(self.fundo,(0,0))
        tela.blit(self.personagem_img, (800, 50))

        mouse_pos = mouse.get_pos()
        self.tempo += 0.05

        #quantidade de almas
        almas = self.alagard(40).render(f'{self.player.almas}x', True,(253, 246, 225))
        x_almas, y_almas = 50, 50
        tela.blit(almas,(x_almas,y_almas))
        texto_width = almas.get_width()
        tela.blit(self.img_alma(48), (x_almas + texto_width + 2.5, y_almas-16))

        for pos, item in enumerate(self.itens_sorteados):


            base_x = -20
            base_y = 120 + pos * 260

            item_rect = Rect(base_x, base_y, self.item_width, self.item_height)
            is_hovered = item_rect.collidepoint(mouse_pos)
            self.descricao_visivel[pos] = is_hovered

            alvo = Vector2(1.05, -20) if is_hovered else Vector2(1.0, 0.0)
            self.estados_hover[pos] = self.estados_hover[pos].lerp(alvo, 0.1)

            scale = self.estados_hover[pos].x
            offset_y = self.estados_hover[pos].y

            width = int(self.item_width * scale)
            height = int(self.item_height * scale)
            pos_x = base_x + (self.item_width - width) // 2
            pos_y = base_y + offset_y
            
            if is_hovered == True:
                # Desenhar imagem da carta de fundo (DEPOIS FAZER NO BOLSO DELA)
                carta_base = transform.scale(self.carta_imgs[item.raridade], (width + 40, height + 130))
                tela.blit(carta_base, (pos_x + 1200, 525))

                item_img = transform.scale(item.sprite, (100, 100))
                tela.blit(item_img, (1280,40 + 525))

                nome = self.font_chata.render(item.nome, True, (0,0,0))
                tela.blit(nome, (1250, 182 + 525))

                # Descrição 
                carta_x = pos_x + 1200
                carta_y = 525

                # Margens internas da carta
                margem_lateral = 30
                margem_topo = 220  # espaço pra imagem e título
                largura_texto = self.carta_imgs[item.raridade].get_width() - 2 * margem_lateral

                # Quebra de texto dentro da largura da carta
                desc_lines = self.quebrar_texto_em_linhas(item.descricao, self.font_desc, largura_texto)

                # Desenhar texto linha a linha
                for i, line in enumerate(desc_lines):
                    desc_text = self.font_desc.render(line, True, (0,0,0))
                    tela.blit(desc_text, (carta_x + margem_lateral, carta_y + 20 + margem_topo + i * 22))



            

            #Sprite do item
            item_img = transform.scale(item.sprite, (140, 140))
            tela.blit(item_img, (pos_x + (width - 100)//2, pos_y + 70))

            # Nome do item
            if self.comprado[pos]:
                nome = self.alagard(30).render("COMPRADA", True, (200, 50, 50))
            else:
                nome = self.alagard(30).render(item.nome, True, (253, 246, 225))

            tela.blit(nome, (pos_x + 250, pos_y + 100))

            #Preço
            preco = self.alagard(25).render(f"Preço: {self.precos[item.raridade]}", True, (253, 246, 225))
            tela.blit(preco, (pos_x + 250, pos_y+150))
            texto_width_price = almas.get_width()
            tela.blit(self.img_alma(32), (pos_x + 250 + 40+ texto_width_price + 2.5, pos_y+150-8))

            

    
        for botao in self.botoes: # para todos os botões (para aparecerem na tela)
            botao.changeColor(mouse_pos)
            botao.update(tela)
        self.botaosair.changeColor(mouse_pos)
        self.botaosair.update(tela)

    def quebrar_texto_em_linhas(self, texto, fonte, largura_max):
        palavras = texto.split()
        linhas = []
        linha_atual = ""
        
        for palavra in palavras:
            teste = linha_atual + (" " if linha_atual else "") + palavra
            if fonte.size(teste)[0] <= largura_max:
                linha_atual = teste
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra
        
        if linha_atual:
            linhas.append(linha_atual)
        
        return linhas

      

    def checar_compra(self, mouse_pos, tela):

        if self.botaosair.checkForInput(mouse_pos):
            som.tocar("clique")
            self.musica = 0
            return 'sair'
        
        for i, botao in enumerate(self.botoes):

            if botao.checkForInput(mouse_pos):
                item = self.itens_sorteados[i]
                preco = self.precos[item.raridade]
            

                if self.player.almas >= preco and not self.comprado[i]:
                    som.tocar("buy")
                    self.player.almas -= preco
                    self.player.adicionarItem(item)
                    comprado = self.font_preco.render("COMPRADO", True, ('Green'))
                    tela.blit(comprado, (0, 0))
                    self.comprado[i] = True
                    self.no_grafo["itens_comprados"] = self.comprado
                    
                    return True
                else:
                    falta = self.font_preco.render("Faltam almas", True, ('red'))
                    tela.blit(falta, (0, 0))
                    return False