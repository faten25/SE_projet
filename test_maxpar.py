from maxpar import Task, TaskSystem

# Variables globales utilisées par les tâches
X = 0
Y = 0
A = 0
B = 0
C = 0
Z = 0
D = 0


# ------------------------------------------------------------
# Fonctions associées aux tâches
# ------------------------------------------------------------

def runT1():
    global X
    X = 1
    print("T1 exécutée : X =", X)


def runT2():
    global Y, X, A
    Y = X + A
    print("T2 exécutée : Y =", Y)


def runT3():
    global A
    A = 3
    print("T3 exécutée : A =", A)


def runT4():
    B = A + 4
    print("T4 exécutée : B =", B)


def runT5():
    global C
    C = 5
    print("T5 exécutée : C =", C)


def runTSomme():
    global Z, X, Y
    Z = X + Y
    print("TSomme exécutée : Z =", Z)


def runTProduit():
    global D, C, Z
    D = C * Z
    print("TProduit exécutée : D =", D)


# ------------------------------------------------------------
# Création des tâches
# ------------------------------------------------------------

t1 = Task("T1", writes=["X"], run=runT1)
t2 = Task("T2", reads=["X", "A"], writes=["Y"], run=runT2)
t3 = Task("T3", writes=["A"], run=runT3)
t4 = Task("T4", reads=["A"], writes=["B"], run=runT4)
t5 = Task("T5", writes=["C"], run=runT5)

tSomme = Task("TSomme", reads=["X", "Y"], writes=["Z"], run=runTSomme)
tProduit = Task("TProduit", reads=["C", "Z"], writes=["D"], run=runTProduit)


tasks = [t1, t2, t3, t4, t5, tSomme, tProduit]


# ------------------------------------------------------------
# Graphe de précédence initial
# ------------------------------------------------------------

# ce dictionnaire donne les contraintes de depart si changement alors le graphe change aussi 

# ATTENTION cas ou ca ne marche pas -> si deux taches interferent et que le graphe initial ne dit pas dans quel sens les ordonner alors erreur #

precedence = {
    "T1": [],
    "T2": ["T1", "T3"],
    "T3": [],
    "T4": ["T3"],
    "T5": [],
    "TSomme": ["T2"],
    "TProduit": ["T5", "TSomme"]
}


# ------------------------------------------------------------
# Création du système
# ------------------------------------------------------------

system = TaskSystem(tasks, precedence)


print("\nDépendances finales :\n")

for task in tasks:
    print(task.name, "<-", system.getDependencies(task.name))


print("\nExécution séquentielle\n")
system.runSeq()

print("\nExécution parallèle\n")
system.run()

print("\nComparaison des performances\n")
system.parCost(globals(), runs=10) #faten ajout : pour lancer la fonction du prof

print("\nTest de déterminisme\n")
system.detTestRnd(globals(), trials=5) #faten ajout : pour lancer la fonction du prof


print("\nAffichage du graphe\n")
system.draw() # je lai mis à la fin pour que tout fonctionne et que tout s'afficbe 
