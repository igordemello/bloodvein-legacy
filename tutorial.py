from pygame import *
from utils import resource_path


class Tutorial:
    PASSOS = [
        {
            "titulo": "Bem-vindo ao Blood Vein!",
            "linhas": [
                "Você acordou no castelo da sua linhagem.",
                "Explore os andares, colete itens e sobreviva.",
            ],
        },
        {
            "titulo": "Movimento",
            "linhas": [
                "W A S D  -  Mover-se pelo ambiente",
                "ESPAÇO   -  Dar Dash (esquivar rapidamente)",
            ],
        },
        {
            "titulo": "Combate",
            "linhas": [
                "Clique Esquerdo  -  Ataque Principal",
                "Clique Direito   -  Ataque Pesado",
            ],
        },
        {
            "titulo": "Habilidades & Itens",
            "linhas": [
                "1  2  3  4  -  Habilidades       Q  -  Item Ativo",
                "C  -  Poção de Vida              V  -  Poção de Mana",
            ],
        },
        {
            "titulo": "Exploração",
            "linhas": [
                "I  -  Inventário        TAB  -  Minimapa",
                "E  -  Interagir com Loja    ESC  -  Pausar",
            ],
        },
        {
            "titulo": "Pronta para batalhar!",
            "linhas": [
                "Derrote todos os inimigos de uma sala para abrir as portas.",
                "Avance pelos andares e chegue ao fim do castelo. Boa sorte!",
            ],
        },
    ]

    PANEL_W = 1060
    PANEL_H = 210
    PANEL_X = (1920 - PANEL_W) // 2
    PANEL_Y = 628

    FADE_IN_SPEED  = 10
    FADE_OUT_DURACAO = 1400  # ms

    def __init__(self):
        self.passo = 0
        self.ativo = True
        self.alpha = 0
        self.fading_out = False
        self.fade_out_inicio = 0

        self.fonte_titulo = font.Font(resource_path('assets/Fontes/alagard.ttf'), 36)
        self.fonte_texto  = font.Font(resource_path('assets/Fontes/alagard.ttf'), 26)
        self.fonte_hint   = font.Font(resource_path('assets/Fontes/alagard.ttf'), 19)
        self.fonte_count  = font.Font(resource_path('assets/Fontes/alagard.ttf'), 19)

        self.panel_rect = Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H)

    # ── Controle ──────────────────────────────────────────────────

    def avancar(self):
        if self.fading_out:
            return
        self.passo += 1
        self.alpha = 0
        if self.passo >= len(self.PASSOS):
            self.fading_out = True
            self.fade_out_inicio = time.get_ticks()

    def pular(self):
        self.ativo = False

    # ── Update ────────────────────────────────────────────────────

    def update(self):
        if not self.ativo:
            return
        if self.fading_out:
            if time.get_ticks() - self.fade_out_inicio >= self.FADE_OUT_DURACAO:
                self.ativo = False
            return
        self.alpha = min(230, self.alpha + self.FADE_IN_SPEED)

    # ── Desenho ───────────────────────────────────────────────────

    def desenhar(self, tela):
        if not self.ativo:
            return

        alpha = self.alpha
        if self.fading_out:
            elapsed = time.get_ticks() - self.fade_out_inicio
            alpha = max(0, int(230 * (1 - elapsed / self.FADE_OUT_DURACAO)))

        cena = self.PASSOS[min(self.passo, len(self.PASSOS) - 1)]

        surf = Surface((self.PANEL_W, self.PANEL_H))
        surf.fill((12, 8, 6))

        # Bordas decorativas
        draw.rect(surf, (212, 175, 55), Rect(0, 0, self.PANEL_W, self.PANEL_H), 3)
        draw.rect(surf, (90, 72, 38),   Rect(7, 7, self.PANEL_W - 14, self.PANEL_H - 14), 1)

        # Título
        titulo_s = self.fonte_titulo.render(cena["titulo"], True, (212, 175, 55))
        surf.blit(titulo_s, (self.PANEL_W // 2 - titulo_s.get_width() // 2, 18))

        # Texto das linhas
        for i, linha in enumerate(cena["linhas"]):
            linha_s = self.fonte_texto.render(linha, True, (253, 246, 225))
            surf.blit(linha_s, (self.PANEL_W // 2 - linha_s.get_width() // 2, 76 + i * 38))

        # Contador de passo (canto superior direito)
        total = len(self.PASSOS)
        atual = min(self.passo + 1, total)
        count_s = self.fonte_count.render(f"{atual}/{total}", True, (130, 110, 70))
        surf.blit(count_s, (self.PANEL_W - count_s.get_width() - 14, 14))

        # Dica de navegação
        if not self.fading_out:
            is_ultimo = self.passo >= len(self.PASSOS) - 1
            hint_txt = "ENTER para fechar  -  ESC para pular" if is_ultimo else "ENTER para continuar  -  ESC para pular"
            hint_s = self.fonte_hint.render(hint_txt, True, (140, 120, 75))
            surf.blit(hint_s, (self.PANEL_W // 2 - hint_s.get_width() // 2, self.PANEL_H - 30))

        surf.set_alpha(alpha)
        tela.blit(surf, (self.PANEL_X, self.PANEL_Y))
