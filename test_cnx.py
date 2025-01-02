from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime

# Configuration de la base de données MySQL
db_user = 'e3v5vqvmprsuzjfi'
db_password = 'a4dps9zul7ar1t85'
db_host = 'onnjomlc4vqc55fw.chr7pe7iynqr.eu-west-1.rds.amazonaws.com'
db_port = '3306'
db_name = 'pettlxfldr9yfyx0'

# Connexion à MySQL
engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# Requêtes SQL pour charger les données
classes_query = "SELECT * FROM class"
profs_query = "SELECT * FROM users WHERE role='teacher'"
matieres_query = "SELECT * FROM course"
salles_query = "SELECT * FROM classRoom"
matieres_classes_query = "SELECT * FROM classCourse"
matieres_profs_query = "SELECT * FROM teacherCourse"

# Charger les données dans des DataFrames
classes_df = pd.read_sql(classes_query, engine)
profs_df = pd.read_sql(profs_query, engine)
matieres_df = pd.read_sql(matieres_query, engine)
salles_df = pd.read_sql(salles_query, engine)
matieres_classes_df = pd.read_sql(matieres_classes_query, engine)
matieres_profs_df = pd.read_sql(matieres_profs_query, engine)

# Créer des mappings (IDs vers noms)
id_to_name_class = dict(zip(classes_df['id'], classes_df['name']))
id_to_name_course = dict(zip(matieres_df['id'], matieres_df['name']))
id_to_name_teacher = dict(zip(profs_df['id'], profs_df['first_name']))

# Traduire les données de la BDD en noms
matieres_classes = {
    id_to_name_class[class_id]: [id_to_name_course[course_id] for course_id in courses]
    for class_id, courses in matieres_classes_df.groupby('idClass')['idCourse'].apply(list).to_dict().items()
}

matieres_profs = {
    id_to_name_teacher[teacher_id]: [id_to_name_course[course_id] for course_id in courses]
    for teacher_id, courses in matieres_profs_df.groupby('idTeacher')['idCourse'].apply(list).to_dict().items()
}

# Extraire les listes des entités
classes = list(id_to_name_class.values())
profs = list(id_to_name_teacher.values())
matieres = list(id_to_name_course.values())
salles = salles_df['name'].tolist()

# Vérifier les données traduites
print("Classes :", classes)
print("Profs :", profs)
print("Matières :", matieres)
print("Salles :", salles)
print("Matières par classe :", matieres_classes)
print("Matières par prof :", matieres_profs)

# Définir une plage d'années scolaires et générer des créneaux
annee_scolaire = pd.date_range(start="2024-09-01", end="2024-09-30", freq='B')  # Jours ouvrables
jours_ouvrables = annee_scolaire[annee_scolaire.dayofweek < 5]  # Lundi à Vendredi
creneaux = [(jour, creneau) for jour in jours_ouvrables for creneau in range(5)]  # 5 créneaux par jour

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
                                 for matiere in matieres_classes.get(classe, [])
                                 for prof in profs
                                 if matiere in matieres_profs.get(prof, [])) <= 1

# 2. Une classe suit une seule matière par créneau et jour
for classe in classes:
    for jour, creneau in creneaux:
        emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                 for matiere in matieres_classes.get(classe, [])
                                 for prof in profs
                                 for salle in salles
                                 if matiere in matieres_profs.get(prof, [])) <= 1

# 3. Un prof ne peut enseigner qu'une seule classe à un créneau donné
for prof in profs:
    for jour, creneau in creneaux:
        emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                 for classe in classes
                                 for matiere in matieres_profs.get(prof, [])
                                 for salle in salles
                                 if matiere in matieres_classes.get(classe, [])) <= 1

# OBJECTIF : Minimiser les créneaux vides
emploi_du_temps += lpSum(1 - lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                   for matiere in matieres_classes.get(classe, [])
                                   for prof in profs
                                   for salle in salles
                                   if matiere in matieres_profs.get(prof, []))
                         for classe in classes for jour, creneau in creneaux)

# Résoudre le problème
emploi_du_temps.solve()

# Vérifier le statut de la solution
print("Statut de la solution :", LpStatus[emploi_du_temps.status])

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
if not emploi_du_temps_df.empty:
    print(emploi_du_temps_df.head())
else:
    print("Aucune solution trouvée, le fichier est vide.")
