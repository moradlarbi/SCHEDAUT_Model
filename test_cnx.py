from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
from sqlalchemy import text


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
id_to_name_classroom = dict(zip(salles_df['id'], salles_df['name']))



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
salles = list(id_to_name_classroom.values())

"""# Vérifier les données traduites
print("Classes :", classes)
print("Profs :", profs)
print("Matières :", matieres)
print("Salles :", salles)
print("Matières par classe :", matieres_classes)
print("Matières par prof :", matieres_profs)
"""
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


# Créer des mappings (noms vers IDs)
id_class_mapping = dict(zip(classes_df['name'], classes_df['id']))
id_teacher_mapping = dict(zip(profs_df['first_name'], profs_df['id']))
id_course_mapping = dict(zip(matieres_df['name'], matieres_df['id']))
id_classroom_mapping = dict(zip(salles_df['name'], salles_df['id']))


creneau_horaires = {
    0: ("08:30", "10:00"),
    1: ("10:15", "11:45"),
    2: ("13:00", "14:30"),
    3: ("14:45", "16:15"),
    4: ("16:30", "18:00")
}

# Calculer les colonnes startTime et endTime
emploi_du_temps_df['startTime'] = emploi_du_temps_df.apply(
    lambda row: f"{row['Date']} {creneau_horaires[row['Créneau']][0]}", axis=1
)
emploi_du_temps_df['endTime'] = emploi_du_temps_df.apply(
    lambda row: f"{row['Date']} {creneau_horaires[row['Créneau']][1]}", axis=1
)

# Convertir en format datetime
emploi_du_temps_df['startTime'] = pd.to_datetime(emploi_du_temps_df['startTime'])
emploi_du_temps_df['endTime'] = pd.to_datetime(emploi_du_temps_df['endTime'])

# Mapper les noms vers leurs IDs
emploi_du_temps_df['idClass'] = emploi_du_temps_df['Classe'].map(id_class_mapping)
emploi_du_temps_df['idCourse'] = emploi_du_temps_df['Matière'].map(id_course_mapping)
emploi_du_temps_df['idTeacher'] = emploi_du_temps_df['Professeur'].map(id_teacher_mapping)
emploi_du_temps_df['idClassRoom'] = emploi_du_temps_df['Salle'].map(id_classroom_mapping)

# Vérifier si des mappings sont manquants
if emploi_du_temps_df[['idClass', 'idCourse', 'idTeacher', 'idClassRoom']].isnull().any().any():
    print("Erreur : Certains noms ne peuvent pas être mappés aux IDs.")
    print(emploi_du_temps_df[emploi_du_temps_df[['idClass', 'idCourse', 'idTeacher', 'idClassRoom']].isnull().any(axis=1)])
    raise ValueError("Certains noms ne sont pas mappés correctement aux IDs.")

# Filtrer les colonnes nécessaires pour la table `event`
event_df = emploi_du_temps_df[['startTime', 'endTime', 'idClass', 'idCourse', 'idTeacher', 'idClassRoom']]


# Vider la table `event` avant insertion
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE event;"))
    print("suppression OK")
# Insérer les données dans la table `event`
event_df.to_sql('event', con=engine, if_exists='append', index=False)

# Vérification finale
print("Les données ont été insérées avec succès dans la table `event`.")