from pygame import *
from pygame.math import Vector2
from utils import resource_path
from som import som, musica

BASE_W = 1920
BASE_H = 1080


class Config:
    MODOS       = ["janela", "fullscreen"]
    MODOS_LABEL = ["Janela", "Fullscreen"]

    def __init__(self, screen, game):
        self.screen = screen
        self.game   = game

        self.resolucoes = [
            (800,  600),
            (1024, 768),
            (1280, 720),
            (1366, 768),
            (1600, 900),
            (1920, 1080),
        ]

        monitor_w = getattr(game, 'monitor_w', game.largura)
        monitor_h = getattr(game, 'monitor_h', game.altura)
        nativo = (monitor_w, monitor_h)
        if nativo not in self.resolucoes:
            self.resolucoes.append(nativo)
            self.resolucoes.sort()

        self.indice      = self.resolucoes.index(nativo)
        self.indice_modo = 1  # default: fullscreen

        # Volume indices: 0-20 (step 5% each)
        self.vol_sfx_idx = max(0, min(20, round(som.volume    * 20)))
        self.vol_mus_idx = max(0, min(20, round(musica.volume * 20)))

        # flag: drawn from pause (shows title) or from menu
        self.modo_pause = False

        self.fonte_titulo_cfg = font.Font(resource_path('assets/Fontes/alagard.ttf'), 80)
        self.fonte_label      = font.Font(resource_path('assets/Fontes/alagard.ttf'), 40)
        self.fonte_valor      = font.Font(resource_path('assets/Fontes/alagard.ttf'), 56)
        self.fonte_botao      = font.Font(resource_path('assets/Fontes/alagard.ttf'), 64)

        self.cor_base        = (253, 246, 225)
        self.cor_hover       = (0, 0, 0)         # usado no contexto do menu
        self.cor_hover_pause = (228, 133, 40)     # âmbar visível no fundo escuro do pause
        self.cor_label       = (180, 170, 140)

        self.espada_img = image.load(resource_path('assets/UI/Espada menu.png')).convert_alpha()
        self.espada_img = transform.scale(self.espada_img, (100, 50))

        SW = SH = 44
        self.seta_dir = transform.scale(
            image.load(resource_path('assets/UI/seta_direita.png')).convert_alpha(), (SW, SH))
        self.seta_esq = transform.scale(
            image.load(resource_path('assets/UI/seta_esquerda.png')).convert_alpha(), (SW, SH))

        # Layout — eixo x coincide com os botões do menu
        self.CX        = 600
        self.SETA_DIST = 235

        # Posições Y — 4 linhas de configuração + 2 botões
        self.Y_LBL_RES  = 305
        self.Y_RES      = 355
        self.Y_LBL_MODO = 413
        self.Y_MODO     = 463
        self.Y_SEP      = 492   # separador visual vídeo/áudio
        self.Y_LBL_SFX  = 521
        self.Y_SFX      = 571
        self.Y_LBL_MUS  = 629
        self.Y_MUS      = 679
        self.Y_APLICAR  = 749
        self.Y_VOLTAR   = 834

        SW2 = SW // 2; SH2 = SH // 2
        self._hb_res_esq  = Rect(self.CX - self.SETA_DIST - SW2, self.Y_RES  - SH2, SW, SH)
        self._hb_res_dir  = Rect(self.CX + self.SETA_DIST - SW2, self.Y_RES  - SH2, SW, SH)
        self._hb_modo_esq = Rect(self.CX - self.SETA_DIST - SW2, self.Y_MODO - SH2, SW, SH)
        self._hb_modo_dir = Rect(self.CX + self.SETA_DIST - SW2, self.Y_MODO - SH2, SW, SH)
        self._hb_sfx_esq  = Rect(self.CX - self.SETA_DIST - SW2, self.Y_SFX  - SH2, SW, SH)
        self._hb_sfx_dir  = Rect(self.CX + self.SETA_DIST - SW2, self.Y_SFX  - SH2, SW, SH)
        self._hb_mus_esq  = Rect(self.CX - self.SETA_DIST - SW2, self.Y_MUS  - SH2, SW, SH)
        self._hb_mus_dir  = Rect(self.CX + self.SETA_DIST - SW2, self.Y_MUS  - SH2, SW, SH)
        self._hb_aplicar  = Rect(self.CX - 150, self.Y_APLICAR - 42, 300, 84)
        self._hb_voltar   = Rect(self.CX - 130, self.Y_VOLTAR  - 42, 260, 84)

        # lerp hover: 0=res, 1=modo, 2=sfx, 3=mus, 4=aplicar, 5=voltar
        self.hover_esc = [Vector2(1.0, 0.0) for _ in range(6)]
        self.idx_sel   = 4
        self.ultimo_hi = -1

    # ────────────────────────────────────────────────────────────

    def _hover_idx(self, mp):
        span = self.SETA_DIST + 60
        for i, y in enumerate([self.Y_RES, self.Y_MODO, self.Y_SFX, self.Y_MUS]):
            if Rect(self.CX - span, y - 38, span * 2, 76).collidepoint(mp):
                return i
        if self._hb_aplicar.collidepoint(mp):
            return 4
        if self._hb_voltar.collidepoint(mp):
            return 5
        return -1

    def _blit_c(self, tela, texto, fonte, cor, cx, cy, sc=1.0, oy=0):
        s  = fonte.render(texto, True, cor)
        sh = fonte.render(texto, True, (50, 50, 50))
        w  = int(s.get_width()  * sc)
        h  = int(s.get_height() * sc)
        if sc != 1.0:
            s  = transform.scale(s,  (w, h))
            sh = transform.scale(sh, (w, h))
        px = cx - w // 2
        py = cy - h // 2 + int(oy)
        tela.blit(sh, (px + 3, py + 3))
        tela.blit(s,  (px, py))
        return Rect(px, py, w, h)

    # ────────────────────────────────────────────────────────────

    def tratar_clique(self, mp):
        if self._hb_res_esq.collidepoint(mp):
            self.indice = (self.indice - 1) % len(self.resolucoes)
            som.tocar("hover")
        elif self._hb_res_dir.collidepoint(mp):
            self.indice = (self.indice + 1) % len(self.resolucoes)
            som.tocar("hover")
        elif self._hb_modo_esq.collidepoint(mp):
            self.indice_modo = (self.indice_modo - 1) % len(self.MODOS)
            som.tocar("hover")
        elif self._hb_modo_dir.collidepoint(mp):
            self.indice_modo = (self.indice_modo + 1) % len(self.MODOS)
            som.tocar("hover")
        elif self._hb_sfx_esq.collidepoint(mp):
            self.vol_sfx_idx = max(0, self.vol_sfx_idx - 1)
            som.set_volume(self.vol_sfx_idx * 0.05)
            som.tocar("hover")
        elif self._hb_sfx_dir.collidepoint(mp):
            self.vol_sfx_idx = min(20, self.vol_sfx_idx + 1)
            som.set_volume(self.vol_sfx_idx * 0.05)
            som.tocar("hover")
        elif self._hb_mus_esq.collidepoint(mp):
            self.vol_mus_idx = max(0, self.vol_mus_idx - 1)
            musica.set_volume(self.vol_mus_idx * 0.05)
            som.tocar("hover")
        elif self._hb_mus_dir.collidepoint(mp):
            self.vol_mus_idx = min(20, self.vol_mus_idx + 1)
            musica.set_volume(self.vol_mus_idx * 0.05)
            som.tocar("hover")
        elif self._hb_aplicar.collidepoint(mp):
            som.tocar("click3")
            self.aplicar()
        elif self._hb_voltar.collidepoint(mp):
            som.tocar("hover")
            return "voltar"
        return None

    def proxima_resolucao(self):
        self.indice = (self.indice + 1) % len(self.resolucoes)

    def aplicar(self):
        largura, altura = self.resolucoes[self.indice]
        flags = (FULLSCREEN | HWSURFACE | DOUBLEBUF) if self.MODOS[self.indice_modo] == "fullscreen" else DOUBLEBUF

        self.game.largura = largura
        self.game.altura  = altura
        self.game.window  = display.set_mode((largura, altura), flags=flags, vsync=1)
        display.set_caption("Blood Vein")
        mouse.set_visible(False)
        self.game.scale_x = largura / BASE_W
        self.game.scale_y = altura  / BASE_H

    def desenhar(self, tela, mouse_pos):
        hi = self._hover_idx(mouse_pos)

        if hi != -1 and hi != self.ultimo_hi:
            som.tocar("hover")
            self.ultimo_hi = hi
        elif hi == -1:
            self.ultimo_hi = -1

        if hi != -1:
            self.idx_sel = hi

        for i in range(6):
            alvo = Vector2(1.1, -5) if i == self.idx_sel else Vector2(1.0, 0.0)
            self.hover_esc[i] = self.hover_esc[i].lerp(alvo, 0.1)

        # cor de hover depende do fundo (menu claro vs pause escuro)
        ch = self.cor_hover_pause if self.modo_pause else self.cor_hover

        # Título "Opções" — só no contexto do pause (no menu, "Blood Vein" já é o título)
        if self.modo_pause:
            self._blit_c(tela, "Opções", self.fonte_titulo_cfg, self.cor_base, self.CX, 220)

        # ── Labels de seção ───────────────────────────────────
        self._blit_c(tela, "Resolução",        self.fonte_label, self.cor_label, self.CX, self.Y_LBL_RES)
        self._blit_c(tela, "Modo de exibição", self.fonte_label, self.cor_label, self.CX, self.Y_LBL_MODO)

        # separador vídeo / áudio
        draw.line(tela, (120, 110, 85), (self.CX - 200, self.Y_SEP), (self.CX + 200, self.Y_SEP), 1)

        self._blit_c(tela, "Volume SFX",    self.fonte_label, self.cor_label, self.CX, self.Y_LBL_SFX)
        self._blit_c(tela, "Volume Música", self.fonte_label, self.cor_label, self.CX, self.Y_LBL_MUS)

        # ── Linha resolução ────────────────────────────────────
        sc, oy = self.hover_esc[0].x, self.hover_esc[0].y
        cor = ch if self.idx_sel == 0 else self.cor_base
        res_txt = f"{self.resolucoes[self.indice][0]} x {self.resolucoes[self.indice][1]}"
        r0 = self._blit_c(tela, res_txt, self.fonte_valor, cor, self.CX, self.Y_RES, sc, oy)
        tela.blit(self.seta_esq, self._hb_res_esq.topleft)
        tela.blit(self.seta_dir, self._hb_res_dir.topleft)

        # ── Linha modo ─────────────────────────────────────────
        sc, oy = self.hover_esc[1].x, self.hover_esc[1].y
        cor = ch if self.idx_sel == 1 else self.cor_base
        r1 = self._blit_c(tela, self.MODOS_LABEL[self.indice_modo], self.fonte_valor, cor, self.CX, self.Y_MODO, sc, oy)
        tela.blit(self.seta_esq, self._hb_modo_esq.topleft)
        tela.blit(self.seta_dir, self._hb_modo_dir.topleft)

        # ── Linha SFX ──────────────────────────────────────────
        sc, oy = self.hover_esc[2].x, self.hover_esc[2].y
        cor = ch if self.idx_sel == 2 else self.cor_base
        r2 = self._blit_c(tela, f"{self.vol_sfx_idx * 5}%", self.fonte_valor, cor, self.CX, self.Y_SFX, sc, oy)
        tela.blit(self.seta_esq, self._hb_sfx_esq.topleft)
        tela.blit(self.seta_dir, self._hb_sfx_dir.topleft)

        # ── Linha Música ───────────────────────────────────────
        sc, oy = self.hover_esc[3].x, self.hover_esc[3].y
        cor = ch if self.idx_sel == 3 else self.cor_base
        r3 = self._blit_c(tela, f"{self.vol_mus_idx * 5}%", self.fonte_valor, cor, self.CX, self.Y_MUS, sc, oy)
        tela.blit(self.seta_esq, self._hb_mus_esq.topleft)
        tela.blit(self.seta_dir, self._hb_mus_dir.topleft)

        # ── Aplicar ────────────────────────────────────────────
        sc, oy = self.hover_esc[4].x, self.hover_esc[4].y
        cor = ch if self.idx_sel == 4 else self.cor_base
        r4 = self._blit_c(tela, "Aplicar", self.fonte_botao, cor, self.CX, self.Y_APLICAR, sc, oy)
        self._hb_aplicar = r4.inflate(30, 20)

        # ── Voltar ─────────────────────────────────────────────
        sc, oy = self.hover_esc[5].x, self.hover_esc[5].y
        cor = ch if self.idx_sel == 5 else self.cor_base
        r5 = self._blit_c(tela, "Voltar", self.fonte_botao, cor, self.CX, self.Y_VOLTAR, sc, oy)
        self._hb_voltar = r5.inflate(30, 20)

        # ── Espada indicadora — só nos botões, não nas linhas com setas ──
        if self.idx_sel >= 4:
            ref = [r4, r5][self.idx_sel - 4]
            tela.blit(self.espada_img, (
                ref.left - self.espada_img.get_width() - 20,
                ref.centery - self.espada_img.get_height() // 2,
            ))
