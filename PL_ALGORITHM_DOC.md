"""
# Génération d'un Emploi du Temps Optimal avec PuLP et SQLAlchemy

Ce script a pour objectif de générer un emploi du temps optimal en fonction des contraintes suivantes :
- Une salle ne peut accueillir qu'une seule classe à la fois.
- Une classe ne peut suivre qu'une seule matière par créneau.
- Un enseignant ne peut enseigner qu'à une seule classe par créneau.
- Les salles doivent être assez grandes pour accueillir les étudiants.
- Les enseignants et les salles doivent être marqués comme actifs.

Les données sont stockées dans une base de données MySQL et manipulées avec SQLAlchemy. La solution optimale est calculée avec PuLP (bibliothèque de programmation linéaire).

## Étapes du script

1. Connexion à la base de données et chargement des données.
2. Transformation des données pour être utilisées dans le modèle d'optimisation.
3. Création et résolution du problème d'optimisation.
4. Extraction des résultats et mise en forme pour l'insertion dans la table `event`.
5. Insertion des résultats dans la base de données.

## Prérequis
- Python 3.10+
- Bibliothèques : `pandas`, `SQLAlchemy`, `PuLP`, `pymysql`
- Base de données MySQL configurée avec les tables nécessaires : `class`, `users`, `course`, `classRoom`, `classCourse`, `teacherCourse`, `event`.

## Variables et Tables Utilisées

### Tables
- `class`: Contient les informations sur les classes.
- `users`: Contient les informations sur les utilisateurs (enseignants inclus).
- `course`: Contient les informations sur les matières.
- `classRoom`: Contient les informations sur les salles.
- `classCourse`: Associe les matières à des classes.
- `teacherCourse`: Associe les matières à des enseignants.
- `event`: Résultats de l'emploi du temps généré (remplacés à chaque exécution).

### Variables Python
- `X`: Variable de décision binaire pour représenter si une matière est assignée à une classe, un enseignant et une salle pour un créneau donné.
- `creneaux`: Dictionnaire des horaires possibles.
- `capacites_salles`: Capacités des salles.
- `effectifs_classes`: Nombre d'étudiants par classe.
