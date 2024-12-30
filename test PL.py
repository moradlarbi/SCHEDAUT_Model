from pulp import LpProblem, LpMinimize, LpVariable, lpSum
import pandas as pd
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
jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
creneaux = ['8h30-10h', '10h15-11h45', '13h-14h30', '14h45-16h15', '16h30-18h']

# Créer les dictionnaires des matières par classe et prof
matieres_classes = matieres_classes_df.groupby('Classe')['Matiere'].apply(list).to_dict()
matieres_profs = matieres_profs_df.groupby('Professeur')['Matiere'].apply(list).to_dict()

# Création du problème d'optimisation
emploi_du_temps = LpProblem("Emploi_du_Temps", LpMinimize)

# Variables de décision : 1 si un cours est assigné à un créneau, jour, prof, salle, sinon 0
X = LpVariable.dicts("Cours",
                     [(classe, matiere, jour, creneau, prof, salle) 
                      for classe in classes 
                      for matiere in matieres 
                      for jour in jours
                      for creneau in creneaux 
                      for prof in profs 
                      for salle in salles], 
                     cat='Binary')

# CONTRAINTES

# 1. Une salle peut accueillir une seule classe, une matière et un prof par créneau et jour
for salle in salles:
    for jour in jours:
        for creneau in creneaux:
            emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                     for classe in classes 
                                     for matiere in matieres_classes[classe]
                                     for prof in profs 
                                     if matiere in matieres_profs[prof]) <= 1

# 2. Une classe suit une seule matière par créneau et jour
for classe in classes:
    for jour in jours:
        for creneau in creneaux:
            emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                     for matiere in matieres_classes[classe] 
                                     for prof in profs 
                                     for salle in salles
                                     if matiere in matieres_profs[prof]) <= 1

# 3. Un prof ne peut enseigner qu'une seule classe à un créneau donné
for prof in profs:
    for jour in jours:
        for creneau in creneaux:
            emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                     for classe in classes 
                                     for matiere in matieres_profs[prof] 
                                     for salle in salles
                                     if matiere in matieres_classes[classe]) <= 1

# OBJECTIF : Minimiser les créneaux vides sur toute la semaine
emploi_du_temps += lpSum(1 - lpSum(X[(classe, matiere, jour, creneau, prof, salle)] 
                                   for matiere in matieres_classes[classe] 
                                   for prof in profs 
                                   for salle in salles
                                   if matiere in matieres_profs[prof])
                         for classe in classes for jour in jours for creneau in creneaux)

# Résoudre le problème
emploi_du_temps.solve()

# Extraire les résultats et les afficher sous forme de tableau
emploi_du_temps_resultat = []
for (classe, matiere, jour, creneau, prof, salle), variable in X.items():
    if variable.varValue == 1:
        emploi_du_temps_resultat.append([classe, matiere, jour, creneau, prof, salle])

# Convertir les résultats en DataFrame Pandas
emploi_du_temps_df = pd.DataFrame(emploi_du_temps_resultat, columns=['Classe', 'Matière', 'Jour', 'Créneau', 'Professeur', 'Salle'])

# Afficher le tableau des résultats
emploi_du_temps_df.to_csv('C:\Users\PC\Desktop\Projet App 1\SCHEDAUT_Model\test_resultat.csv')