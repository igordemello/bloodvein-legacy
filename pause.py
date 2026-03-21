from pygame import *
from som import musica
from utils import resource_path 
from botao import Botao

class Pause:
    def __init__(self):
        self.font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 24)

        # Botões com hover animado
        botao_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 48)
        cor_base = (228, 133, 40)
        cor_hover = (255, 190, 80)

        self.botaocontinuar = Botao(image=None, pos=(1920//2, 400), text_input="CONTINUAR", font=botao_font, base_color=cor_base, hovering_color=cor_hover)
        self.botaosair = Botao(image=None, pos=(1920//2, 500), text_input="SAIR", font=botao_font, base_color=cor_base, hovering_color=cor_hover)

        self.botoes = [self.botaocontinuar,  self.botaosair]

        self.menu_ativo = False

        self.pause_font = font.Font(resource_path('assets/Fontes/alagard.ttf'), 72)


    def pauseFuncionamento(self, tela, mouse_pos,imagem_fundo=None):
        try:
            self.menu_ativo = True

            if imagem_fundo:
                tela.blit(imagem_fundo, (0, 0))

                overlay = Surface((1920, 1080), SRCALPHA)
                overlay.fill((0, 0, 0, 180)) 
                tela.blit(overlay, (0, 0))

            # Título
            pause_text = self.pause_font.render("PAUSADO", True, (228, 133, 40))
            text_rect = pause_text.get_rect(center=(1920 // 2, 150))
            tela.blit(pause_text, text_rect)

            # Hover e update dos botões
            for botao in self.botoes:
                botao.changeColor(mouse_pos)
                botao.update(tela)
        except Exception as e:
            print(f"[PAUSE CRASH] {type(e).__name__}: {e}")
        

    def checar_clique_pause(self, mouse_pos,):
        try:
            if not self.menu_ativo:
                return None
            if self.botaocontinuar.checkForInput(mouse_pos):
                musica.retomar()
                self.menu_ativo = False
                return "continuar"
            if self.botaosair.checkForInput(mouse_pos):
                return "sair"
            return None
        except Exception as e:
            print(f"[PAUSE CLICK CRASH] {type(e).__name__}: {e}")
            return None
