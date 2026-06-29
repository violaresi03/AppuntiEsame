# ==============================================================================
#  CHEAT SHEET GRAFI — TdP Politecnico di Torino
#  Struttura identica ai progetti d'esame reali (Baseball, Chinook, ecc.)
#
#  FILE DEL PROGETTO:
#    model/Arco.py          → dataclass Arco (t1, t2, peso)
#    database/DAO.py        → query SQL statiche
#    model/Model.py         → buildGraph + calcoli
#    controller/Controller  → handler pulsanti
#    ui/View.py             → interfaccia Flet
#    main.py                → avvio app
# ==============================================================================

# ==============================================================================
# FILE: model/Arco.py
# Rappresenta un arco del grafo. Creato nel DAO, usato nel Model.
# t1 e t2 sono i due nodi (es. teamCode, ArtistId, ecc.)
# ==============================================================================
from dataclasses import dataclass

@dataclass
class Arco:
    t1: str   # nodo 1  (adatta il tipo: str se teamCode, int se ArtistId)
    t2: str   # nodo 2
    peso: float


# ==============================================================================
# FILE: database/DAO.py
# Tutte le query SQL. Solo dati, nessun calcolo.
# Ogni metodo: apre connessione → try → query → finally chiudi tutto.
# ==============================================================================
from database.DB_connect import DBConnect
from model.Arco import Arco

class DAO():
    def __init__(self):
        pass

    # --------------------------------------------------------------------------
    # Popola il primo dropdown (es. anni, generi, stagioni...)
    # --------------------------------------------------------------------------
    @staticmethod
    def getAllYears():
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """SELECT DISTINCT year
                       FROM teams t
                       WHERE year >= %s
                       ORDER BY year ASC"""
            cursor.execute(query, (1980,))
            res = []
            for row in cursor:
                res.append(row["year"])
            return res
        except Exception as e:
            print(f"Errore getAllYears: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # --------------------------------------------------------------------------
    # Popola la ListView e il secondo dropdown (es. team per anno scelto)
    # --------------------------------------------------------------------------
    @staticmethod
    def getAllTeams(year):
        cnx = DBConnect.get_connection()
        try:
            cursor1 = cnx.cursor(dictionary=True, buffered=True)
            query = """SELECT COUNT(DISTINCT teamCode) AS totale
                       FROM teams t
                       WHERE year = %s"""
            cursor1.execute(query, (year,))
            for row in cursor1:
                totale = row["totale"]

            cursor2 = cnx.cursor(dictionary=True, buffered=True)
            query1 = """SELECT teamCode
                        FROM teams t
                        WHERE year = %s
                        GROUP BY teamCode"""
            cursor2.execute(query1, (year,))
            res = [f"Totale squadre che hanno giocato nel {year}: {totale}"]
            for row in cursor2:
                res.append(row["teamCode"])
            return res
        except Exception as e:
            print(f"Errore getAllTeams: {e}")
            return []
        finally:
            cursor1.close()
            cursor2.close()
            cnx.close()

    # --------------------------------------------------------------------------
    # Recupera i NODI del grafo
    # Restituisce lista di valori (stringhe o int) che diventano nodi
    # --------------------------------------------------------------------------
    @staticmethod
    def getAllNodes(year):
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """SELECT DISTINCT t.teamCode
                       FROM teams t
                       WHERE year >= %s
                       ORDER BY t.year ASC"""
            cursor.execute(query, (year,))
            res = []
            for row in cursor:
                res.append(row["teamCode"])
            return res
        except Exception as e:
            print(f"Errore getAllNodes: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # --------------------------------------------------------------------------
    # Recupera gli ARCHI del grafo (grafo NON ORIENTATO, con peso)
    # Restituisce lista di oggetti Arco(t1, t2, peso)
    # --------------------------------------------------------------------------
    @staticmethod
    def getAllEdges(year, idMapTeams):
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """SELECT t1.teamCode AS team1, t2.teamCode AS team2,
                              s1.totale + s2.totale AS peso
                       FROM teams t1, teams t2,
                            (SELECT teamCode, year, SUM(salary) AS totale
                             FROM salaries GROUP BY teamCode, year) s1,
                            (SELECT teamCode, year, SUM(salary) AS totale
                             FROM salaries GROUP BY teamCode, year) s2
                       WHERE t1.ID < t2.ID
                         AND t1.year = %s
                         AND t1.year = t2.year
                         AND t1.teamCode = s1.teamCode AND t1.year = s1.year
                         AND t2.teamCode = s2.teamCode AND t2.year = s2.year
                       GROUP BY t1.teamCode, t2.teamCode"""
            cursor.execute(query, (year,))
            res = []
            for row in cursor:
                if row["team1"] in idMapTeams and row["team2"] in idMapTeams:
                    res.append(Arco(idMapTeams[row["team1"]],
                                    idMapTeams[row["team2"]],
                                    row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # --------------------------------------------------------------------------
    # VARIANTE: archi per grafo ORIENTATO
    # La direzione A→B è determinata dalla logica (es. popolarità A > B)
    # La query recupera coppie + un valore numerico per decidere la direzione
    # Il modello decide la direzione, non il DAO
    # --------------------------------------------------------------------------
    @staticmethod
    def getAllEdgesDirected(year, idMapTeams):
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            # Esempio: recupera le coppie di team con la loro popolarità separata
            query = """SELECT t1.teamCode AS team1, t2.teamCode AS team2,
                              s1.totale AS peso1, s2.totale AS peso2
                       FROM teams t1, teams t2,
                            (SELECT teamCode, year, SUM(salary) AS totale
                             FROM salaries GROUP BY teamCode, year) s1,
                            (SELECT teamCode, year, SUM(salary) AS totale
                             FROM salaries GROUP BY teamCode, year) s2
                       WHERE t1.ID < t2.ID
                         AND t1.year = %s AND t1.year = t2.year
                         AND t1.teamCode = s1.teamCode AND t1.year = s1.year
                         AND t2.teamCode = s2.teamCode AND t2.year = s2.year
                       GROUP BY t1.teamCode, t2.teamCode"""
            cursor.execute(query, (year,))
            res = []
            for row in cursor:
                if row["team1"] in idMapTeams and row["team2"] in idMapTeams:
                    # Restituisce Arco con peso1 e peso2 separati per decidere
                    # la direzione nel Model
                    res.append((idMapTeams[row["team1"]],
                                idMapTeams[row["team2"]],
                                row["peso1"],
                                row["peso2"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdgesDirected: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()


# ==============================================================================
# FILE: model/Model.py
# Costruisce il grafo e fa TUTTI i calcoli.
# Nessuna query SQL qui. Riceve i dati dal DAO.
# ==============================================================================
import networkx as nx
from collections import deque

class Model:
    def __init__(self):
        self._idMapTeams = {}   # {"BOS": "BOS", "NYA": "NYA", ...}
                                # oppure {teamCode: teamCode} — serve al DAO per
                                # verificare che i team degli archi siano nel grafo
        self._graph = nx.Graph()   # grafo non orientato di default

    # --------------------------------------------------------------------------
    # Metodi che il Controller chiama per ottenere i dati dal DAO
    # (il Model fa da tramite: Controller → Model → DAO)
    # --------------------------------------------------------------------------
    def getAllYears(self):
        from database.DAO import DAO
        return DAO.getAllYears()

    def getAllTeams(self, year):
        from database.DAO import DAO
        return DAO.getAllTeams(year)

    # --------------------------------------------------------------------------
    # buildGraph — GRAFO NON ORIENTATO (nx.Graph)
    # Chiamato da handleCreaGrafo nel Controller
    # --------------------------------------------------------------------------
    def buildGraph(self, year):
        self._idMapTeams = {}
        self._graph = nx.Graph()
        from database.DAO import DAO

        # 1. NODI
        teams = DAO.getAllNodes(year)
        for t in teams:
            self._idMapTeams[t] = t
        self._graph.add_nodes_from(teams)

        # 2. ARCHI
        allEdges = DAO.getAllEdges(year, idMapTeams=self._idMapTeams)
        for e in allEdges:
            self._graph.add_edge(e.t1, e.t2, weight=e.peso)

        # Struttura interna del grafo dopo add_edge:
        # self._graph = {
        #   "BOS": {"NYA": {"weight": 1500000.0}, "CLE": {"weight": 2000000.0}},
        #   "NYA": {"BOS": {"weight": 1500000.0}, ...},
        # }

    # --------------------------------------------------------------------------
    # buildGraph — GRAFO ORIENTATO (nx.DiGraph)
    # Usa quando la direzione degli archi dipende da un valore (es. popolarità)
    # --------------------------------------------------------------------------
    def buildGraphDirected(self, year):
        self._idMapTeams = {}
        self._graph = nx.DiGraph()   # ← ORIENTATO
        from database.DAO import DAO

        # 1. NODI
        teams = DAO.getAllNodes(year)
        for t in teams:
            self._idMapTeams[t] = t
        self._graph.add_nodes_from(teams)

        # 2. ARCHI CON DIREZIONE
        allEdges = DAO.getAllEdgesDirected(year, idMapTeams=self._idMapTeams)
        for t1, t2, peso1, peso2 in allEdges:
            peso_arco = peso1 + peso2
            if peso1 > peso2:
                self._graph.add_edge(t1, t2, weight=peso_arco)
            elif peso2 > peso1:
                self._graph.add_edge(t2, t1, weight=peso_arco)
            else:
                # stessa popolarità → arco in entrambe le direzioni
                self._graph.add_edge(t1, t2, weight=peso_arco)
                self._graph.add_edge(t2, t1, weight=peso_arco)

    # --------------------------------------------------------------------------
    # getGraph — rende il grafo accessibile al Controller
    # --------------------------------------------------------------------------
    def getGraph(self):
        return self._graph

    # --------------------------------------------------------------------------
    # getGraphDetails — numero nodi e archi
    # --------------------------------------------------------------------------
    def getGraphDetails(self):
        return len(self._graph.nodes), len(self._graph.edges)

    # ==========================================================================
    # CALCOLI SUL GRAFO
    # Tutti i metodi qui sotto vengono chiamati dal Controller dopo buildGraph
    # ==========================================================================

    # --------------------------------------------------------------------------
    # STATISTICHE BASE
    # --------------------------------------------------------------------------
    def getNumNodi(self):
        return self._graph.number_of_nodes()

    def getNumArchi(self):
        return self._graph.number_of_edges()

    def getNomeNodo(self, node_id):
        """Legge l'attributo 'name' di un nodo (se esiste), altrimenti usa node_id."""
        return self._graph.nodes[node_id].get("name", str(node_id))

    # --------------------------------------------------------------------------
    # TOP N ARCHI PER PESO (decrescente)
    # Usato per: "mostra i 5 archi con peso maggiore"
    # --------------------------------------------------------------------------
    def getTopArchi(self, n=5):
        """
        Restituisce lista di tuple (t1, t2, peso) ordinate per peso decrescente.
        Controller: for t1, t2, peso in self._model.getTopArchi(5): ...
        """
        archi = [(u, v, d["weight"]) for u, v, d in self._graph.edges(data=True)]
        archi.sort(key=lambda x: x[2], reverse=True)
        return archi[:n]

    # --------------------------------------------------------------------------
    # INFLUENZA (solo DiGraph)
    # Influenza = somma pesi archi uscenti − somma pesi archi entranti
    # Usato per: "artista/team con maggiore influenza"
    # --------------------------------------------------------------------------
    def getMaxInfluenza(self):
        """
        Restituisce (nodo, valore_influenza) per il nodo con influenza massima.
        SOLO per DiGraph.
        Controller: nodo, val = self._model.getMaxInfluenza()
        """
        max_nodo = None
        max_val = float('-inf')
        for node in self._graph.nodes():
            uscenti = sum(d["weight"] for _, _, d in self._graph.out_edges(node, data=True))
            entranti = sum(d["weight"] for _, _, d in self._graph.in_edges(node, data=True))
            influenza = uscenti - entranti
            if influenza > max_val:
                max_val = influenza
                max_nodo = node
        return max_nodo, max_val

    # --------------------------------------------------------------------------
    # NODO CON GRADO MASSIMO
    # Usato per: "team/artista più connesso"
    # --------------------------------------------------------------------------
    def getMaxDegree(self):
        """
        Restituisce (nodo, grado) per il nodo con più archi.
        Per DiGraph: grado = in_degree + out_degree.
        Controller: nodo, grado = self._model.getMaxDegree()
        """
        degrees = dict(self._graph.degree())
        max_nodo = max(degrees, key=lambda n: degrees[n])
        return max_nodo, degrees[max_nodo]

    # --------------------------------------------------------------------------
    # VICINI DI UN NODO con peso arco (già nel controller del baseball)
    # Usato da handleDettagli
    # --------------------------------------------------------------------------
    def getViciniOrdinati(self, nodo):
        """
        Restituisce lista di tuple (vicino, peso) ordinata per peso decrescente.
        Per DiGraph: usa neighbors() che dà i successori.
        Controller: vicini = self._model.getViciniOrdinati(squadra)
        """
        vicini = []
        for vicino in self._graph.neighbors(nodo):
            peso = self._graph[nodo][vicino]["weight"]
            vicini.append((vicino, peso))
        vicini.sort(key=lambda x: x[1], reverse=True)
        return vicini

    # --------------------------------------------------------------------------
    # SHORTEST PATH — cammino minimo (numero archi, non pesato)
    # Usato per: "percorso più breve tra A e B"
    # --------------------------------------------------------------------------
    def getShortestPath(self, source, target):
        """
        Restituisce lista di nodi del cammino minimo, o [] se non esiste.
        Controller: path = self._model.getShortestPath(nodo1, nodo2)
        """
        try:
            return nx.shortest_path(self._graph, source=source, target=target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    # --------------------------------------------------------------------------
    # SHORTEST PATH PESATO — cammino di peso minimo
    # Usato per: "percorso con costo/distanza minore tra A e B"
    # --------------------------------------------------------------------------
    def getShortestPathPesato(self, source, target):
        """
        Restituisce (lista_nodi, peso_totale) del cammino di peso minimo.
        Controller: path, peso = self._model.getShortestPathPesato(n1, n2)
        """
        try:
            path = nx.shortest_path(self._graph, source=source,
                                    target=target, weight="weight")
            lunghezza = nx.shortest_path_length(self._graph, source=source,
                                                target=target, weight="weight")
            return path, lunghezza
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [], float('inf')

    # --------------------------------------------------------------------------
    # CAMMINO PIÙ LUNGO da un nodo sorgente (ricerca esaustiva DFS)
    # Usato per: "percorso di lunghezza massima partendo da X"
    # --------------------------------------------------------------------------
    def getLongestPath(self, source):
        """
        Cammino semplice di lunghezza massima (numero di archi) da source.
        Ricerca esaustiva con DFS (ricerca su profondità) ricorsiva — OK per grafi d'esame (< 100 nodi).
        Restituisce lista di nodi.
        Controller: path = self._model.getLongestPath(nodo)
        """
        if source not in self._graph:
            return []
        risultato = {"path": [source]}

        def dfs(corrente, visitati, cammino):
            esteso = False
            for vicino in self._graph.neighbors(corrente):
                if vicino not in visitati:
                    esteso = True
                    visitati.add(vicino)
                    cammino.append(vicino)
                    dfs(vicino, visitati, cammino)
                    cammino.pop()
                    visitati.remove(vicino)
            if not esteso and len(cammino) > len(risultato["path"]):
                risultato["path"] = list(cammino)

        dfs(source, {source}, [source])
        return risultato["path"]

    # --------------------------------------------------------------------------
    # CAMMINO PIÙ LUNGO CON PESI STRETTAMENTE CRESCENTI
    # Usato per: "cammino semplice tale che ogni arco successivo abbia peso > precedente"
    # (Punto 2c della simulazione Chinook 19/05/2026)
    # --------------------------------------------------------------------------
    def getLongestPathPesiCrescenti(self, source):
        """
        Cammino semplice di lunghezza massima con pesi strettamente crescenti.
        Restituisce lista di nodi.
        Controller: path = self._model.getLongestPathPesiCrescenti(nodo)
        """
        if source not in self._graph:
            return []
        risultato = {"path": [source]}

        def dfs(corrente, visitati, cammino, ultimo_peso):
            esteso = False
            for vicino, dati in self._graph[corrente].items():
                peso = dati.get("weight", 1)
                if vicino not in visitati and peso > ultimo_peso:
                    esteso = True
                    visitati.add(vicino)
                    cammino.append(vicino)
                    dfs(vicino, visitati, cammino, peso)
                    cammino.pop()
                    visitati.remove(vicino)
            if not esteso and len(cammino) > len(risultato["path"]):
                risultato["path"] = list(cammino)

        dfs(source, {source}, [source], ultimo_peso=float('-inf'))
        return risultato["path"]

    # --------------------------------------------------------------------------
    # CAMMINO PIÙ LUNGO SU DAG (Directed Acyclic Graph): non sono possibili cicli chiusi — metodo nx diretto
    # Usato solo se il grafo è garantito aciclico
    # --------------------------------------------------------------------------
    def getLongestPathDAG(self):
        """
        Cammino più lungo su DAG. Lancia eccezione se ci sono cicli.
        Restituisce lista di nodi.
        """
        try:
            return nx.dag_longest_path(self._graph)
        except nx.NetworkXUnfeasible:
            return []   # grafo con cicli, non è un DAG

    # --------------------------------------------------------------------------
    # CONNETTIVITÀ
    # --------------------------------------------------------------------------
    def isConnesso(self):
        """
        True se il grafo è connesso.
        Per DiGraph: controlla connettività debole (ignora direzione).
        """
        if isinstance(self._graph, nx.DiGraph):
            return nx.is_weakly_connected(self._graph)
        return nx.is_connected(self._graph)

    def isFortementeConnesso(self):
        """True se DiGraph è fortemente connesso (da ogni nodo raggiungi tutti)."""
        if not isinstance(self._graph, nx.DiGraph):
            return False
        return nx.is_strongly_connected(self._graph)

    def getComponentiConnesse(self):
        """
        Lista di set di nodi per ogni componente connessa.
        Per DiGraph: componenti debolmente connesse.
        """
        if isinstance(self._graph, nx.DiGraph):
            return list(nx.weakly_connected_components(self._graph))
        return list(nx.connected_components(self._graph))

    def getComponentiFortementeConnesse(self):
        """Lista di set per componenti fortemente connesse (solo DiGraph)."""
        if not isinstance(self._graph, nx.DiGraph):
            return []
        return list(nx.strongly_connected_components(self._graph))

    # --------------------------------------------------------------------------
    # BFS MANUALE (come nelle slide TdP — con coda deque)
    # Usato per: implementare la visita o ottenere l'ordine di visita
    # --------------------------------------------------------------------------
    def bfsManuale(self, source):
        """
        BFS con deque. Restituisce lista di nodi nell'ordine di visita.
        Controller: ordine = self._model.bfsManuale(nodo)
        """
        if source not in self._graph:
            return []
        visitati = {source}
        coda = deque([source])
        ordine = []
        while coda:
            nodo = coda.popleft()
            ordine.append(nodo)
            for vicino in self._graph.neighbors(nodo):
                if vicino not in visitati:
                    visitati.add(vicino)
                    coda.append(vicino)
        return ordine

    def bfsLivelli(self, source):
        """
        BFS per livelli. Restituisce dict {livello: [lista_nodi]}.
        Corrisponde a S0={source}, S1={vicini di source}, S2=... delle slide.
        """
        if source not in self._graph:
            return {}
        livelli = {}
        visitati = {source}
        livello_corrente = [source]
        l = 0
        while livello_corrente:
            livelli[l] = livello_corrente
            prossimo = []
            for nodo in livello_corrente:
                for vicino in self._graph.neighbors(nodo):
                    if vicino not in visitati:
                        visitati.add(vicino)
                        prossimo.append(vicino)
            livello_corrente = prossimo
            l += 1
        return livelli

    # --------------------------------------------------------------------------
    # DFS MANUALE (come nelle slide TdP — ricorsiva)
    # --------------------------------------------------------------------------
    def dfsManuale(self, source):
        """
        DFS ricorsiva. Restituisce lista di nodi nell'ordine di visita.
        Controller: ordine = self._model.dfsManuale(nodo)
        """
        if source not in self._graph:
            return []
        visitati = set()
        ordine = []

        def _dfs(v):
            visitati.add(v)
            ordine.append(v)
            for w in self._graph.neighbors(v):
                if w not in visitati:
                    _dfs(w)

        _dfs(source)
        return ordine

    # --------------------------------------------------------------------------
    # METODI NetworkX PRONTI — traversal
    # Usali quando il professore non chiede implementazione manuale
    # --------------------------------------------------------------------------
    def bfsEdgesNx(self, source):
        """Archi nell'ordine BFS. → list of (u, v)"""
        return list(nx.bfs_edges(self._graph, source))

    def bfsTreeNx(self, source):
        """Albero BFS radicato in source. → DiGraph"""
        return nx.bfs_tree(self._graph, source)

    def bfsLayersNx(self, source):
        """Livelli BFS come lista di liste. → [[S0], [S1], [S2], ...]"""
        return list(nx.bfs_layers(self._graph, source))

    def dfsEdgesNx(self, source):
        """Archi nell'ordine DFS. → list of (u, v)"""
        return list(nx.dfs_edges(self._graph, source))

    def dfsPreorderNx(self, source):
        """Nodi in pre-ordine DFS (ordine di scoperta). → list"""
        return list(nx.dfs_preorder_nodes(self._graph, source))

    def dfsPostorderNx(self, source):
        """Nodi in post-ordine DFS (ordine di chiusura). → list"""
        return list(nx.dfs_postorder_nodes(self._graph, source))

    def dfsTreeNx(self, source):
        """Albero DFS radicato in source. → DiGraph"""
        return nx.dfs_tree(self._graph, source)

    def discendentiADistanza(self, source, distance):
        """Tutti i nodi esattamente a 'distance' hop da source. → set"""
        return nx.descendants_at_distance(self._graph, source, distance)

    # --------------------------------------------------------------------------
    # CICLI
    # --------------------------------------------------------------------------
    def haCicli(self):
        """True se il grafo contiene almeno un ciclo."""
        if isinstance(self._graph, nx.DiGraph):
            return not nx.is_directed_acyclic_graph(self._graph)
        try:
            nx.find_cycle(self._graph)
            return True
        except nx.NetworkXNoCycle:
            return False

    # --------------------------------------------------------------------------
    # MINIMUM SPANNING TREE (solo Graph non diretto)
    # --------------------------------------------------------------------------
    def getMST(self):
        """Albero di copertura minimo. Restituisce un Graph."""
        if isinstance(self._graph, nx.DiGraph):
            return None
        try:
            return nx.minimum_spanning_tree(self._graph, weight="weight")
        except Exception as e:
            print(f"Errore getMST: {e}")
            return None

    # --------------------------------------------------------------------------
    # DIAMETRO E CENTRO (solo se grafo connesso)
    # --------------------------------------------------------------------------
    def getDiametro(self):
        """Massima distanza tra qualsiasi coppia di nodi. -1 se non connesso."""
        if not self.isConnesso():
            return -1
        try:
            return nx.diameter(self._graph)
        except Exception:
            return -1

    def getCentro(self):
        """Nodi con eccentricità minima. → list"""
        if not self.isConnesso():
            return []
        try:
            return nx.center(self._graph)
        except Exception:
            return []

    # --------------------------------------------------------------------------
    # UTILITY — converti percorso in stringa leggibile
    # --------------------------------------------------------------------------
    def pathToString(self, path):
        """
        Converte lista di nodi in stringa "A → B → C".
        Se i nodi hanno attributo 'name', lo usa; altrimenti usa il nodo stesso.
        """
        if not path:
            return "Nessun percorso trovato"
        nomi = []
        for n in path:
            if n in self._graph.nodes and "name" in self._graph.nodes[n]:
                nomi.append(self._graph.nodes[n]["name"])
            else:
                nomi.append(str(n))
        return " → ".join(nomi)


# ==============================================================================
# FILE: controller/Controller.py
# Gestisce gli eventi Flet. Chiama Model (che chiama DAO).
# Aggiorna la View con i risultati.
# ==============================================================================
import flet as ft

class Controller:
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._choiceYear = None      # valore del primo dropdown
        self._choiceSquadra = None   # valore del secondo dropdown
        self._graph = None           # grafo salvato dopo buildGraph

    # --------------------------------------------------------------------------
    # DROPDOWN 1 — on_change: salva la scelta e popola il secondo dropdown
    # --------------------------------------------------------------------------
    def _choiceDDYear(self, e):
        self._choiceYear = e.control.value
        self.fillDDsTeam(self._choiceYear)
        print(f"Anno selezionato: {self._choiceYear}")

    # --------------------------------------------------------------------------
    # Popola il primo dropdown all'avvio (chiamato da View.load_interface)
    # --------------------------------------------------------------------------
    def fillDDsYear(self):
        years = self._model.getAllYears()
        yearsoptions = list(map(lambda x: ft.dropdown.Option(x), years))
        self._view._ddAnno.options = yearsoptions
        self._view.update_page()

    # --------------------------------------------------------------------------
    # Popola ListView + secondo dropdown in base all'anno scelto
    # --------------------------------------------------------------------------
    def fillDDsTeam(self, year):
        teams = self._model.getAllTeams(year)
        self._view._txtOutSquadre.controls.clear()
        for team in teams:
            self._view._txtOutSquadre.controls.append(ft.Text(str(team)))
        teamsoptions = list(map(lambda x: ft.dropdown.Option(x), teams))
        self._view._ddSquadra.options = teamsoptions[1:]  # [1:] salta la prima riga (il totale)
        self._view.update_page()

    # --------------------------------------------------------------------------
    # PULSANTE "Crea Grafo"
    # --------------------------------------------------------------------------
    def handleCreaGrafo(self, e):
        if self._choiceYear is None:
            self._view._txt_result.controls.clear()
            self._view._txt_result.controls.append(ft.Text("Seleziona un anno!", color="red"))
            self._view.update_page()
            return

        self._model.buildGraph(self._choiceYear)
        self._graph = self._model.getGraph()

        # Mostra numero nodi e archi
        nNodi, nArchi = self._model.getGraphDetails()
        self._view._txt_result.controls.clear()
        self._view._txt_result.controls.append(ft.Text(f"Grafo creato: {nNodi} nodi, {nArchi} archi"))

        # Mostra top 5 archi per peso
        self._view._txt_result.controls.append(ft.Text("Top 5 archi per peso:"))
        for t1, t2, peso in self._model.getTopArchi(5):
            self._view._txt_result.controls.append(ft.Text(f"  {t1} → {t2} : {peso}"))

        # Se DiGraph: mostra nodo con maggiore influenza
        if hasattr(self._graph, 'out_edges'):  # è un DiGraph
            nodo, val = self._model.getMaxInfluenza()
            self._view._txt_result.controls.append(
                ft.Text(f"Nodo più influente: {nodo} (influenza: {val})")
            )

        self._view.update_page()

    # --------------------------------------------------------------------------
    # PULSANTE "Dettagli" — vicini di un nodo selezionato
    # --------------------------------------------------------------------------
    def handleDettagli(self, e):
        squadra = self._view._ddSquadra.value
        if squadra is None:
            self._view._txt_result.controls.clear()
            self._view._txt_result.controls.append(ft.Text("Seleziona una squadra!", color="red"))
            self._view.update_page()
            return

        if self._graph is None:
            self._view._txt_result.controls.clear()
            self._view._txt_result.controls.append(ft.Text("Prima crea il grafo!", color="red"))
            self._view.update_page()
            return

        vicini = self._model.getViciniOrdinati(squadra)
        self._view._txt_result.controls.clear()
        self._view._txt_result.controls.append(ft.Text(f"Vicini di {squadra}:"))
        for vicino, peso in vicini:
            self._view._txt_result.controls.append(ft.Text(f"  {vicino}: {peso}"))
        self._view.update_page()

    # --------------------------------------------------------------------------
    # PULSANTE "Percorso" — cammino più lungo / più breve / con pesi crescenti
    # Adatta in base alla richiesta dell'esame
    # --------------------------------------------------------------------------
    def handlePercorso(self, e):
        squadra = self._view._ddSquadra.value
        if squadra is None:
            self._view._txt_result.controls.clear()
            self._view._txt_result.controls.append(ft.Text("Seleziona una squadra!", color="red"))
            self._view.update_page()
            return

        if self._graph is None:
            self._view._txt_result.controls.clear()
            self._view._txt_result.controls.append(ft.Text("Prima crea il grafo!", color="red"))
            self._view.update_page()
            return

        # --- SCEGLI UNO DEI SEGUENTI IN BASE ALLA RICHIESTA D'ESAME ---

        # A) Cammino più lungo da source (generico)
        path = self._model.getLongestPath(squadra)

        # B) Cammino più lungo con pesi crescenti
        # path = self._model.getLongestPathPesiCrescenti(squadra)

        # C) Cammino minimo tra due nodi (serve un secondo nodo dal dropdown)
        # target = self._view._ddTarget.value
        # path = self._model.getShortestPath(squadra, target)

        # D) Cammino minimo pesato
        # path, peso = self._model.getShortestPathPesato(squadra, target)

        self._view._txt_result.controls.clear()
        if not path or len(path) < 2:
            self._view._txt_result.controls.append(ft.Text("Nessun percorso trovato."))
        else:
            path_str = self._model.pathToString(path)
            self._view._txt_result.controls.append(
                ft.Text(f"Cammino ({len(path)-1} archi): {path_str}")
            )
        self._view.update_page()


# ==============================================================================
# FILE: ui/View.py  (struttura identica al tuo progetto baseball)
# ==============================================================================
class View(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self._page.title = "TdP - Esame"
        self._page.horizontal_alignment = 'CENTER'
        self._page.theme_mode = ft.ThemeMode.LIGHT
        self._controller = None

    def load_interface(self):
        self._title = ft.Text("TdP - Esame", color="blue", size=24)

        # Dropdown 1 (es. Anno / Genere)
        self._ddAnno = ft.Dropdown(
            label="Anno", width=200,
            on_change=self._controller._choiceDDYear
        )
        self._controller.fillDDsYear()

        row1 = ft.Row([
            ft.Container(self._title, width=500),
            ft.Container(self._ddAnno, width=250)
        ], alignment=ft.MainAxisAlignment.CENTER)

        # ListView risultati query
        self._txtOutSquadre = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=False)
        cont = ft.Container(self._txtOutSquadre, width=300, height=200,
                            alignment=ft.alignment.top_left, bgcolor="#deeded")

        self._btnCreaGrafo = ft.ElevatedButton(
            text="Crea Grafo", on_click=self._controller.handleCreaGrafo
        )
        row2 = ft.Row([cont, self._btnCreaGrafo],
                      alignment=ft.MainAxisAlignment.CENTER,
                      vertical_alignment=ft.CrossAxisAlignment.END)

        # Dropdown 2 (es. Squadra / Artista)
        self._ddSquadra = ft.Dropdown(label="Squadra", width=200)
        self._btnDettagli = ft.ElevatedButton(
            text="Dettagli", on_click=self._controller.handleDettagli
        )
        self._btnPercorso = ft.ElevatedButton(
            text="Percorso", on_click=self._controller.handlePercorso
        )
        row3 = ft.Row([
            ft.Container(self._ddSquadra, width=250),
            ft.Container(self._btnDettagli, width=250),
            ft.Container(self._btnPercorso, width=250)
        ], alignment=ft.MainAxisAlignment.CENTER)

        self._page.controls.append(row1)
        self._page.controls.append(row2)
        self._page.controls.append(row3)

        # ListView output risultati
        self._txt_result = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self._page.controls.append(
            ft.Container(self._txt_result, bgcolor="#deeded", height=350)
        )
        self._page.update()

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, controller):
        self._controller = controller

    def set_controller(self, controller):
        self._controller = controller

    def update_page(self):
        self._page.update()


# ==============================================================================
# FILE: main.py
# ==============================================================================
# import flet as ft
# from ui.View import View
# from model.Model import Model
# from controller.Controller import Controller
#
# def main(page: ft.Page):
#     model = Model()
#     view = View(page)
#     controller = Controller(view, model)
#     view.controller = controller
#     view.load_interface()
#
# ft.app(target=main)


# ==============================================================================
# QUICK REFERENCE — cosa usare per ogni domanda d'esame
# ==============================================================================
#
#  DOMANDA                                   FILE      METODO
#  ──────────────────────────────────────────────────────────────────────────────
#  Numero nodi / archi                       Model     getGraphDetails()
#  Top N archi per peso decrescente          Model     getTopArchi(n)
#  Nodo con max influenza (DiGraph)          Model     getMaxInfluenza()
#  Nodo con max degree                       Model     getMaxDegree()
#  Vicini di un nodo + peso, ordinati        Model     getViciniOrdinati(nodo)
#  Cammino minimo (num. archi)               Model     getShortestPath(s, t)
#  Cammino minimo pesato                     Model     getShortestPathPesato(s, t)
#  Cammino più lungo da source               Model     getLongestPath(source)
#  Cammino più lungo pesi crescenti          Model     getLongestPathPesiCrescenti(source)
#  Cammino più lungo su DAG                  Model     getLongestPathDAG()
#  Grafo connesso?                           Model     isConnesso()
#  Grafo fortemente connesso?                Model     isFortementeConnesso()
#  Componenti connesse                       Model     getComponentiConnesse()
#  Componenti fortemente connesse            Model     getComponentiFortementeConnesse()
#  BFS manuale (ordine visita)               Model     bfsManuale(source)
#  BFS per livelli S0, S1, S2...            Model     bfsLivelli(source)
#  DFS manuale (ordine visita)               Model     dfsManuale(source)
#  BFS con nx (archi)                        Model     bfsEdgesNx(source)
#  BFS albero                                Model     bfsTreeNx(source)
#  BFS livelli con nx                        Model     bfsLayersNx(source)
#  DFS con nx (archi)                        Model     dfsEdgesNx(source)
#  DFS pre-ordine con nx                     Model     dfsPreorderNx(source)
#  DFS post-ordine con nx                    Model     dfsPostorderNx(source)
#  DFS albero                                Model     dfsTreeNx(source)
#  Nodi a distanza K da source               Model     discendentiADistanza(s, K)
#  Il grafo ha cicli?                        Model     haCicli()
#  Albero minimo (MST, solo Graph)           Model     getMST()
#  Diametro del grafo                        Model     getDiametro()
#  Centro del grafo                          Model     getCentro()
#  Converti path in stringa                  Model     pathToString(path)
#
#  TIPO GRAFO:
#    nx.Graph()   → non orientato   (buildGraph)
#    nx.DiGraph() → orientato       (buildGraphDirected)
#    Peso arco: add_edge(u, v, weight=valore)
#
#  ERRORI DA GESTIRE SEMPRE:
#    • dropdown.value è None → controlla prima di usare
#    • self._graph è None   → controlla prima di usare
#    • nodo non nel grafo   → "if nodo not in self._graph"
#    • percorso inesistente → except nx.NetworkXNoPath
#    • DB offline           → try/except/finally in ogni metodo DAO

























AGGIUNTA
# ==============================================================================
#  CHEAT SHEET GRAFI — TdP Politecnico di Torino
#  Struttura identica ai progetti d'esame reali (Baseball, Chinook, ecc.)
#
#  FILE DEL PROGETTO:
#    model/Arco.py          → dataclass Arco (t1, t2, peso)
#    database/DAO.py        → query SQL statiche
#    model/Model.py         → buildGraph + calcoli
#    controller/Controller  → handler pulsanti
#    ui/View.py             → interfaccia Flet
#    main.py                → avvio app
# ==============================================================================

# ==============================================================================
# FILE: model/Arco.py
# ==============================================================================
from dataclasses import dataclass

@dataclass
class Arco:
    t1: str
    t2: str
    peso: float


# ==============================================================================
# FILE: model/Model.py  — SEZIONE CALCOLI SUL GRAFO
# (solo i metodi aggiuntivi rispetto al cheat sheet base)
# ==============================================================================
import networkx as nx
from collections import deque

class Model:
    def __init__(self):
        self._idMapTeams = {}
        self._graph = nx.Graph()

    # --------------------------------------------------------------------------
    # SHORTEST PATH (già presenti nel cheat sheet originale — riportati per completezza)
    # --------------------------------------------------------------------------
    def getShortestPath(self, source, target):
        try:
            return nx.shortest_path(self._graph, source=source, target=target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def getShortestPathPesato(self, source, target):
        try:
            path = nx.shortest_path(self._graph, source=source,
                                    target=target, weight="weight")
            lunghezza = nx.shortest_path_length(self._graph, source=source,
                                                target=target, weight="weight")
            return path, lunghezza
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [], float('inf')

    # ==========================================================================
    # *** NUOVI METODI DAL PDF — SHORTEST PATH ALGORITHMS ***
    # ==========================================================================

    # --------------------------------------------------------------------------
    # FLOYD-WARSHALL — All-Pairs Shortest Path (AP-SP)
    # Complessità: O(V^3)
    # Funziona con pesi negativi MA non con cicli negativi
    # Usato per: "trova il cammino minimo tra TUTTE le coppie di nodi"
    # --------------------------------------------------------------------------
    def getFloydWarshall(self):
        """
        Restituisce dizionario annidato dist[u][v] = peso cammino minimo da u a v.
        Se dist[u][v] == inf, non esiste cammino.
        Controller:
            dist = self._model.getFloydWarshall()
            peso = dist[nodo1][nodo2]   # peso del cammino minimo
        """
        try:
            fw = nx.floyd_warshall(self._graph, weight="weight")
            return {u: dict(v) for u, v in fw.items()}
        except Exception as e:
            print(f"Errore getFloydWarshall: {e}")
            return {}

    def getFloydWarshallPath(self, source, target):
        """
        Restituisce (lista_nodi, peso) del cammino minimo tra source e target
        usando Floyd-Warshall (predecessori + distanze).
        Controller: path, peso = self._model.getFloydWarshallPath(n1, n2)
        """
        try:
            pred, dist = nx.floyd_warshall_predecessor_and_distance(
                self._graph, weight="weight"
            )
            if target not in dist.get(source, {}):
                return [], float('inf')
            path = nx.reconstruct_path(source, target, pred)
            return path, dist[source][target]
        except (nx.NodeNotFound, KeyError):
            return [], float('inf')
        except Exception as e:
            print(f"Errore getFloydWarshallPath: {e}")
            return [], float('inf')

    # --------------------------------------------------------------------------
    # BELLMAN-FORD-MOORE — Single-Source Shortest Path (SS-SP)
    # Complessità: O(V * E)
    # Funziona con pesi negativi MA non con cicli negativi (li rileva)
    # Usato per: cammino minimo da sorgente unica, anche con archi negativi
    # --------------------------------------------------------------------------
    def getBellmanFordPath(self, source, target):
        """
        Cammino minimo da source a target con Bellman-Ford.
        Gestisce pesi negativi; rileva cicli negativi.
        Controller: path, peso = self._model.getBellmanFordPath(s, t)
        """
        try:
            path = nx.bellman_ford_path(self._graph, source, target,
                                        weight="weight")
            lunghezza = nx.bellman_ford_path_length(self._graph, source, target,
                                                    weight="weight")
            return path, lunghezza
        except nx.NetworkXUnfeasible:
            print("Ciclo negativo rilevato nel grafo!")
            return [], float('inf')
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [], float('inf')

    def getAllPairsBellmanFord(self):
        """
        Tutti i cammini minimi tra tutte le coppie (AP-SP) con Bellman-Ford.
        Restituisce iteratore (source, {target: [path]}).
        Complessità: O(V^2 * E)
        Controller:
            for source, paths in self._model.getAllPairsBellmanFord():
                path_to_t = paths[target]
        """
        try:
            return dict(nx.all_pairs_bellman_ford_path(self._graph, weight="weight"))
        except nx.NetworkXUnfeasible:
            print("Ciclo negativo rilevato!")
            return {}

    # --------------------------------------------------------------------------
    # DIJKSTRA — Single-Source Shortest Path (SS-SP)
    # Complessità: O(E + V * log V)
    # NON funziona con pesi negativi
    # NetworkX usa Dijkstra internamente in nx.shortest_path con weight=
    # Usato per: cammino di peso minimo (pesi tutti >= 0)
    # --------------------------------------------------------------------------
    def getDijkstraPath(self, source, target):
        """
        Cammino minimo pesato con Dijkstra (alias esplicito).
        Equivalente a getShortestPathPesato ma rende esplicito l'algoritmo.
        Controller: path, peso = self._model.getDijkstraPath(s, t)
        """
        try:
            path = nx.dijkstra_path(self._graph, source, target, weight="weight")
            lunghezza = nx.dijkstra_path_length(self._graph, source, target,
                                                weight="weight")
            return path, lunghezza
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return [], float('inf')

    def getAllPairsDijkstra(self):
        """
        Tutti i cammini minimi tra tutte le coppie con Dijkstra (AP-SP).
        Complessità: O(V * E + V^2 * log V)
        Controller:
            paths = self._model.getAllPairsDijkstra()
            path = paths[source][target]
        """
        try:
            return dict(nx.all_pairs_dijkstra_path(self._graph, weight="weight"))
        except Exception as e:
            print(f"Errore getAllPairsDijkstra: {e}")
            return {}

    # --------------------------------------------------------------------------
    # CONFRONTO ALGORITMI — QUALE USARE?
    #
    #  ALGORITMO          | PROBLEMA | COMPLESSITÀ         | LIMITAZIONE
    #  -------------------|----------|---------------------|------------------
    #  Floyd-Warshall     | AP-SP    | O(V^3)              | No cicli negativi
    #  Bellman-Ford       | SS-SP    | O(V * E)            | No cicli negativi
    #  Bellman-Ford x V   | AP-SP    | O(V^2 * E)          | No cicli negativi
    #  Dijkstra           | SS-SP    | O(E + V * log V)    | No archi negativi
    #  Dijkstra x V       | AP-SP    | O(V*E + V^2*log V)  | No archi negativi
    #  BFS                | SS-SP    | O(V + E)            | Solo non pesato
    #
    #  REGOLA PRATICA PER L'ESAME:
    #  - Pesi positivi, un nodo sorgente  → Dijkstra  (nx.dijkstra_path)
    #  - Pesi positivi, tutte le coppie  → Floyd-Warshall (nx.floyd_warshall)
    #  - Pesi negativi presenti           → Bellman-Ford
    #  - Grafo non pesato                 → BFS (nx.shortest_path senza weight)
    # --------------------------------------------------------------------------

    # ==========================================================================
    # *** NUOVI METODI DAL PDF — CICLI ***
    # ==========================================================================

    # --------------------------------------------------------------------------
    # CICLI EULERIANI — Hierholzer's algorithm
    # Un ciclo euleriano visita ogni ARCO esattamente una volta
    # Condizione: grafo connesso + tutti i nodi hanno grado PARI
    # --------------------------------------------------------------------------
    def isEulerian(self):
        """
        True se il grafo ha un ciclo euleriano (tutti i nodi hanno grado pari).
        Controller: if self._model.isEulerian(): ...
        """
        return nx.is_eulerian(self._graph)

    def isSemiEulerian(self):
        """
        True se il grafo ha un cammino euleriano (esattamente 2 nodi con grado dispari).
        Controller: if self._model.isSemiEulerian(): ...
        """
        return nx.is_semieulerian(self._graph)

    def hasEulerianPath(self):
        """
        True se esiste un cammino euleriano (percorre ogni arco una volta).
        Controller: if self._model.hasEulerianPath(): ...
        """
        return nx.has_eulerian_path(self._graph)

    def getEulerianCircuit(self, source=None):
        """
        Restituisce lista di archi (u, v) del circuito euleriano.
        Il grafo deve essere euleriano (isEulerian() == True).
        Controller:
            circuit = self._model.getEulerianCircuit()
            for u, v in circuit:
                print(f"{u} → {v}")
        """
        try:
            return list(nx.eulerian_circuit(self._graph, source=source))
        except nx.NetworkXError as e:
            print(f"Grafo non euleriano: {e}")
            return []

    def getEulerianPath(self, source=None):
        """
        Restituisce lista di archi (u, v) del cammino euleriano.
        Richiede hasEulerianPath() == True.
        Controller:
            path_edges = self._model.getEulerianPath()
            for u, v in path_edges:
                print(f"{u} → {v}")
        """
        try:
            return list(nx.eulerian_path(self._graph, source=source))
        except nx.NetworkXError as e:
            print(f"Nessun cammino euleriano: {e}")
            return []

    def eulerize(self):
        """
        Trasforma il grafo in euleriano aggiungendo archi minimi.
        Restituisce il grafo eulerianizzato (NON modifica self._graph).
        Controller: g_euler = self._model.eulerize()
        """
        try:
            return nx.eulerize(self._graph)
        except Exception as e:
            print(f"Errore eulerize: {e}")
            return None

    # --------------------------------------------------------------------------
    # CICLI HAMILTONIANI — TSP / Traveling Salesman Problem
    # Un ciclo hamiltoniano visita ogni NODO esattamente una volta
    # Problema NP-completo → si usano algoritmi approssimati
    # --------------------------------------------------------------------------
    def getTSPGreedy(self, source=None):
        """
        Cammino hamiltoniano approssimato — algoritmo greedy.
        Restituisce lista di nodi del ciclo (basso costo, non ottimale).
        Il grafo deve essere completo e pesato.
        Controller: cycle = self._model.getTSPGreedy()
        """
        try:
            return nx.approximation.greedy_tsp(self._graph,
                                               weight="weight",
                                               source=source)
        except Exception as e:
            print(f"Errore getTSPGreedy: {e}")
            return []

    def getTSPChristofides(self):
        """
        Cammino hamiltoniano approssimato — algoritmo Christofides.
        Garantisce al massimo 1.5x il costo ottimale (3/2-approximation).
        Richiede grafo NON orientato, completo, con pesi (disuguaglianza triangolare).
        Controller: cycle = self._model.getTSPChristofides()
        """
        try:
            return nx.approximation.christofides(self._graph, weight="weight")
        except Exception as e:
            print(f"Errore getTSPChristofides: {e}")
            return []

    def getTSPSimulatedAnnealing(self, init_cycle=None):
        """
        Cammino hamiltoniano approssimato — Simulated Annealing.
        Può dare risultati migliori di Greedy su grafi grandi.
        Controller: cycle = self._model.getTSPSimulatedAnnealing()
        """
        try:
            if init_cycle is None:
                init_cycle = nx.approximation.greedy_tsp(self._graph,
                                                          weight="weight")
            return nx.approximation.simulated_annealing_tsp(
                self._graph, init_cycle, weight="weight"
            )
        except Exception as e:
            print(f"Errore getTSPSimulatedAnnealing: {e}")
            return []

    def getTSPCost(self, cycle):
        """
        Calcola il costo totale di un ciclo hamiltoniano (lista di nodi).
        Controller:
            cycle = self._model.getTSPGreedy()
            costo = self._model.getTSPCost(cycle)
        """
        if len(cycle) < 2:
            return 0.0
        costo = 0.0
        for i in range(len(cycle) - 1):
            u, v = cycle[i], cycle[i + 1]
            if self._graph.has_edge(u, v):
                costo += self._graph[u][v].get("weight", 1)
            else:
                costo += float('inf')
        return costo









##àCHIN0OOK

# ══════════════════════════════════════════════════════════════
# DAO
# ══════════════════════════════════════════════════════════════

from database.DB_connect import DBConnect
from model.Arco import Arco


class DAO():
    def __init__(self):
        pass

    # ══════════════════════════════════════════════════════════════
    # DROPDOWN
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllGenre():
        """
        Popola il dropdown 'Genere'.
        Usato in: esame Chinook 19/05/2026
        Restituisce la lista dei nomi dei generi musicali.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """SELECT DISTINCT name
                       FROM genre
                       ORDER BY name"""
            cursor.execute(query)
            res = []
            for row in cursor:
                res.append(row["name"])
            return res
        except Exception as e:
            print(f"Errore getAllGenre: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def getAllArtistsByGenre(genre):
        """
        Popola il dropdown 'Artist' dopo aver scelto il genere.
        Usato in: esame Chinook 19/05/2026 – Punto 2a
        Restituisce i nomi degli artisti che hanno almeno un brano nel genere.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """SELECT DISTINCT a.Name
                       FROM artist a, album al, track t, genre g
                       WHERE a.ArtistId = al.ArtistId
                         AND al.AlbumId = t.AlbumId
                         AND t.GenreId  = g.GenreId
                         AND g.Name     = %s
                       ORDER BY a.Name"""
            cursor.execute(query, (genre,))
            res = []
            for row in cursor:
                res.append(row["Name"])
            return res
        except Exception as e:
            print(f"Errore getAllArtistsByGenre: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # NODI DEL GRAFO
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllNodes(genre):
        """
        Restituisce tutti i nodi del grafo: artisti che hanno almeno un brano
        nel genere selezionato.
        Usato in: esame Chinook 19/05/2026 – Punto 1b (costruzione nodi)

        Nota: i nodi sono identificati dal NOME dell'artista (stringa),
        non dall'id numerico — coerente con idMapNames[nome] = nome.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """SELECT DISTINCT a.Name
                       FROM artist a, album al, track t, genre g
                       WHERE a.ArtistId = al.ArtistId
                         AND al.AlbumId = t.AlbumId
                         AND t.GenreId  = g.GenreId
                         AND g.Name     = %s"""
            cursor.execute(query, (genre,))
            res = []
            for row in cursor:
                res.append(row["Name"])
            return res
        except Exception as e:
            print(f"Errore getAllNodes: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ARCHI DEL GRAFO – VERSO A→B  (pop(A) > pop(B))
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges1(genre, idMapNames):
        """
        Archi orientati da A verso B quando popolarità(A) > popolarità(B).
        Usato in: esame Chinook 19/05/2026 – Punto 1b

        Logica:
          - Due artisti A e B sono collegati se almeno un cliente ha
            acquistato brani di entrambi (stesso CustomerId nelle fatture).
          - La popolarità di un artista = numero di brani acquistati nel genere.
          - Peso arco = pop(A) + pop(B).
          - Questa query restituisce solo le coppie con pop(A) > pop(B)
            → arco va da A verso B.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1,
                     artist a2,
                     invoice i1,
                     invoice i2,
                     invoiceline il1,
                     invoiceline il2,
                     track t1,
                     track t2,
                     album al1,
                     album al2,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2

                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId = a1.ArtistId
                  AND p2.ArtistId = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita > p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges1: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ARCHI DEL GRAFO – VERSO B→A  (pop(B) > pop(A))
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges2(genre, idMapNames):
        """
        Archi orientati da B verso A quando popolarità(B) > popolarità(A).
        Usato in: esame Chinook 19/05/2026 – Punto 1b

        Stessa query di getAllEdges1, cambia solo la condizione finale:
            p1.popolarita < p2.popolarita   (invece di >)
        Nel Model viene aggiunto come: add_edge(e.a2, e.a1, weight=e.peso)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1,
                     artist a2,
                     invoice i1,
                     invoice i2,
                     invoiceline il1,
                     invoiceline il2,
                     track t1,
                     track t2,
                     album al1,
                     album al2,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2

                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId = a1.ArtistId
                  AND p2.ArtistId = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita < p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges2: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ARCHI DEL GRAFO – DOPPIO VERSO A↔B  (pop(A) == pop(B))
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges3(genre, idMapNames):
        """
        Archi in entrambi i versi A↔B quando popolarità(A) == popolarità(B).
        Usato in: esame Chinook 19/05/2026 – Punto 1b

        Nel Model vengono aggiunti ENTRAMBI:
            add_edge(e.a1, e.a2, weight=e.peso)
            add_edge(e.a2, e.a1, weight=e.peso)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1,
                     artist a2,
                     invoice i1,
                     invoice i2,
                     invoiceline il1,
                     invoiceline il2,
                     track t1,
                     track t2,
                     album al1,
                     album al2,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2

                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId = a1.ArtistId
                  AND p2.ArtistId = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita = p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges3: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # VARIANTE: GRAFO NON ORIENTATO
    # Usato quando la consegna chiede un grafo NON orientato (es. imdb 26/05/2026)
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdgesUndirected(genre, idMapNames):
        """
        Archi NON orientati: collega A e B se almeno un cliente ha
        acquistato brani di entrambi. Peso = pop(A) + pop(B).

        Usato quando la consegna dice 'grafo NON orientato ma pesato'.
        Nel Model: self._graph = nx.Graph() e add_edge(e.a1, e.a2, weight=e.peso).

        Differenza rispetto a getAllEdges1/2/3:
          - Non si divide per verso (non c'è orientamento).
          - Una sola query restituisce tutte le coppie distinte.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1,
                     artist a2,
                     invoice i1,
                     invoice i2,
                     invoiceline il1,
                     invoiceline il2,
                     track t1,
                     track t2,
                     album al1,
                     album al2,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,

                     (SELECT al.ArtistId,
                             COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2

                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId = a1.ArtistId
                  AND p2.ArtistId = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
            """
            # Nota: nessuna condizione su p1.popolarita vs p2.popolarita
            # perché il grafo è non orientato — tutte le coppie vanno bene
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdgesUndirected: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # VARIANTE: PESO = SOMMA QUANTITÀ PEZZI ACQUISTATI
    # (es. se il peso non è il conteggio brani ma la quantità in InvoiceLine)
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdgesWeightByQuantity(genre, idMapNames):
        """
        Come getAllEdgesUndirected ma il peso dell'arco è la SOMMA delle
        QUANTITÀ acquistate (campo Quantity di InvoiceLine), non il conteggio.

        Usato quando la consegna dice:
            'peso = somma del numero di pezzi venduti (campo quantity)'
        Esempio: esame bike_store Traccia B 10/07/2025.

        Cambia rispetto ad getAllEdgesUndirected solo nella subquery di popolarità:
            SUM(il.Quantity) invece di COUNT(*)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1,
                     artist a2,
                     invoice i1,
                     invoice i2,
                     invoiceline il1,
                     invoiceline il2,
                     track t1,
                     track t2,
                     album al1,
                     album al2,

                     (SELECT al.ArtistId,
                             SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,

                     (SELECT al.ArtistId,
                             SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2

                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId = a1.ArtistId
                  AND p2.ArtistId = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdgesWeightByQuantity: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()


    # ══════════════════════════════════════════════════════════════
    # ──────────────────────────────────────────────────────────────
    # SCENARIO 1 – GRAFO ORIENTATO, VERSO IN BASE ALLA POPOLARITÀ
    # Condizione arco: cliente comune ha comprato brani di entrambi
    # Popolarità: COUNT(*) brani acquistati nel genere
    # Peso: pop(A) + pop(B)
    # Usato in: esame Chinook 19/05/2026
    # ──────────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges1_popCount(genre, idMapNames):
        """
        SCENARIO 1a – Arco A→B quando pop(A) > pop(B).
        Popolarità = COUNT(*) brani acquistati nel genere.
        Nel Model: add_edge(e.a1, e.a2, weight=e.peso)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2
                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId  = a1.ArtistId
                  AND p2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita > p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges1_popCount: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def getAllEdges2_popCount(genre, idMapNames):
        """
        SCENARIO 1b – Arco B→A quando pop(B) > pop(A).
        Stessa query di getAllEdges1, cambia solo la condizione finale (<).
        Nel Model: add_edge(e.a2, e.a1, weight=e.peso)  ← ATTENZIONE inversione!
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2
                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId  = a1.ArtistId
                  AND p2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita < p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges2_popCount: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def getAllEdges3_popCount(genre, idMapNames):
        """
        SCENARIO 1c – Archi A↔B quando pop(A) == pop(B).
        Nel Model: add_edge(e.a1, e.a2) E add_edge(e.a2, e.a1)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2
                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId  = a1.ArtistId
                  AND p2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita = p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges3_popCount: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ──────────────────────────────────────────────────────────────
    # SCENARIO 2 – STESSO SCENARIO 1 MA POPOLARITÀ = SUM(Quantity)
    # Differenza: invece di COUNT(*) si usa SUM(il.Quantity)
    # Quando la consegna dice: 'popolarità = somma dei pezzi acquistati'
    # Peso: pop(A) + pop(B) dove pop = SUM(Quantity)
    # ──────────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges1_popQuantity(genre, idMapNames):
        """
        SCENARIO 2a – Arco A→B, pop(A) > pop(B).
        Popolarità = SUM(Quantity) invece di COUNT(*).
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,
                     (SELECT al.ArtistId, SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2
                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId  = a1.ArtistId
                  AND p2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita > p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges1_popQuantity: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def getAllEdges2_popQuantity(genre, idMapNames):
        """
        SCENARIO 2b – Arco B→A, pop(B) > pop(A). SUM(Quantity).
        Nel Model: add_edge(e.a2, e.a1, weight=e.peso)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,
                     (SELECT al.ArtistId, SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2
                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId  = a1.ArtistId
                  AND p2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita < p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges2_popQuantity: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def getAllEdges3_popQuantity(genre, idMapNames):
        """
        SCENARIO 2c – Archi A↔B, pop(A) == pop(B). SUM(Quantity).
        Nel Model: add_edge(e.a1, e.a2) E add_edge(e.a2, e.a1)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,
                     (SELECT al.ArtistId, SUM(il.Quantity) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2
                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId  = a1.ArtistId
                  AND p2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND p1.popolarita = p2.popolarita
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges3_popQuantity: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ──────────────────────────────────────────────────────────────
    # SCENARIO 3 – GRAFO NON ORIENTATO, PESO = pop(A) + pop(B)
    # Condizione arco: cliente comune
    # Quando la consegna dice 'grafo NON orientato ma pesato'
    # Nel Model: self._graph = nx.Graph()
    #            add_edge(e.a1, e.a2, weight=e.peso)
    # ──────────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdgesUndirected_popCount(genre, idMapNames):
        """
        SCENARIO 3 – Grafo non orientato.
        Peso = COUNT(*) pop(A) + COUNT(*) pop(B).
        Una sola query, nessuna condizione su popolarità relativa.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    p1.popolarita + p2.popolarita AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p1,
                     (SELECT al.ArtistId, COUNT(*) AS popolarita
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) p2
                WHERE a1.ArtistId < a2.ArtistId
                  AND p1.ArtistId  = a1.ArtistId
                  AND p2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdgesUndirected_popCount: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ──────────────────────────────────────────────────────────────
    # SCENARIO 4 – GRAFO NON ORIENTATO, PESO = NUMERO BRANI IN COMUNE
    # Condizione arco: i due artisti hanno almeno un brano nella
    # stessa playlist
    # Peso: numero di playlist in comune
    # Quando la consegna dice 'esiste un arco se hanno brani
    # nella stessa playlist, peso = numero playlist in comune'
    # ──────────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges_playlist(genre, idMapNames):
        """
        SCENARIO 4 – Arco tra A e B se hanno brani nella stessa playlist.
        Peso = numero di playlist in cui compaiono entrambi.
        Grafo non orientato.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    COUNT(DISTINCT pt1.PlaylistId) AS peso
                FROM artist a1, artist a2,
                     album al1, album al2,
                     track t1, track t2,
                     playlisttrack pt1, playlisttrack pt2,
                     genre g1, genre g2
                WHERE a1.ArtistId < a2.ArtistId
                  AND a1.ArtistId  = al1.ArtistId
                  AND a2.ArtistId  = al2.ArtistId
                  AND al1.AlbumId  = t1.AlbumId
                  AND al2.AlbumId  = t2.AlbumId
                  AND t1.TrackId   = pt1.TrackId
                  AND t2.TrackId   = pt2.TrackId
                  AND pt1.PlaylistId = pt2.PlaylistId
                  AND t1.GenreId   = g1.GenreId
                  AND t2.GenreId   = g2.GenreId
                  AND g1.Name      = %s
                  AND g2.Name      = %s
                GROUP BY a1.Name, a2.Name
                HAVING COUNT(DISTINCT pt1.PlaylistId) > 0
            """
            cursor.execute(query, (genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges_playlist: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ──────────────────────────────────────────────────────────────
    # SCENARIO 5 – GRAFO NON ORIENTATO, PESO = NUMERO CLIENTI IN COMUNE
    # Condizione arco: almeno un cliente ha comprato brani di entrambi
    # Peso: numero di clienti che hanno comprato da entrambi
    # Quando la consegna dice 'peso = numero clienti in comune'
    # ──────────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges_numClientiComuni(genre, idMapNames):
        """
        SCENARIO 5 – Peso = numero di clienti che hanno acquistato
        brani di entrambi gli artisti (non la somma delle popolarità).
        Grafo non orientato.
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    COUNT(DISTINCT i1.CustomerId) AS peso
                FROM artist a1, artist a2,
                     album al1, album al2,
                     track t1, track t2,
                     invoiceline il1, invoiceline il2,
                     invoice i1, invoice i2
                WHERE a1.ArtistId < a2.ArtistId
                  AND a1.ArtistId  = al1.ArtistId
                  AND a2.ArtistId  = al2.ArtistId
                  AND al1.AlbumId  = t1.AlbumId
                  AND al2.AlbumId  = t2.AlbumId
                  AND t1.TrackId   = il1.TrackId
                  AND t2.TrackId   = il2.TrackId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND t1.GenreId   = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId   = (SELECT GenreId FROM genre WHERE Name = %s)
                GROUP BY a1.Name, a2.Name
                HAVING COUNT(DISTINCT i1.CustomerId) > 0
            """
            cursor.execute(query, (genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges_numClientiComuni: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    # ══════════════════════════════════════════════════════════════
    # ──────────────────────────────────────────────────────────────
    # SCENARIO 6 – GRAFO ORIENTATO, VERSO IN BASE ALLE VENDITE TOTALI
    # Condizione arco: entrambi venduti almeno una volta
    # Peso: vendite(A) + vendite(B)
    # Verso: da chi ha più vendite verso chi ne ha meno
    # Quando la consegna dice 'arco uscente dal nodo con più vendite'
    # (es. variante bike_store Traccia A 10/07/2025)
    # ──────────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def getAllEdges1_venditeMaggiori(genre, idMapNames):
        """
        SCENARIO 6a – Arco A→B quando vendite(A) > vendite(B).
        Vendite = numero di fatture distinte che includono brani dell'artista.
        Nel Model: add_edge(e.a1, e.a2, weight=e.peso)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    v1.vendite + v2.vendite AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, COUNT(DISTINCT il.InvoiceId) AS vendite
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) v1,
                     (SELECT al.ArtistId, COUNT(DISTINCT il.InvoiceId) AS vendite
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) v2
                WHERE a1.ArtistId < a2.ArtistId
                  AND v1.ArtistId  = a1.ArtistId
                  AND v2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND v1.vendite > v2.vendite
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges1_venditeMaggiori: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def getAllEdges2_venditeMaggiori(genre, idMapNames):
        """
        SCENARIO 6b – Arco B→A quando vendite(B) > vendite(A).
        Nel Model: add_edge(e.a2, e.a1, weight=e.peso)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    v1.vendite + v2.vendite AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, COUNT(DISTINCT il.InvoiceId) AS vendite
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) v1,
                     (SELECT al.ArtistId, COUNT(DISTINCT il.InvoiceId) AS vendite
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) v2
                WHERE a1.ArtistId < a2.ArtistId
                  AND v1.ArtistId  = a1.ArtistId
                  AND v2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND v1.vendite < v2.vendite
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges2_venditeMaggiori: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def getAllEdges3_venditeMaggiori(genre, idMapNames):
        """
        SCENARIO 6c – Archi A↔B quando vendite(A) == vendite(B).
        Nel Model: add_edge(e.a1, e.a2) E add_edge(e.a2, e.a1)
        """
        cnx = DBConnect.get_connection()
        try:
            cursor = cnx.cursor(dictionary=True, buffered=True)
            query = """
                SELECT DISTINCT
                    a1.Name AS nomeA,
                    a2.Name AS nomeB,
                    v1.vendite + v2.vendite AS peso
                FROM artist a1, artist a2,
                     invoice i1, invoice i2,
                     invoiceline il1, invoiceline il2,
                     track t1, track t2,
                     album al1, album al2,
                     (SELECT al.ArtistId, COUNT(DISTINCT il.InvoiceId) AS vendite
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) v1,
                     (SELECT al.ArtistId, COUNT(DISTINCT il.InvoiceId) AS vendite
                      FROM invoiceline il, track t, album al
                      WHERE il.TrackId = t.TrackId
                        AND t.AlbumId  = al.AlbumId
                        AND t.GenreId  = (SELECT GenreId FROM genre WHERE Name = %s)
                      GROUP BY al.ArtistId) v2
                WHERE a1.ArtistId < a2.ArtistId
                  AND v1.ArtistId  = a1.ArtistId
                  AND v2.ArtistId  = a2.ArtistId
                  AND il1.InvoiceId = i1.InvoiceId
                  AND il2.InvoiceId = i2.InvoiceId
                  AND i1.CustomerId = i2.CustomerId
                  AND il1.TrackId   = t1.TrackId
                  AND il2.TrackId   = t2.TrackId
                  AND t1.AlbumId    = al1.AlbumId
                  AND t2.AlbumId    = al2.AlbumId
                  AND al1.ArtistId  = a1.ArtistId
                  AND al2.ArtistId  = a2.ArtistId
                  AND t1.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND t2.GenreId    = (SELECT GenreId FROM genre WHERE Name = %s)
                  AND v1.vendite = v2.vendite
            """
            cursor.execute(query, (genre, genre, genre, genre))
            res = []
            for row in cursor:
                if row["nomeA"] in idMapNames and row["nomeB"] in idMapNames:
                    res.append(Arco(idMapNames[row["nomeA"]], idMapNames[row["nomeB"]], row["peso"]))
            return res
        except Exception as e:
            print(f"Errore getAllEdges3_venditeMaggiori: {e}")
            return []
        finally:
            cursor.close()
            cnx.close()


 # ══════════════════════════════════════════════════════════════
# MODEL
# ══════════════════════════════════════════════════════════════
import networkx as nx


class Model:
    def __init__(self):
        self._idMapNames = {}     # nome → nome  (chiave e valore uguali per Chinook)
        self._graph = nx.DiGraph()  # default orientato; cambia in buildGraphUndirected

    # ══════════════════════════════════════════════════════════════
    # DROPDOWN
    # ══════════════════════════════════════════════════════════════

    def getAllGenre(self):
        from database.DAO import DAO
        return DAO.getAllGenre()

    def getAllArtistsByGenre(self, genre):
        """
        Restituisce i nomi degli artisti del genere selezionato.
        Usato per popolare il dropdown 'Artist' (Punto 2a esame 19/05/2026).
        """
        from database.DAO import DAO
        return DAO.getAllArtistsByGenre(genre)

    # ══════════════════════════════════════════════════════════════
    # COSTRUZIONE GRAFO – ORIENTATO (esame Chinook 19/05/2026)
    # ══════════════════════════════════════════════════════════════

    def buildGraph(self, genre):
        """
        Costruisce il grafo ORIENTATO E PESATO degli artisti.
        Usato in: esame Chinook 19/05/2026 – Punto 1b

        Logica degli archi:
          - Arco A→B se pop(A) > pop(B)  → getAllEdges1
          - Arco B→A se pop(B) > pop(A)  → getAllEdges2 (aggiunto come e.a2→e.a1)
          - Arco A↔B se pop(A) == pop(B) → getAllEdges3 (entrambe le direzioni)
        """
        self._idMapNames = {}
        self._graph = nx.DiGraph()
        from database.DAO import DAO

        # Nodi
        self._names = DAO.getAllNodes(genre)
        for n in self._names:
            self._idMapNames[n] = n
        self._graph.add_nodes_from(self._names)

        # Archi A→B (pop A > pop B)
        allEdges1 = DAO.getAllEdges1(genre, idMapNames=self._idMapNames)
        for e in allEdges1:
            self._graph.add_edge(e.a1, e.a2, weight=e.peso)

        # Archi B→A (pop B > pop A)
        # ATTENZIONE: il DAO restituisce (nomeA, nomeB) con a1<a2,
        # ma qui vogliamo B→A, quindi si inverte: e.a2 → e.a1
        allEdges2 = DAO.getAllEdges2(genre, idMapNames=self._idMapNames)
        for e in allEdges2:
            self._graph.add_edge(e.a2, e.a1, weight=e.peso)

        # Archi A↔B (stessa popolarità → entrambe le direzioni)
        allEdges3 = DAO.getAllEdges3(genre, idMapNames=self._idMapNames)
        for e in allEdges3:
            self._graph.add_edge(e.a1, e.a2, weight=e.peso)
            self._graph.add_edge(e.a2, e.a1, weight=e.peso)

    # ══════════════════════════════════════════════════════════════
    # COSTRUZIONE GRAFO – NON ORIENTATO
    # Usato quando la consegna dice 'grafo NON orientato ma pesato'
    # (es. esame imdb 26/05/2026, formula1 15/09/2025)
    # ══════════════════════════════════════════════════════════════

    def buildGraphUndirected(self, genre):
        """
        Costruisce il grafo NON ORIENTATO E PESATO.
        Usato quando la consegna dice: 'grafo NON orientato ma pesato'.

        Una sola chiamata al DAO perché non c'è verso da gestire.
        Peso = pop(A) + pop(B) di default (getAllEdgesUndirected).
        """
        self._idMapNames = {}
        self._graph = nx.Graph()  # ← Graph, non DiGraph
        from database.DAO import DAO

        self._names = DAO.getAllNodes(genre)
        for n in self._names:
            self._idMapNames[n] = n
        self._graph.add_nodes_from(self._names)

        allEdges = DAO.getAllEdgesUndirected(genre, idMapNames=self._idMapNames)
        for e in allEdges:
            self._graph.add_edge(e.a1, e.a2, weight=e.peso)

    # ══════════════════════════════════════════════════════════════
    # STATISTICHE BASE DEL GRAFO
    # Usate sempre in Punto 1c di tutti gli esami
    # ══════════════════════════════════════════════════════════════

    def getGraphDetails(self):
        """
        Restituisce numero di nodi e numero di archi.
        Usato in: tutti gli esami – Punto 1c
        Output nel controller: ft.Text(f"Nodi: {nNodi}, Archi: {nArchi}")
        """
        return len(self._graph.nodes), len(self._graph.edges)

    def getGraph(self):
        """Rende il grafo accessibile dal controller per operazioni dirette."""
        return self._graph

    def getTop5Archi(self):
        """
        Restituisce i 5 archi con peso maggiore, ordinati in modo decrescente.
        Usato in: tutti gli esami – Punto 1c

        Output nel controller:
            for arco in top5:
                ft.Text(f"{arco[0]} -> {arco[1]} : {arco[2]['weight']}")

        Nota: arco[0] = nodo partenza, arco[1] = nodo arrivo, arco[2] = dict attributi
        """
        return sorted(
            self._graph.edges(data=True),
            key=lambda x: x[2]["weight"],
            reverse=True
        )[:5]

    # ══════════════════════════════════════════════════════════════
    # INFLUENZA – GRAFO ORIENTATO
    # Usato in: esame Chinook 19/05/2026 – Punto 1c
    # ══════════════════════════════════════════════════════════════

    def getInfluenza(self, nodo):
        """
        Calcola l'influenza di un artista come:
            influenza = somma pesi archi USCENTI − somma pesi archi ENTRANTI

        Usato internamente da getArtistaPiuInfluente().
        Funziona solo su DiGraph (grafo orientato).
        """
        uscenti = sum(
            self._graph[nodo][v]["weight"]
            for v in self._graph.successors(nodo)
        )
        entranti = sum(
            self._graph[u][nodo]["weight"]
            for u in self._graph.predecessors(nodo)
        )
        return uscenti - entranti

    def getArtistaPiuInfluente(self):
        """
        Restituisce l'artista con influenza massima e il suo punteggio.
        Usato in: esame Chinook 19/05/2026 – Punto 1c

        Output nel controller:
            artista, infl = self._model.getArtistaPiuInfluente()
            ft.Text(f"Artista più influente: {artista} ({infl})")
        """
        migliore = max(self._graph.nodes, key=self.getInfluenza)
        return migliore, self.getInfluenza(migliore)

    # ══════════════════════════════════════════════════════════════
    # COMPONENTI CONNESSE
    # Usato in: tutti gli esami – Punto 1c (numero componenti + componente maggiore)
    # ══════════════════════════════════════════════════════════════

    def getNumComponentiConnesse(self):
        """
        Restituisce il numero di componenti connesse.
        - DiGraph → componenti DEBOLMENTE connesse (ignora il verso)
        - Graph   → componenti connesse normali

        Usato in: esami formula1, imdb, bike_store – Punto 1c
        Output nel controller:
            ft.Text(f"Il grafo ha {n} componenti connesse")
        """
        if isinstance(self._graph, nx.DiGraph):
            return nx.number_weakly_connected_components(self._graph)
        else:
            return nx.number_connected_components(self._graph)

    def getComponentiConnesse(self):
        """
        Restituisce la lista di tutte le componenti connesse,
        ordinate per dimensione decrescente.
        Ogni componente è un set di nomi di nodi.

        Usato internamente da getComponenteMaggiore().
        """
        if isinstance(self._graph, nx.DiGraph):
            componenti = list(nx.weakly_connected_components(self._graph))
        else:
            componenti = list(nx.connected_components(self._graph))
        return sorted(componenti, key=len, reverse=True)

    def getComponenteMaggiore(self):
        """
        Restituisce la lista dei nodi della componente connessa più grande.
        Usato in: tutti gli esami – Punto 1c

        Output nel controller:
            componente = self._model.getComponenteMaggiore()
            ft.Text(f"La più grande componente connessa è lunga {len(componente)}:")
            for nodo in componente:
                ft.Text(nodo)
        """
        componenti = self.getComponentiConnesse()
        if not componenti:
            return []
        return list(componenti[0])

    def getComponenteMaggioreOrdinataPerGrado(self):
        """
        Restituisce i nodi della componente più grande
        ORDINATI per grado DECRESCENTE.

        Usato in: esami formula1 12/01/2026, formula1 15/09/2025 – Punto 1c
        La consegna dice: 'stamparne tutti i nodi, ordinati in senso
        decrescente secondo il grado dei nodi'.

        Output nel controller:
            nodi = self._model.getComponenteMaggioreOrdinataPerGrado()
            for nome, grado in nodi:
                ft.Text(f"{nome} (grado={grado})")
        """
        componente = set(self.getComponenteMaggiore())
        subgraph = self._graph.subgraph(componente)

        # Per DiGraph usa degree totale (in+out); per Graph usa degree normale
        nodi_con_grado = [(n, subgraph.degree(n)) for n in subgraph.nodes]
        return sorted(nodi_con_grado, key=lambda x: x[1], reverse=True)

    def getComponenteMaggioreOrdinataPerPesoMassimoArchi(self):
        """
        Restituisce i nodi della componente più grande ordinati per
        PESO MASSIMO degli archi incidenti (decrescente).

        Usato in: esame formula1 26/06/2025 Traccia C – Punto 1
        La consegna dice: 'stamparne tutti i nodi, ordinati in senso
        decrescente di peso massimo degli archi incidenti'.

        Output nel controller:
            nodi = self._model.getComponenteMaggioreOrdinataPerPesoMassimoArchi()
            for nome, peso_max in nodi:
                ft.Text(f"{nome} -- {peso_max}")
        """
        componente = set(self.getComponenteMaggiore())
        subgraph = self._graph.subgraph(componente)

        def peso_massimo_incidente(nodo):
            # Tutti gli archi del nodo nel sottografo (entranti + uscenti)
            pesi = [d["weight"] for _, _, d in subgraph.edges(nodo, data=True)]
            if isinstance(subgraph, nx.DiGraph):
                pesi += [d["weight"] for _, _, d in subgraph.in_edges(nodo, data=True)]
            return max(pesi) if pesi else 0

        nodi_con_peso = [(n, peso_massimo_incidente(n)) for n in subgraph.nodes]
        return sorted(nodi_con_peso, key=lambda x: x[1], reverse=True)

    def getComponenteMaggioreOrdinataPerPesoMinimoArchi(self):
        """
        Restituisce i nodi della componente più grande ordinati per
        PESO MINIMO degli archi incidenti (decrescente).

        Usato in: esame formula1 26/06/2025 Traccia B – Punto 1
        La consegna dice: 'stamparne tutti i nodi, ordinati in senso
        decrescente di peso minimo degli archi incidenti'.
        """
        componente = set(self.getComponenteMaggiore())
        subgraph = self._graph.subgraph(componente)

        def peso_minimo_incidente(nodo):
            pesi = [d["weight"] for _, _, d in subgraph.edges(nodo, data=True)]
            if isinstance(subgraph, nx.DiGraph):
                pesi += [d["weight"] for _, _, d in subgraph.in_edges(nodo, data=True)]
            return min(pesi) if pesi else 0

        nodi_con_peso = [(n, peso_minimo_incidente(n)) for n in subgraph.nodes]
        return sorted(nodi_con_peso, key=lambda x: x[1], reverse=True)

    def getTop3Archi(self):
        """
        Restituisce i 3 archi con peso maggiore.
        Usato in: esami formula1 12/01/2026, 15/09/2025 – Punto 1c
        La consegna dice: 'stampare i TRE archi di peso maggiore'.

        Output nel controller:
            for arco in top3:
                ft.Text(f"{arco[0]} -> {arco[1]} : {arco[2]['weight']}")
        """
        return sorted(
            self._graph.edges(data=True),
            key=lambda x: x[2]["weight"],
            reverse=True
        )[:3]

    # ══════════════════════════════════════════════════════════════
    # CAMMINI – PUNTO 2
    # ══════════════════════════════════════════════════════════════

    def getCamminoMaxDFS(self, nodoPartenza):
        """
        Trova il PERCORSO PIÙ LUNGO (in numero di nodi) partendo da nodoPartenza.
        Algoritmo: DFS ricorsiva con backtracking.

        Usato in: esame Chinook 19/05/2026 – Punto 2b
                  esame bike_store 10/11/2025 – Punto 1d (cerca percorso massimo)

        Args:
            nodoPartenza: nome del nodo di partenza (stringa per Chinook)

        Output nel controller:
            cammino = self._model.getCamminoMaxDFS(artista)
            for nodo in cammino:
                ft.Text(nodo)
        """
        self._best_path = [nodoPartenza]

        def dfs(nodo, visitati, cammino_corrente):
            if len(cammino_corrente) > len(self._best_path):
                self._best_path = list(cammino_corrente)

            # successors per DiGraph, neighbors per Graph
            if isinstance(self._graph, nx.DiGraph):
                vicini = list(self._graph.successors(nodo))
            else:
                vicini = list(self._graph.neighbors(nodo))

            for vicino in vicini:
                if vicino not in visitati:
                    visitati.add(vicino)
                    cammino_corrente.append(vicino)
                    dfs(vicino, visitati, cammino_corrente)
                    cammino_corrente.pop()
                    visitati.remove(vicino)

        dfs(nodoPartenza, {nodoPartenza}, [nodoPartenza])
        return self._best_path

    def getCamminoMaxGlobale(self):
        """
        Trova il percorso più lungo in TUTTO IL GRAFO, provando ogni nodo
        come punto di partenza.

        Usato quando la consegna non specifica il nodo di partenza
        (es. 'individuare il percorso più lungo dato il grafo').

        ATTENZIONE: lento su grafi grandi (O(n) chiamate DFS).
        Output nel controller: stessa struttura di getCamminoMaxDFS.
        """
        cammino_globale = []
        for nodo in self._graph.nodes:
            cammino = self.getCamminoMaxDFS(nodo)
            if len(cammino) > len(cammino_globale):
                cammino_globale = cammino
        return cammino_globale

    def getCamminoPesiCrescenti(self, nodoPartenza):
        """
        Cammino semplice di lunghezza MASSIMA con pesi degli archi
        STRETTAMENTE CRESCENTI.

        Usato in: esame Chinook 19/05/2026 – Punto 2c
        La consegna dice: 'trovare un cammino semplice di lunghezza massima
        tale che ogni arco successivo abbia peso strettamente crescente'.

        Args:
            nodoPartenza: nome del nodo di partenza

        Output nel controller:
            cammino = self._model.getCamminoPesiCrescenti(artista)
            for nodo in cammino:
                ft.Text(nodo)
        """
        self._best_path = [nodoPartenza]

        def dfs(nodo, visitati, cammino_corrente, peso_precedente):
            if len(cammino_corrente) > len(self._best_path):
                self._best_path = list(cammino_corrente)

            if isinstance(self._graph, nx.DiGraph):
                vicini = list(self._graph.successors(nodo))
            else:
                vicini = list(self._graph.neighbors(nodo))

            for vicino in vicini:
                if vicino not in visitati:
                    peso_arco = self._graph[nodo][vicino]["weight"]
                    if peso_arco > peso_precedente:  # strettamente crescente
                        visitati.add(vicino)
                        cammino_corrente.append(vicino)
                        dfs(vicino, visitati, cammino_corrente, peso_arco)
                        cammino_corrente.pop()
                        visitati.remove(vicino)

        dfs(nodoPartenza, {nodoPartenza}, [nodoPartenza], float('-inf'))
        return self._best_path

    def getCamminoPesiDecrescenti(self, nodoPartenza):
        """
        Cammino semplice di lunghezza MASSIMA con pesi degli archi
        STRETTAMENTE DECRESCENTI.

        Usato in: esame bike_store 10/11/2025 – Punto 2 (Ricorsione)
        La consegna dice: 'il peso degli archi nel percorso deve essere
        strettamente decrescente'.

        Args:
            nodoPartenza: nome/id del nodo di partenza
        """
        self._best_path = [nodoPartenza]

        def dfs(nodo, visitati, cammino_corrente, peso_precedente):
            if len(cammino_corrente) > len(self._best_path):
                self._best_path = list(cammino_corrente)

            if isinstance(self._graph, nx.DiGraph):
                vicini = list(self._graph.successors(nodo))
            else:
                vicini = list(self._graph.neighbors(nodo))

            for vicino in vicini:
                if vicino not in visitati:
                    peso_arco = self._graph[nodo][vicino]["weight"]
                    if peso_arco < peso_precedente:  # strettamente decrescente
                        visitati.add(vicino)
                        cammino_corrente.append(vicino)
                        dfs(vicino, visitati, cammino_corrente, peso_arco)
                        cammino_corrente.pop()
                        visitati.remove(vicino)

        dfs(nodoPartenza, {nodoPartenza}, [nodoPartenza], float('inf'))
        return self._best_path

    def getCamminoEtaDecrescente(self, nodoPartenza):
        """
        Cammino semplice di lunghezza massima dove ogni nodo successivo
        ha ETÀ STRETTAMENTE DECRESCENTE.

        Usato in: esame imdb 26/05/2026 – Punto 2b
        La consegna dice: 'trovare un cammino semplice di lunghezza massima
        tale che ogni nodo successivo abbia un età strettamente decrescente'.

        PREREQUISITO: ogni nodo deve avere l'attributo 'eta' impostato
        durante la costruzione del grafo, es:
            self._graph.add_node(nome, eta=valore_eta)

        Args:
            nodoPartenza: nome del nodo di partenza
        """
        self._best_path = [nodoPartenza]

        def dfs(nodo, visitati, cammino_corrente, eta_precedente):
            if len(cammino_corrente) > len(self._best_path):
                self._best_path = list(cammino_corrente)

            vicini = list(self._graph.neighbors(nodo))  # Graph non orientato per imdb
            for vicino in vicini:
                if vicino not in visitati:
                    eta_vicino = self._graph.nodes[vicino].get("eta", 0)
                    if eta_vicino < eta_precedente:  # strettamente decrescente
                        visitati.add(vicino)
                        cammino_corrente.append(vicino)
                        dfs(vicino, visitati, cammino_corrente, eta_vicino)
                        cammino_corrente.pop()
                        visitati.remove(vicino)

        eta_start = self._graph.nodes[nodoPartenza].get("eta", float('inf'))
        dfs(nodoPartenza, {nodoPartenza}, [nodoPartenza], eta_start)
        return self._best_path


 # ══════════════════════════════════════════════════════════════
# CONTROLLER
# ══════════════════════════════════════════════════════════════
import flet as ft


class Controller:
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._choiceGenre = None    # genere selezionato dal dropdown
        self._choiceArtist = None   # artista selezionato dal dropdown (Punto 2)

    # ══════════════════════════════════════════════════════════════
    # DROPDOWN
    # ══════════════════════════════════════════════════════════════

    def fillDDGenre(self):
        """
        Popola il dropdown dei generi all'avvio dell'applicazione.
        Chiamato da view.load_interface().
        """
        generi = self._model.getAllGenre()
        genreOptions = list(map(lambda x: ft.dropdown.Option(x), generi))
        self._view._ddGenre.options = genreOptions
        self._view.update_page()

    def _choiceDDGenre(self, e):
        """
        Salva il genere selezionato dall'utente.
        Collegato all'evento on_change del dropdown genere.
        """
        self._choiceGenre = e.control.value
        print(f"Genere selezionato: {self._choiceGenre}")

    def _choiceDDArtist(self, e):
        """
        Salva l'artista selezionato dall'utente.
        Collegato all'evento on_change del dropdown artista (Punto 2).
        """
        self._choiceArtist = e.control.value
        print(f"Artista selezionato: {self._choiceArtist}")

    def fillDDArtist(self):
        """
        Popola il dropdown degli artisti dopo aver costruito il grafo.
        Chiamato alla fine di handleCreaGrafo.
        Usato in: esame Chinook 19/05/2026 – Punto 2a
        """
        if self._choiceGenre is None:
            return
        artisti = self._model.getAllArtistsByGenre(self._choiceGenre)
        artistOptions = list(map(lambda x: ft.dropdown.Option(x), artisti))
        self._view._ddArtist.options = artistOptions
        self._view._ddArtist.disabled = False
        self._view.update_page()

    # ══════════════════════════════════════════════════════════════
    # COSTRUZIONE GRAFO – Punto 1
    # ══════════════════════════════════════════════════════════════

    def handleCreaGrafo(self, e):
        """
        Gestisce il click sul pulsante 'Crea Grafo'.
        Usato in: esame Chinook 19/05/2026 – Punto 1b/1c

        Mostra in output:
          - numero nodi e archi
          - artista più influente (peso uscente - peso entrante)
          - top 5 archi per peso
          - numero componenti connesse
          - nodi della componente più grande
        """
        self._view.txt_result.controls.clear()

        # Validazione: genere selezionato?
        if self._choiceGenre is None:
            self._view.txt_result.controls.append(
                ft.Text("Seleziona un genere!", color="red")
            )
            self._view.update_page()
            return

        # Costruisce il grafo
        self._model.buildGraph(self._choiceGenre)
        self._graph = self._model.getGraph()

        # Numero nodi e archi
        nNodi, nArchi = self._model.getGraphDetails()
        self._view.txt_result.controls.append(
            ft.Text("Grafo correttamente creato:", color="green")
        )
        self._view.txt_result.controls.append(ft.Text(f"Numero di nodi:{nNodi}"))
        self._view.txt_result.controls.append(ft.Text(f"Numero di archi:{nArchi}"))

        # Artista più influente
        artista, infl = self._model.getArtistaPiuInfluente()
        self._view.txt_result.controls.append(
            ft.Text(f"Artista più influente: {artista}, con influenza: {int(infl)}")
        )

        # Top 5 archi
        self._view.txt_result.controls.append(ft.Text("Top 5 archi:"))
        top5 = self._model.getTop5Archi()
        for arco in top5:
            self._view.txt_result.controls.append(
                ft.Text(f"{arco[0]} -> {arco[1]} : {int(arco[2]['weight'])}")
            )

        # Componenti connesse
        nComp = self._model.getNumComponentiConnesse()
        self._view.txt_result.controls.append(
            ft.Text(f"Il grafo ha {nComp} componenti connesse")
        )

        # Componente maggiore
        componente = self._model.getComponenteMaggiore()
        self._view.txt_result.controls.append(
            ft.Text(f"La più grande componente connessa è lunga {len(componente)}:")
        )
        for nodo in componente:
            self._view.txt_result.controls.append(ft.Text(f"  {nodo}"))

        # Popola dropdown artisti per Punto 2
        self.fillDDArtist()

        self._view.update_page()

    # ──────────────────────────────────────────────────────────────
    # VARIANTE: handleCreaGrafo con top3 archi e componente ordinata per grado
    # Usato in: esami formula1 12/01/2026, 15/09/2025
    # Stessa struttura di handleCreaGrafo, cambia getTop3Archi e
    # getComponenteMaggioreOrdinataPerGrado al posto dei metodi standard
    # ──────────────────────────────────────────────────────────────

    def handleStampaDettagliF1(self, e):
        """
        Gestisce 'Stampa Dettagli' per gli esami formula1.
        Usato in: esame formula1 12/01/2026, 15/09/2025 – Punto 1c (Stampa Dettagli)

        Differenze rispetto a handleCreaGrafo:
          - 3 archi invece di 5
          - Componente ordinata per GRADO (non dimensione)
          - Non c'è artista più influente
        """
        self._view.txt_result.controls.clear()

        if self._graph is None:
            self._view.txt_result.controls.append(
                ft.Text("Crea prima il grafo!", color="red")
            )
            self._view.update_page()
            return

        # Top 3 archi
        self._view.txt_result.controls.append(ft.Text("Archi di peso maggiore:", color="red"))
        top3 = self._model.getTop3Archi()
        for arco in top3:
            self._view.txt_result.controls.append(
                ft.Text(f"{arco[0]} -> {arco[1]} ({int(arco[2]['weight'])} piloti condivisi)")
            )

        # Numero componenti connesse
        nComp = self._model.getNumComponentiConnesse()
        self._view.txt_result.controls.append(
            ft.Text(f"Il grafo ha {nComp} componenti connesse", color="red")
        )

        # Componente più grande ordinata per grado
        nodi_con_grado = self._model.getComponenteMaggioreOrdinataPerGrado()
        self._view.txt_result.controls.append(
            ft.Text(f"Componente più grande ({len(nodi_con_grado)} nodi):", color="red")
        )
        for nome, grado in nodi_con_grado:
            self._view.txt_result.controls.append(
                ft.Text(f"  {nome} (grado={grado})")
            )

        self._view.update_page()

    # ──────────────────────────────────────────────────────────────
    # VARIANTE: handleCreaGrafo con componente ordinata per peso massimo archi
    # Usato in: esame formula1 26/06/2025 Traccia C
    # ──────────────────────────────────────────────────────────────

    def handleStampaDettagliF1C(self, e):
        """
        Gestisce 'Stampa Dettagli' per esame formula1 26/06/2025 Traccia C.
        Componente ordinata per peso MASSIMO degli archi incidenti.
        """
        self._view.txt_result.controls.clear()

        nNodi, nArchi = self._model.getGraphDetails()
        self._view.txt_result.controls.append(ft.Text("Stampa dettagli:"))

        nodi_con_peso = self._model.getComponenteMaggioreOrdinataPerPesoMassimoArchi()
        for nome, peso_max in nodi_con_peso:
            self._view.txt_result.controls.append(
                ft.Text(f"{nome} -- {int(peso_max)}")
            )

        self._view.update_page()

    # ══════════════════════════════════════════════════════════════
    # CAMMINI – Punto 2
    # ══════════════════════════════════════════════════════════════

    def handleCammino(self, e):
        """
        Gestisce il click su 'Trova Cammino'.
        Usato in: esame Chinook 19/05/2026 – Punto 2b/2c

        Mostra:
          - Il percorso più lungo dal nodo selezionato (DFS)
          - Il cammino con pesi strettamente crescenti (Punto 2c)

        PREREQUISITO: l'utente deve aver selezionato un artista dal dropdown.
        """
        self._view.txt_result.controls.clear()

        # Validazione
        if self._choiceArtist is None:
            self._view.txt_result.controls.append(
                ft.Text("Seleziona un artista!", color="red")
            )
            self._view.update_page()
            return

        if self._model.getGraph().number_of_nodes() == 0:
            self._view.txt_result.controls.append(
                ft.Text("Crea prima il grafo!", color="red")
            )
            self._view.update_page()
            return

        # Punto 2b: percorso più lungo
        self._view.txt_result.controls.append(
            ft.Text("Percorso più lungo:", color="blue")
        )
        cammino = self._model.getCamminoMaxDFS(self._choiceArtist)
        self._view.txt_result.controls.append(
            ft.Text(f"Lunghezza: {len(cammino)}")
        )
        for nodo in cammino:
            self._view.txt_result.controls.append(ft.Text(f"  {nodo}"))

        # Punto 2c: cammino con pesi crescenti
        self._view.txt_result.controls.append(
            ft.Text("Cammino con pesi strettamente crescenti:", color="blue")
        )
        cammino_crescente = self._model.getCamminoPesiCrescenti(self._choiceArtist)
        self._view.txt_result.controls.append(
            ft.Text(f"Lunghezza: {len(cammino_crescente)}")
        )
        for nodo in cammino_crescente:
            self._view.txt_result.controls.append(ft.Text(f"  {nodo}"))

        self._view.update_page()

    def handleCamminoGlobale(self, e):
        """
        Trova il percorso più lungo nell'INTERO grafo (prova tutti i nodi).
        Usato quando la consegna non specifica il nodo di partenza:
            'individuare il percorso più lungo dato il grafo costruito'
        Es: esame imdb 26/05/2026 – Punto 2a
        """
        self._view.txt_result.controls.clear()

        if self._model.getGraph().number_of_nodes() == 0:
            self._view.txt_result.controls.append(
                ft.Text("Crea prima il grafo!", color="red")
            )
            self._view.update_page()
            return

        cammino = self._model.getCamminoMaxGlobale()
        self._view.txt_result.controls.append(
            ft.Text(f"Percorso più lungo globale (lunghezza: {len(cammino)}):", color="blue")
        )
        for nodo in cammino:
            self._view.txt_result.controls.append(ft.Text(f"  {nodo}"))

        self._view.update_page()

    def handleCamminoPesiDecrescenti(self, e):
        """
        Cammino con pesi STRETTAMENTE DECRESCENTI dal nodo selezionato.
        Usato in: esame bike_store 10/11/2025 – Punto 2 (pulsante 'Ricorsione')
        """
        self._view.txt_result.controls.clear()

        if self._choiceArtist is None:
            self._view.txt_result.controls.append(
                ft.Text("Seleziona un nodo di partenza!", color="red")
            )
            self._view.update_page()
            return

        cammino = self._model.getCamminoPesiDecrescenti(self._choiceArtist)
        self._view.txt_result.controls.append(
            ft.Text(f"Cammino pesi decrescenti (lunghezza: {len(cammino)}):", color="blue")
        )
        for nodo in cammino:
            self._view.txt_result.controls.append(ft.Text(f"  {nodo}"))

        self._view.update_page()