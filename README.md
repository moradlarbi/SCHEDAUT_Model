# Timetable Optimization System

## Description

Ce projet est un système d'optimisation d'emploi du temps conçu pour gérer automatiquement les emplois du temps des classes, professeurs, matières et salles, tout en respectant un ensemble de contraintes.  
L'algorithme utilise **Python**, **PuLP** (pour la programmation linéaire) et **MySQL** comme base de données.  

---

## Fonctionnalités

- Génération automatique d'emplois du temps optimisés.
- Gestion des contraintes, comme :
  - Une seule classe par salle et créneau.
  - Une seule matière par créneau pour une classe.
  - Un professeur ne peut enseigner qu'une classe par créneau.
  - Capacité des salles respectée pour chaque classe.
  - Gestion des enseignants et des salles actifs uniquement.
- Support des créneaux horaires fixes et des jours ouvrables.
- Exportation des emplois du temps dans une table MySQL pour une utilisation ultérieure.

---

## Technologies Utilisées

- **Langage :** Python 3.x
- **Bibliothèque d'optimisation :** PuLP
- **Base de données :** MySQL
- **Bibliothèque de connexion DB :** SQLAlchemy + pymysql
- **Manipulation de données :** Pandas

---

## Installation

### Prérequis

- Python 3.10 ou supérieur
- MySQL installé et configuré
- Bibliothèques Python nécessaires :  
  ```bash
  pip install pulp sqlalchemy pandas pymysql
