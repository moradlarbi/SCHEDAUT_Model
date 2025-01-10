from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
from sqlalchemy import create_engine, text
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

# Charger les données
def charger_donnees():
    classes_query = "SELECT * FROM class"
    profs_query = "SELECT * FROM users WHERE role='teacher'"
    matieres_query = "SELECT * FROM course"
    salles_query = "SELECT * FROM classRoom"
    matieres_classes_query = "SELECT * FROM classCourse"
    matieres_profs_query = "SELECT * FROM teacherCourse"

    classes_df = pd.read_sql(classes_query, engine)
    profs_df = pd.read_sql(profs_query, engine)
    matieres_df = pd.read_sql(matieres_query, engine)
    salles_df = pd.read_sql(salles_query, engine)
    matieres_classes_df = pd.read_sql(matieres_classes_query, engine)
    matieres_profs_df = pd.read_sql(matieres_profs_query, engine)

    return classes_df, profs_df, matieres_df, salles_df, matieres_classes_df, matieres_profs_df

# Charger les données
classes_df, profs_df, matieres_df, salles_df, matieres_classes_df, matieres_profs_df = charger_donnees()

# Mappings
id_to_name_class = dict(zip(classes_df['id'], classes_df['name']))
id_to_name_course = dict(zip(matieres_df['id'], matieres_df['name']))
id_to_name_teacher = dict(zip(profs_df['id'], profs_df['first_name']))
id_to_name_classroom = dict(zip(salles_df['id'], salles_df['name']))

name_to_id_class = {v: k for k, v in id_to_name_class.items()}
name_to_id_course = {v: k for k, v in id_to_name_course.items()}
name_to_id_teacher = {v: k for k, v in id_to_name_teacher.items()}
name_to_id_classroom = {v: k for k, v in id_to_name_classroom.items()}

matieres_classes = {
    id_to_name_class[class_id]: [id_to_name_course[course_id] for course_id in courses]
    for class_id, courses in matieres_classes_df.groupby('idClass')['idCourse'].apply(list).to_dict().items()
}

matieres_profs = {
    id_to_name_teacher[teacher_id]: [id_to_name_course[course_id] for course_id in courses]
    for teacher_id, courses in matieres_profs_df.groupby('idTeacher')['idCourse'].apply(list).to_dict().items()
}

# Listes des entités
classes = list(id_to_name_class.values())
profs = list(id_to_name_teacher.values())
matieres = list(id_to_name_course.values())
salles = list(id_to_name_classroom.values())

# Créneaux simplifiés
creneaux = {
    0: ("08:00", "11:45"),
    1: ("13:00", "16:15"),
    2: ("16:30", "18:00"),
}

jours_ouvrables = pd.date_range(start="2024-09-01", end="2024-12-31", freq='B')
creneaux_par_jour = [(jour, creneau) for jour in jours_ouvrables for creneau in creneaux.keys()]

# Création du problème d'optimisation
emploi_du_temps = LpProblem("Emploi_du_Temps", LpMinimize)

# Variables de décision
X = LpVariable.dicts("Cours",
                     [(classe, matiere, jour, creneau, prof, salle)
                      for classe in classes
                      for matiere in matieres_classes.get(classe, [])
                      for jour, creneau in creneaux_par_jour
                      for prof in matieres_profs.keys()
                      for salle in salles
                      if matiere in matieres_profs[prof]],
                     cat='Binary')

# CONTRAINTES

# 1. Une salle peut accueillir une seule classe par créneau
for salle in salles:
    for jour, creneau in creneaux_par_jour:
        emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                 for classe in classes
                                 for matiere in matieres_classes.get(classe, [])
                                 for prof in profs
                                 if matiere in matieres_profs.get(prof, [])) <= 1

# 2. Une classe suit une seule matière par créneau
for classe in classes:
    for jour, creneau in creneaux_par_jour:
        emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                 for matiere in matieres_classes.get(classe, [])
                                 for prof in profs
                                 for salle in salles
                                 if matiere in matieres_profs.get(prof, [])) <= 1

# 3. Un prof ne peut enseigner qu'une seule classe par créneau
for prof in profs:
    for jour, creneau in creneaux_par_jour:
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
                         for classe in classes for jour, creneau in creneaux_par_jour)


emploi_du_temps.solve()

# Vérifier le statut
print("Statut de la solution :", LpStatus[emploi_du_temps.status])

# Extraction et manipulation des résultats
emploi_du_temps_resultat = []
for (classe, matiere, jour, creneau, prof, salle), variable in X.items():
    if variable.varValue == 1:
        emploi_du_temps_resultat.append([classe, matiere, jour.strftime('%Y-%m-%d'), creneau, prof, salle])

emploi_du_temps_df = pd.DataFrame(emploi_du_temps_resultat, columns=['Classe', 'Matière', 'Date', 'Créneau', 'Professeur', 'Salle'])

# Gestion des heures
emploi_du_temps_df['startTime'] = emploi_du_temps_df.apply(
    lambda row: f"{row['Date']} {creneaux[row['Créneau']][0]}", axis=1
)
emploi_du_temps_df['endTime'] = emploi_du_temps_df.apply(
    lambda row: f"{row['Date']} {creneaux[row['Créneau']][1]}", axis=1
)

# Convertir en datetime
emploi_du_temps_df['startTime'] = pd.to_datetime(emploi_du_temps_df['startTime'])
emploi_du_temps_df['endTime'] = pd.to_datetime(emploi_du_temps_df['endTime'])


# Mapper les noms vers leurs IDs
emploi_du_temps_df['idClass'] = emploi_du_temps_df['Classe'].map(name_to_id_class)
emploi_du_temps_df['idCourse'] = emploi_du_temps_df['Matière'].map(name_to_id_course)
emploi_du_temps_df['idTeacher'] = emploi_du_temps_df['Professeur'].map(name_to_id_teacher)
emploi_du_temps_df['idClassRoom'] = emploi_du_temps_df['Salle'].map(name_to_id_classroom)

# Vérifier si des mappings sont manquants
if emploi_du_temps_df[['idClass', 'idCourse', 'idTeacher', 'idClassRoom']].isnull().any().any():
    print("Erreur : Certains noms ne peuvent pas être mappés aux IDs.")
    print(emploi_du_temps_df[emploi_du_temps_df[['idClass', 'idCourse', 'idTeacher', 'idClassRoom']].isnull().any(axis=1)])
    raise ValueError("Certains noms ne sont pas mappés correctement aux IDs.")

# Filtrer les colonnes pour la table `event`
# Filtrer les colonnes nécessaires pour la table `event`
event_df = emploi_du_temps_df[['startTime', 'endTime', 'idClass', 'idCourse', 'idTeacher', 'idClassRoom']]

# Insérer dans la base
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE event;"))
    print("Table `event` vidée.")
event_df.to_sql('event', con=engine, if_exists='append', index=False)
print("Les données ont été insérées avec succès.")