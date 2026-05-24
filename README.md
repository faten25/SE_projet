# Système de Détection de Parallélisme Maximal (Conditions de Bernstein)

Ce projet de programmation système en Python implémente un moteur d'ordonnancement et d'analyse capable de maximiser le parallélisme d'un ensemble de tâches concurrentes. En s'appuyant sur les **conditions de Bernstein**, le système détecte les interférences sur les variables partagées afin de garantir une exécution parallèle déterministe et performante.

## Concepts Théoriques & Algorithmiques

L'application valide et optimise l'ordonnancement en vérifiant les trois conditions d'interférence de Bernstein pour chaque paire de tâches ($T_i, T_j$) :
1. **Pas de conflit Lecture/Écriture :** $R(T_i) \cap W(T_j) = \emptyset$
2. **Pas de conflit Écriture/Lecture :** $W(T_i) \cap R(T_j) = \emptyset$
3. **Pas de conflit Écriture/Écriture :** $W(T_i) \cap W(T_j) = \emptyset$

Si ces conditions sont respectées et qu'aucune contrainte de précédence initiale ne s'y oppose, le système permet aux tâches d'être exécutées simultanément via des **threads**.

## Fonctionnalités Clés

* **Validation du Graphe de Précédence :** Analyse automatique du graphe de départ pour s'assurer de l'absence de cycles (détection de deadlocks) et validation de la structure.
* **Ordonnancement Parallèle Dynamique :** Exécution des tâches prêtes au sein de threads Python (`threading`), réduisant le temps global d'exécution sur les machines multi-cœurs.
* **Analyse de Performance (`parCost`) :** Benchmark intégré mesurant et comparant le temps moyen d'exécution séquentiel face au temps parallèle, mettant en évidence le coût de l'overhead des threads.
* **Test de Déterminisme Automatisé (`detTestRnd`) :** Simulation d'exécutions multiples avec l'introduction d'aléatoire pour valider empiriquement que les résultats des variables globales restent invariants et déterministes.

## Outils utilisés

* **Langage :** Python 3
* **Bibliothèques Natives :** `threading` (parallélisation), `time` (calcul de performance), `copy` (gestion des états mémoire).

## Structure du Dépôt

```text
Max-Parallelism-Task-System/
├── maxpar.py        # Moteur principal (Classes Task et TaskSystem)
├── test_maxpar.py   # Script de test avec un jeu de 7 tâches (T1 à T5, TSomme, TProduit)
└── README.md        # Présentation et documentation du projet
