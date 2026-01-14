from pypresence import Presence
import time

class DiscordRPC:
    def __init__(self):
        self.client_id = "1461012653626621962"
        self.rpc = Presence(self.client_id)
        self.start_time = int(time.time())

    def conectar(self):
        try:
            self.rpc.connect()
        except:
            print("Discord não está aberto")

    def atualizar(self, estado, detalhes, imagem="logo"):
        try:
            self.rpc.update(
                state=estado,
                details=detalhes,
                large_image=imagem,
                large_text="Blood Vein",
                start=self.start_time
            )
        except:
            pass

    def fechar(self):
        try:
            self.rpc.clear()
            self.rpc.close()
        except:
            pass
