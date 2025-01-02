from pulp import LpProblem, LpMinimize, LpVariable, lpSum
import pandas as pd
from datetime import datetime

# Charger les données générées
data_path = 'C:/Users/PC/Desktop/Projet App 1/large_dataset.xlsx'
classes_df = pd.read_excel(data_path, sheet_name='Classes')
profs_df = pd.read_excel(data_path, sheet_name='Profs')
salles_df = pd.read_excel(data_path, sheet_name='Salles')
matieres_df = pd.read_excel(data_path, sheet_name='Matieres')
matieres_classes_df = pd.read_excel(data_path, sheet_name='Matieres_Classes')
matieres_profs_df = pd.read_excel(data_path, sheet_name='Matieres_Profs')

# Extraire les listes des entités
classes = classes_df['Classe'].tolist()
profs = profs_df['Professeur'].tolist()
salles = salles_df['Salle'].tolist()
matieres = matieres_df['Matiere'].tolist()

# Définir une plage d'années scolaires et générer des créneaux
annee_scolaire = pd.date_range(start="2024-09-01", end="2024-09-30", freq='B')  # Jours ouvrables
jours_ouvrables = annee_scolaire[annee_scolaire.dayofweek < 5]  # Lundi à Vendredi
creneaux = [(jour, creneau) for jour in jours_ouvrables for creneau in range(5)]  # 5 créneaux par jour

# Créer les dictionnaires des matières par classe et prof
matieres_classes = matieres_classes_df.groupby('Classe')['Matiere'].apply(list).to_dict()
matieres_profs = matieres_profs_df.groupby('Professeur')['Matiere'].apply(list).to_dict()

# Création du problème d'optimisation
emploi_du_temps = LpProblem("Emploi_du_Temps", LpMinimize)

# Variables de décision : 1 si un cours est assigné à un jour et créneau donné
X = LpVariable.dicts("Cours",
                     [(classe, matiere, jour, creneau, prof, salle) 
                      for classe in classes 
                      for matiere in matieres 
                      for jour, creneau in creneaux 
                      for prof in profs 
                      for salle in salles], 
                     cat='Binary')

# CONTRAINTES

# 1. Une salle peut accueillir une seule classe, une matière et un prof par créneau et jour
for salle in salles:
    for jour, creneau in creneaux:
        emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                 for classe in classes 
                                 for matiere in matieres_classes[classe]
                                 for prof in profs 
                                 if matiere in matieres_profs[prof]) <= 1

# 2. Une classe suit une seule matière par créneau et jour
for classe in classes:
    for jour, creneau in creneaux:
        emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                 for matiere in matieres_classes[classe] 
                                 for prof in profs 
                                 for salle in salles
                                 if matiere in matieres_profs[prof]) <= 1

# 3. Un prof ne peut enseigner qu'une seule classe à un créneau donné
for prof in profs:
    for jour, creneau in creneaux:
        emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                 for classe in classes 
                                 for matiere in matieres_profs[prof] 
                                 for salle in salles
                                 if matiere in matieres_classes[classe]) <= 1

# OBJECTIF : Minimiser les créneaux vides
emploi_du_temps += lpSum(1 - lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                   for matiere in matieres_classes[classe] 
                                   for prof in profs 
                                   for salle in salles
                                   if matiere in matieres_profs[prof])
                         for classe in classes for jour, creneau in creneaux)

# Résoudre le problème
emploi_du_temps.solve()

# Extraire les résultats et les afficher sous forme de tableau
emploi_du_temps_resultat = []
for (classe, matiere, jour, creneau, prof, salle), variable in X.items():
    if variable.varValue == 1:
        emploi_du_temps_resultat.append([classe, matiere, jour.strftime('%Y-%m-%d'), creneau, prof, salle])

# Convertir les résultats en DataFrame Pandas
emploi_du_temps_df = pd.DataFrame(emploi_du_temps_resultat, columns=['Classe', 'Matière', 'Date', 'Créneau', 'Professeur', 'Salle'])

# Exporter les résultats
emploi_du_temps_df.to_csv('emploi_du_temps.csv', index=False)

# Afficher un aperçu
print(emploi_du_temps_df.head())
