import json
import networkx as nx
from random import randint,shuffle,choice
from utils import resource_path
import os


class GerenciadorAndar:
    def __init__(self):
        self.numero_andar = 1
        self.carregar_andar()



    
    def carregar_andar(self):

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        andar_path = os.path.join(data_dir, resource_path("andar_atual.json"))
        
        try:
            if not os.path.exists(andar_path):
                self.gerar_andar(1)
            with open(andar_path, 'r') as f:
                data = json.load(f)
                self.grafo = nx.node_link_graph(data)
                self.numero_andar = data.get('numero_andar', 1)
        except Exception as e:
            print(f"Erro ao carregar andar: {e}")
            self.gerar_andar(1)
            
        self.sala_atual = self.get_sala_spawn()
        self.salas_conquistadas = set()
        self.salas_visitadas = {self.sala_atual}


    def gerar_andar(self, num_andar):
        self.numero_andar = num_andar
        numsalas = randint(12,15)
        maior_distancia = -1
        sala_inicio = None
        sala_fim = None
        G = nx.Graph()


        direcoes = {
            "cima": (0, -1),
            "baixo": (0, 1),
            "esquerda": (-1, 0),
            "direita": (1, 0)
        }


        oposto = {
            "cima": "baixo",
            "baixo": "cima",
            "esquerda": "direita",
            "direita": "esquerda"
        }


        posicoes = {}  
        ocupado = set() 


        salas = [f"sala{i}" for i in range(numsalas)]
        G.add_nodes_from(salas)

        salas_conectadas = [salas[0]]
        salas_nao_conectadas = salas[1:]

        posicoes[salas[0]] = (0, 0)
        ocupado.add((0, 0))


        while salas_nao_conectadas:
            salas_disponiveis = [s for s in salas_conectadas if G.degree[s] < 3]
            if not salas_disponiveis: break
            
            s1 = choice(salas_disponiveis)
            x1, y1 = posicoes[s1]

            dir_escolhida = None

            for direcao, (dx,dy) in direcoes.items():
                nova_pos = (x1 + dx, y1 + dy)
                if nova_pos not in ocupado:
                    dir_escolhida = direcao
                    break

            if dir_escolhida is None:
                continue

            dx,dy = direcoes[dir_escolhida]
            nova_pos = (x1 + dx, y1 + dy)


            s2 = salas_nao_conectadas.pop(0)
            posicoes[s2] = nova_pos
            ocupado.add(nova_pos)

            G.add_edge(s1, s2)
            salas_conectadas.append(s2)

            if "portas" not in G.nodes[s1]:
                G.nodes[s1]["portas"] = {}
            if "portas" not in G.nodes[s2]:
                G.nodes[s2]["portas"] = {}

            G.nodes[s1]["portas"][dir_escolhida] = s2
            G.nodes[s2]["portas"][oposto[dir_escolhida]] = s1



        um = [n for n in G.nodes if G.degree[n] == 1]

        if not um:
            for sala in G.nodes:
                if G.degree[sala] == 2:
                    vizinhos = list(G.neighbors(sala))
                    if vizinhos:
                        G.remove_edge(sala, vizinhos[0])
                        break

        for sala_a in G.nodes:
            distancias = nx.single_source_shortest_path_length(G, sala_a)
            for sala_b, distancia in distancias.items():
                if distancia > maior_distancia and G.degree(sala_b)==1:
                    maior_distancia = distancia
                    sala_inicio = sala_a
                    sala_fim = sala_b


        G.nodes[sala_inicio]["tipo"] = "spawn"
        G.nodes[sala_fim]["tipo"] = "boss"

        sala_bau_candidatas = [s for s in G.nodes if s != sala_inicio and s != sala_fim]
        sala_bau = choice(sala_bau_candidatas)
        G.nodes[sala_bau]["tipo"] = "bau"

        salas_segunda = list(G.neighbors(sala_inicio))

        sala_loja_candidatas = [
            s for s in G.nodes
            if s != sala_inicio
            and s != sala_fim
            and s != sala_bau
            and s not in salas_segunda
        ]

        if not sala_loja_candidatas:
            sala_loja_candidatas = [
                s for s in G.nodes
                if s != sala_inicio and s != sala_fim and s != sala_bau
            ]

        sala_loja = choice(sala_loja_candidatas)
        G.nodes[sala_loja]["tipo"] = "loja"

        umaporta = []
        duasportas = []
        tresportas = []

        for sala in G.nodes:
            G.nodes[sala]["pos"] = list(posicoes[sala])

            grau = G.degree[sala]
            if grau == 1:
                umaporta.append(sala)
            elif grau == 2:
                duasportas.append(sala)
            elif grau == 3:
                tresportas.append(sala)

            if "tipo" not in G.nodes[sala]:
                G.nodes[sala]["tipo"] = "comum"
    
            if G.nodes[sala]["tipo"] == "bau":
                G.nodes[sala]["bau_aberto"] = False
    
            G.nodes[sala]["visitada"] = (G.nodes[sala]["tipo"] == "spawn")
            G.nodes[sala]["arquivotmx"] = None
            G.nodes[sala]["salaanterior"] = None

            vizinhos = list(G.neighbors(sala))
            G.nodes[sala]["conexoes"] = vizinhos
            if "portas" not in G.nodes[sala]:
                G.nodes[sala]["portas"] = {}


        with open(resource_path('data/andar_atual.json'), 'w') as f:
            json.dump(nx.node_link_data(G), f, ensure_ascii=False, indent=4)

        with open(resource_path('data/andar_atual.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.grafo = nx.node_link_graph(data)

       

        arquivos = [f'andar{num_andar}/{i}.tmx' for i in range(1,30)]
        shuffle(arquivos)

        i=0
        for sala in self.grafo.nodes:
            if self.grafo.nodes[sala]["tipo"] == 'spawn':
                self.grafo.nodes[sala]["arquivotmx"] = f'andar{num_andar}/spawn.tmx'
                continue
            if self.grafo.nodes[sala]["tipo"] == 'boss':
                self.grafo.nodes[sala]["arquivotmx"] = f'andar{num_andar}/boss.tmx'
                continue
            if self.grafo.nodes[sala]["tipo"] == 'loja':
                self.grafo.nodes[sala]["arquivotmx"] = f'andar{num_andar}/loja.tmx'
                continue
            arquivotmx = arquivos[i]
            self.grafo.nodes[sala]["arquivotmx"] = arquivotmx
            i+=1

        graph_data = nx.node_link_data(self.grafo)
        graph_data['numero_andar'] = self.numero_andar

        self.sala_atual = self.get_sala_spawn()
        self.salas_visitadas = {self.sala_atual}
        self.salas_conquistadas = set()

        with open(resource_path('data/andar_atual.json'), 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=4)

        



    def marcar_sala_conquistada(self, sala_id):
        self.salas_conquistadas.add(sala_id)

    def sala_foi_conquistada(self, sala_id):
        return sala_id in self.salas_conquistadas

    def get_sala_spawn(self):
        for sala in self.grafo.nodes:
            if self.grafo.nodes[sala]["tipo"] == "spawn":
                return sala
            
    def get_arquivo_atual(self):
        return self.grafo.nodes[self.sala_atual]["arquivotmx"]
    
    def get_portas_sala(self, sala):
        return self.grafo.nodes[sala].get("portas", {})

    
    def ir_para_proxima_sala(self, codigo_porta):
        porta_direcao = codigo_porta
        
        if porta_direcao in self.grafo.nodes[self.sala_atual].get("portas", {}):
            proxima_sala = self.grafo.nodes[self.sala_atual]["portas"][porta_direcao]
            self.sala_atual = proxima_sala
            self.salas_visitadas.add(proxima_sala)
            return self.grafo.nodes[proxima_sala]["arquivotmx"]
        
    def get_mapa_info(self):
        nodes = []
        
        
        for sala in self.grafo.nodes:
            node_data = self.grafo.nodes[sala]
            nodes.append({
                'id': sala,
                'tipo': node_data['tipo'],
                'visitada': sala in self.salas_visitadas,
                'atual': sala == self.sala_atual,
                'posicao': (
                    (node_data['pos'][0]) * 120 + 400,
                    (node_data['pos'][1]) * 80 + 350
                )
            })
        
        edges = []
        for origem, destino in self.grafo.edges:
            edges.append({
                'origem': origem,
                'destino': destino
            })
            
        
        return {
            'nodes': nodes,
            'edges': edges
        }

    def get_save_data(self):

        return {
            'sala_atual': self.sala_atual,
            'salas_conquistadas': list(self.salas_conquistadas),
            'salas_visitadas': list(self.salas_visitadas),
            'bau_aberto': {
                sala: self.grafo.nodes[sala].get('bau_aberto', False)
                for sala in self.grafo.nodes
                if self.grafo.nodes[sala]['tipo'] == 'bau'
            }
        }

    def load_save_data(self, data):

        self.sala_atual = data['sala_atual']
        self.salas_conquistadas = set(data['salas_conquistadas'])
        self.salas_visitadas = set(data['salas_visitadas'])
        
        for sala, aberto in data['bau_aberto'].items():
            if sala in self.grafo.nodes:
                self.grafo.nodes[sala]['bau_aberto'] = aberto