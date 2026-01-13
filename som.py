from pygame import *
from pygame import mixer
import time
from threading import Thread
from utils import resource_path 

mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
class GerenciadorDeSom:
    def __init__(self, volume=0.1, max_channels=32):
        mixer.set_num_channels(max_channels)
        self.volume = volume
        self.max_channels = max_channels
        self.sons = {}
        self.sons_com_pitch = {}
        self.canais_ocupados = {}

        # Carrega os sons em uma thread separada para não travar o jogo
        self.carregar_sons_thread = Thread(target=self._carregar_sons, daemon=True)
        self.carregar_sons_thread.start()

    def _carregar_sons(self):
        sons_para_carregar = {
            "hover": resource_path("sons/hover.mp3"),
            "buy": resource_path("sons/compra.mp3"),
            "martelo2": resource_path("sons/AOEMartelo.mp3"),
            "arco": resource_path("sons/Arco.mp3"),
            "arco_acerto": resource_path("sons/ArcoAcerto.mp3"),
            "click2": resource_path("sons/Click2.mp3"),
            "click3": resource_path("sons/Click2.mp3"),
            "Dano1": resource_path("sons/Dano1.mp3"),
            "Dano2": resource_path("sons/Dano2.mp3"),
            "Dano3": resource_path("sons/Dano3.mp3"),
            "dash": resource_path("sons/dash.mp3"),
            "espada1": resource_path("sons/espada1.mp3"),
            "espada2": resource_path("sons/espada2.mp3"),
            "espada3": resource_path("sons/espada3.mp3"),
            "faca1": resource_path("sons/Faca1.mp3"),
            "faca2": resource_path("sons/Faca2.mp3"),
            "secon_noite": resource_path("sons/secon_noite.mp3"),
            "Inimigomorre": resource_path("sons/InimigoMorrendo.mp3"),
            "Inimigomorre2": resource_path("sons/InimigoMorrendo2.mp3"),
            "Martelo": resource_path("sons/Martelo.mp3"),
            "passar_porta": resource_path("sons/PassarPorta.mp3"),
            "Spawn": resource_path("sons/Spawn.mp3"),
            "Startar": resource_path("sons/StartNewRun.mp3"),
            "tripleshota": resource_path("sons/TripleShot.mp3"),
            "carrega_critico": resource_path("sons/CarrendoCriticoEspadaDoTita.mp3"),
        }

        for nome, caminho in sons_para_carregar.items():
            try:
                som = mixer.Sound(caminho)
                som.set_volume(self.volume)
                self.sons[nome] = som
            except Exception as e:
                print(f"Erro ao carregar som {nome}: {e}")

    def tocar(self, nome, volume=None, loops=0, fade_ms=0):
        """Toca um som com opções de volume, loops e fade-in"""
        if nome not in self.sons:
            return None



        canal = mixer.find_channel()
        if canal is None:
            canal = self._obter_canal_mais_antigo()
            if canal is None:
                return None
        if hasattr(canal, 'set_pitch'):
            canal.set_pitch(1.0)

        # Configura o volume - garante que não ultrapasse o volume global
        target_volume = self.volume if volume is None else min(volume, self.volume)
        canal.set_volume(target_volume)

        # Toca o som
        canal.play(self.sons[nome], loops, fade_ms=fade_ms)

        self.canais_ocupados[id(canal)] = {
            "canal": canal,
            "inicio": time.time(),
            "nome": nome,
            "volume": target_volume  # Armazena o volume configurado
        }

        return canal

    def _obter_canal_mais_antigo(self):
        if not self.canais_ocupados:
            return None

        id_mais_antigo = min(self.canais_ocupados.keys(),
                             key=lambda k: self.canais_ocupados[k]["inicio"])
        canal = self.canais_ocupados.pop(id_mais_antigo)["canal"]
        canal.stop()
        return canal

    def parar_todos_sons(self, fade_ms=0):
        """Para todos os sons com fade-out opcional"""
        for canal_info in list(self.canais_ocupados.values()):
            canal_info["canal"].fadeout(fade_ms)
        self.canais_ocupados.clear()

    def set_volume(self, volume):
        """Define o volume global para todos os sons"""
        self.volume = max(0.0, min(volume, 1.0))
        for som in self.sons.values():
            som.set_volume(self.volume)
        for canal_info in self.canais_ocupados.values():
            canal_info["canal"].set_volume(self.volume)

    def atualizar(self):
        """Limpa canais que terminaram de tocar"""
        for canal_id in list(self.canais_ocupados.keys()):
            if not self.canais_ocupados[canal_id]["canal"].get_busy():
                self.canais_ocupados.pop(canal_id)

    def tocar_com_pitch(self, nome, pitch=1.0, volume=None, loops=0, fade_ms=0):
        """Toca um som com pitch ajustado"""
        if nome not in self.sons:
            return None

        # Cria uma cópia do som com pitch modificado se necessário
        if pitch != 1.0:
            key = f"{nome}_{pitch}"
            if key not in self.sons_com_pitch:
                original = self.sons[nome]
                # Cria uma cópia do som (infelizmente o pygame não permite mudar pitch diretamente)
                # Como alternativa, vamos usar playback rate que tem efeito similar
                copied = mixer.Sound(buffer=original.get_raw())
                copied.set_volume(original.get_volume())
                self.sons_com_pitch[key] = copied
            som = self.sons_com_pitch[key]
        else:
            som = self.sons[nome]

        canal = mixer.find_channel()
        if canal is None:
            canal = self._obter_canal_mais_antigo()
            if canal is None:
                return None

        # Configura o volume
        target_volume = self.volume if volume is None else min(volume, self.volume)
        canal.set_volume(target_volume)

        # Configura o playback rate (efetivamente muda o pitch)
        if hasattr(canal, 'set_playback_rate'):
            canal.set_playback_rate(pitch)

        # Toca o som
        canal.play(som, loops, fade_ms=fade_ms)

        self.canais_ocupados[id(canal)] = {
            "canal": canal,
            "inicio": time.time(),
            "nome": nome,
            "volume": target_volume,
            "pitch": pitch
        }

        return canal


som = GerenciadorDeSom(volume=0.1) #0.3 dpeosi


class GerenciadorDeMusica:
    def __init__(self, volume=0.5, fade_duration=1000):
        self.volume = volume
        self.fade_duration = fade_duration  # ms para transições
        self.musica_atual = None
        self.proxima_musica = None
        self.musica_fade_out = False
        self.musica_fade_in = False
        self.fade_start_time = 0
        mixer.music.set_volume(self.volume)

    def tocar(self, caminho, loop=-1, fade_ms=None):
        """Toca música com transição suave"""
        if fade_ms is None:
            fade_ms = self.fade_duration

        if self.musica_atual == caminho and mixer.music.get_busy():
            return

        # Se já está tocando música, faz fade out antes de trocar
        if mixer.music.get_busy() and fade_ms > 0:
            self.proxima_musica = (caminho, loop)
            self.musica_fade_out = True
            self.fade_start_time = time.time()
            mixer.music.fadeout(fade_ms)
        else:
            self._tocar_musica_diretamente(caminho, loop)

    def _tocar_musica_diretamente(self, caminho, loop):
        try:
            mixer.music.load(caminho)
            mixer.music.play(loop)
            self.musica_atual = caminho
            self.proxima_musica = None
        except Exception as e:
            print(f"Erro ao carregar música: {e}")

    def atualizar(self):
        """Atualiza as transições de música"""
        if self.musica_fade_out and not mixer.music.get_busy():
            self.musica_fade_out = False
            if self.proxima_musica:
                caminho, loop = self.proxima_musica
                self._tocar_musica_diretamente(caminho, loop)
                mixer.music.set_volume(0)
                self.musica_fade_in = True
                self.fade_start_time = time.time()

        if self.musica_fade_in:
            progresso = (time.time() - self.fade_start_time) * 1000 / self.fade_duration
            if progresso >= 1.0:
                mixer.music.set_volume(self.volume)
                self.musica_fade_in = False
            else:
                mixer.music.set_volume(self.volume * progresso)

        # Garante que o volume dos efeitos sonoros não seja alterado
        som.set_volume(som.volume)

    def pausar(self):
        """Pausa a música atual"""
        mixer.music.pause()

    def retomar(self, fade_ms=None):
        """Retoma a música pausada com fade-in opcional"""
        if fade_ms is None:
            fade_ms = self.fade_duration

        mixer.music.unpause()
        if fade_ms > 0:
            mixer.music.set_volume(0)
            self.musica_fade_in = True
            self.fade_start_time = time.time()

    def parar(self, fade_ms=None):
        """Para completamente a música com fade-out opcional"""
        if fade_ms is None:
            fade_ms = self.fade_duration

        if fade_ms > 0:
            mixer.music.fadeout(fade_ms)
        else:
            mixer.music.stop()
        self.musica_atual = None

    def set_volume(self, volume, fade_ms=0):
        """Define o volume da música com transição suave"""
        self.volume = max(0.0, min(volume, 1.0))
        if fade_ms > 0:
            # Implementação de fade de volume suave
            pass  # Pode ser implementado com um sistema de atualização gradual
        else:
            mixer.music.set_volume(self.volume)


musica = GerenciadorDeMusica(volume=0.3) #0.3 depiso