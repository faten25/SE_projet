import copy
import random
import threading #lance plusieurs taches en parallele
import time # mesure le temps dans parCost


class Task:
    """
    Représente une tâche du système.

    Chaque tâche possède :
    - un nom
    - les variables qu'elle lit
    - les variables qu'elle écrit
    - une fonction run qui sera exécutée
    """
    
    #constructeur de chaque tache 
    
    def __init__(self, name="", reads=None, writes=None, run=None):
        self.name = name
        # si reads existe on en fait une copie sinon liste vide
        self.reads = reads[:] if reads else [] 
        self.writes = writes[:] if writes else []
        self.run = run #on stocke la fonction a executer


class TaskSystem:
    """
    Construit le système de tâches à partir :
    - d'une liste de tâches
    - d'un dictionnaire de précédence initial
    """

    def __init__(self, tasks, precedence):
        self.tasks = tasks
        self.precedence = {} 
        self.task_map = {} # on prepare un dictionnaire qui associe nom et objet de tache

        # Vérification que les tâches sont correctes
        self._validate_tasks()

        # Permet d'accéder rapidement à une tâche via son nom
        self.task_map = {task.name: task for task in self.tasks}

        # Vérification du dictionnaire de précédence
        self._validate_precedence(precedence)

        # Construction du graphe initial
        self.initial_deps = {task.name: set() for task in self.tasks}
        self.initial_succ = {task.name: set() for task in self.tasks}

        for task_name, deps in precedence.items(): # on parcourt du dico
            for dep in deps:
                self.initial_deps[task_name].add(dep) # on ajt dep dans les dep de task_name
                self.initial_succ[dep].add(task_name) # on ajt task_name dans les succ de dep

        # On vérifie que le graphe initial ne contient pas de cycle
        self._check_cycle(self.initial_deps)

        # Permet de savoir si une tâche est avant une autre dans le graphe initial
        self.initial_reach = self._compute_reachability(self.initial_succ)

        # Graphe final = graphe initial + dépendances dues aux interférences
        self.final_deps = {name: set(deps) for name, deps in self.initial_deps.items()}
        self.final_succ = {name: set(v) for name, v in self.initial_succ.items()}

        self._build_max_parallel_graph()

        # Vérification finale
        self._check_cycle(self.final_deps)

        # Version finale plus simple à afficher
        self.precedence = {name: sorted(list(v)) for name, v in self.final_deps.items()}

    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------

    #verifie que les taches sont bien definies
    def _validate_tasks(self):
        # task est bien une liste non vide 
        if not isinstance(self.tasks, list) or len(self.tasks) == 0:
            raise ValueError("tasks doit être une liste non vide.")
        #liste temporaire pour eviter les doublons
        names = []

        for task in self.tasks:
            if not isinstance(task, Task):
                raise TypeError("Les éléments de tasks doivent être des Task.")

            if not isinstance(task.name, str) or task.name.strip() == "":
                raise ValueError("Chaque tâche doit avoir un nom valide.")

            if task.name in names:
                raise ValueError(f"Nom de tâche dupliqué : {task.name}")

            names.append(task.name)

            if not isinstance(task.reads, list) or not isinstance(task.writes, list):
                raise TypeError("reads et writes doivent être des listes.")

            if not callable(task.run):
                raise TypeError(f"La tâche {task.name} doit avoir une fonction run.")

    #verifie le dictionnaire precedence
    def _validate_precedence(self, precedence):

        if not isinstance(precedence, dict):
            raise TypeError("precedence doit être un dictionnaire.")

        task_names = {task.name for task in self.tasks}

        if set(precedence.keys()) != task_names:
            raise ValueError(
                "Le dictionnaire de précédence doit contenir une entrée par tâche."
            )

        for task_name, deps in precedence.items():

            if not isinstance(deps, list):
                raise TypeError("Les dépendances doivent être dans une liste.")

            for dep in deps:

                if dep not in task_names:
                    raise ValueError(f"Tâche inconnue : {dep}")

                if dep == task_name:
                    raise ValueError("Une tâche ne peut pas dépendre d'elle-même.")

    # ------------------------------------------------------------
    # OUTILS GRAPHE
    # ------------------------------------------------------------

    def _compute_reachability(self, succ):
        """
        Calcule quelles tâches sont atteignables depuis chaque tâche.
        Sert à savoir si une tâche est avant une autre.
        """
        
        #on prepare le dictionnaire resultat
        reach = {name: set() for name in succ}

        #parcourt depuis chaque tache de depart 
        for start in succ:

            visited = set() # ce qu on a visite
            stack = [start] # stocke le graphe

            while stack: #tant qu il y a des taches

                node = stack.pop() #on en prend un 

                for nxt in succ[node]: #on regarde les successeurs

                    if nxt not in visited: # si pas visite 
                        visited.add(nxt) # on l ajoute a explorer 
                        stack.append(nxt)

            reach[start] = visited # on stocke l ensemble des taches atteignables depuis start

        return reach

    def _check_cycle(self, deps):
        """
        Vérifie qu'il n'y a pas de cycle dans le graphe.
        """

        #nombre de dependance entrantes de chaque tache 
        indeg = {name: len(deps[name]) for name in deps}
        #toutes les taches sans dependance
        ready = [name for name in indeg if indeg[name] == 0]
        count = 0

        #on reconstruit les successeurs a partie des dependances 
        succ = {name: set() for name in deps}

        #si before est dep de after, after est succ de before
        for after, before_set in deps.items():
            for before in before_set:
                succ[before].add(after)

        # tant que tache prete 
        while ready:

            node = ready.pop(0) # on prend 1ere tache 
            count += 1

            for nxt in sorted(succ[node]): # on regarde les successeurs

                indeg[nxt] -= 1 # on diminue le nb de dependance restante

                if indeg[nxt] == 0: # si plus de dep alors pret 
                    ready.append(nxt)

        if count != len(deps): # si on a pas traite toutes les taches 
            raise ValueError("Cycle détecté dans le graphe.")

    def _interferes(self, task1, task2):
        """
        Vérifie si deux tâches interfèrent (conditions de Bernstein).
        """
        
        # on transforme les listes en ensemble pour faire des intersections
        r1, w1 = set(task1.reads), set(task1.writes)
        r2, w2 = set(task2.reads), set(task2.writes)

        # interference si task1 ecrit ce que task2 lit ou 
        # task1 lit ce que task2 ecrit ou 
        # task1 ecrit ce que task2 ecrit 
        return bool((w1 & r2) or (r1 & w2) or (w1 & w2))

    #ajoute les dep de before vers after
    def _add_edge(self, before, after):
        self.final_deps[after].add(before) # after depend de before
        self.final_succ[before].add(after) # after devient le successeur de before

    def _build_max_parallel_graph(self):
        """
        Ajoute les dépendances nécessaires quand deux tâches interfèrent.
        """
        
        #recup nom des taches 
        names = [task.name for task in self.tasks]
        
        # on recup toutes les paires de taches 
        for i in range(len(names)):

            for j in range(i + 1, len(names)):
                #recup les objets de task
                a = self.task_map[names[i]]
                b = self.task_map[names[j]]

                if not self._interferes(a, b): # pas d interference
                    continue
                
                #on regarde qui est devant qui
                a_before_b = b.name in self.initial_reach[a.name]
                b_before_a = a.name in self.initial_reach[b.name]

                # si A devant B, A -> B
                if a_before_b and not b_before_a:

                    self._add_edge(a.name, b.name)
 
                # sinon si B avant A, B -> A
                elif b_before_a and not a_before_b:

                    self._add_edge(b.name, a.name)

                # si interference mais pas d ordre imposé, systeme indetermine
                else:

                    raise ValueError(
                        f"Interférence indéterminée entre {a.name} et {b.name}"
                    )

    def _topological_order(self):
        """
        Renvoie un ordre valide d'exécution des tâches.
        """
        # on copie les dependances 
        deps = {name: set(v) for name, v in self.final_deps.items()}
        # on compte les dependances entrantes 
        indeg = {name: len(deps[name]) for name in deps}
        # on prend les taches sans dependances
        ready = sorted([name for name in indeg if indeg[name] == 0])
        #liste de l ordre final
        order = []
        
        #pareil que les fonctions precedentes
        while ready:

            node = ready.pop(0)

            order.append(node)

            for nxt in sorted(self.final_succ[node]):

                indeg[nxt] -= 1

                if indeg[nxt] == 0:
                    ready.append(nxt)
                    ready.sort()

        return order #renvoie ordre trouvé

    def _execution_levels(self):
        """
        Regroupe les tâches par niveaux exécutables en parallèle.
        """
        
        #compte les dependances restantes 
        indeg = {name: len(self.final_deps[name]) for name in self.final_deps}
        # 1er niveau tache sans dependance
        current = sorted([name for name in indeg if indeg[name] == 0])
        #liste des nvx
        levels = []

        while current:
            #enregistre le nv courant
            levels.append(current[:])
            #on prepare le niveau suivant 
            nxt_level = []
            
            #on debloque les successeurs 
            for node in current:

                for nxt in sorted(self.final_succ[node]):

                    indeg[nxt] -= 1
                    #si succ n'attend plus rien -> niveau suivant 
                    if indeg[nxt] == 0:
                        nxt_level.append(nxt)

            current = sorted(nxt_level) # niveau suivant

        return levels

    # ------------------------------------------------------------
    # MÉTHODES DEMANDÉES (par le prof)
    # ------------------------------------------------------------
    
    #renvoie les dependances finales d une tache 
    def getDependencies(self, nomTache):
        return self.precedence[nomTache]

    def runSeq(self):
        """
        Exécution séquentielle des tâches.
        """
        order = self._topological_order() #ordre valide 

        for name in order: #calcul des taches dans l ordre
            self.task_map[name].run()

        return order

    def run(self):
        """
        Exécution parallèle par niveaux.
        """

        levels = self._execution_levels() #calcul les nvx paralleles

        for level in levels:

            threads = [] #liste des threads du nv courant 

            for name in level: # on parcourt les taches du niveau

                # on creer un thread qui execute la tache 
                t = threading.Thread(target=self.task_map[name].run)
                # on lance le thread 
                t.start()
                #on le stocke
                threads.append(t)
            # on att que toutes les taches du niveau soient finies 
            for t in threads:
                t.join()
        # on renvoie les niveaux executes
        return levels

    def draw(self):
        """
        Affiche graphiquement le graphe de dépendances.
        """

        import matplotlib.pyplot as plt
        import networkx as nx

        G = nx.DiGraph() # creation graphe oriente
        
        #chaque tache est un noeud
        for task in self.tasks:
            G.add_node(task.name)
        
        # on ajt les aretes du graphe final
        for after, deps in self.precedence.items():

            for before in deps:
                G.add_edge(before, after)
        
        #on recup les nvx pour placer les noeuds
        levels = self._execution_levels()
        #dico des positions des noeuds
        pos = {}
        
        #on place les noeuds
        #une colonne par nv
        # plusieurs lignes dans chaque nv
        for x, level in enumerate(levels):

            for i, node in enumerate(level):

                pos[node] = (x * 4, -i * 2)
        #dessine le graphe avec les fleches 
        nx.draw(G, pos, with_labels=True, node_size=3000, node_color="lightblue", arrows=True)

        plt.title("Graphe de précédence")
        plt.show()

    #faten ajout : fonction demandé par le prof 2.6 de l'énoncé 

    def detTestRnd(self, globals_dict, trials=5):
        """
        Test randomisé de déterminisme.
        """
        print("-> test déterminisme en cours...")
        for i in range(trials):

            test_values = {v: random.randint(1, 100) for task in self.tasks for v in (task.reads + task.writes)}

            for var, val in test_values.items(): globals_dict[var] = val
            self.runSeq()
            ref_state = {}
            for v in test_values:
                valeur = globals_dict.get(v)
                ref_state[v] = valeur

            for var, val in test_values.items(): globals_dict[var] = val
            self.run()
            par_state = {}
            for v in test_values:
                valeur = globals_dict.get(v)
                par_state[v] = valeur


            if ref_state != par_state:
                print(f"ÉCHEC : Différence détectée au test {i+1}")
                return False

        print(f"SUCCÈS : {trials} tests passés. Le système semble déterministe.")
        return True

    #faten ajout : fonction demandé par le prof 2.7 de l'énoncé

    def parCost(self, globals_dict, runs=10):
        """
        Compare le temps d'exécution séquentiel vs parallèle.
        """
        self.runSeq()

        t_seq = []
        for _ in range(runs):
            self._reset_globals(globals_dict) 
            start = time.time()
            self.runSeq()
            t_seq.append(time.time() - start)

        t_par = []
        for _ in range(runs):
            self._reset_globals(globals_dict)
            start = time.time()
            self.run()
            t_par.append(time.time() - start)

        avg_seq = sum(t_seq) / runs
        avg_par = sum(t_par) / runs

        print(f"\n--- Résultats sur {runs} itérations ---")
        print(f"Moyenne Séquentielle : {avg_seq:.6f}s")
        print(f"Moyenne Parallèle    : {avg_par:.6f}s")
        if avg_seq > avg_par:
            gain = ((avg_seq - avg_par) / avg_seq) * 100
            print(f"Gain : {gain:.2f}%")
        else:
            print("Le parallèle est plus lent (overhead des threads).")

    #faten ajout :Réinitialise automatiquement toutes les variables touchées par le système.

    def _reset_globals(self, globals_dict):

        all_vars = set()
        for task in self.tasks:
            all_vars.update(task.reads)
            all_vars.update(task.writes)
    
        for var in all_vars:
            if var in globals_dict:
                globals_dict[var] = 0