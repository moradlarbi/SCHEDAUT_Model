from pulp import LpProblem, LpMinimize, LpVariable, lpSum
import pandas as pd
import MySQLdb

def get_data_from_db():
    # Database connection details
    db = MySQLdb.connect(
        host="onnjomlc4vqc55fw.chr7pe7iynqr.eu-west-1.rds.amazonaws.com",
        user="e3v5vqvmprsuzjfi",
        passwd="a4dps9zul7ar1t85",
        db="pettlxfldr9yfyx0"
    )
    cursor = db.cursor()

    # Query data
    def fetch_table(query):
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columns)

    classes_df = fetch_table("SELECT name FROM class")
    profs_df = fetch_table("SELECT CONCAT(first_name,last_name) as nom FROM users where role='teacher'")
    salles_df = fetch_table("SELECT name FROM classRoom")
    matieres_df = fetch_table("SELECT name FROM course")
    matieres_classes_df = fetch_table("SELECT B.name AS class_name,C.name AS course_name FROM classCourse A LEFT JOIN class B ON A.idClass = B.id LEFT JOIN course C ON A.idCourse = C.id;")
    matieres_profs_df = fetch_table("SELECT CONCAT(B.first_name,B.last_name) AS prof_name, C.name AS course_name FROM teacherCourse A LEFT JOIN users B ON A.idTeacher = B.id LEFT JOIN course C ON A.idCourse = C.id;")

    db.close()

    return classes_df, profs_df, salles_df, matieres_df, matieres_classes_df, matieres_profs_df

def generate_schedule():
    # Fetch data from database
    (classes_df, profs_df, salles_df, matieres_df, matieres_classes_df, matieres_profs_df) = get_data_from_db()
    
    # Extract lists
    classes = classes_df['name'].tolist()
    profs = profs_df['nom'].tolist()
    salles = salles_df['name'].tolist()
    matieres = matieres_df['name'].tolist()
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
    creneaux = ['8h30-10h', '10h15-11h45', '13h-14h30', '14h45-16h15', '16h30-18h']

    matieres_classes = matieres_classes_df.groupby('class_name')['course_name'].apply(list).to_dict()
    matieres_profs = matieres_profs_df.groupby('prof_name')['course_name'].apply(list).to_dict()
    print(classes,profs,salles,matieres,matieres_classes,matieres_profs)
    # Optimization problem
    emploi_du_temps = LpProblem("Emploi_du_Temps", LpMinimize)
    X = LpVariable.dicts("Cours",
                         [(classe, matiere, jour, creneau, prof, salle)
                          for classe in classes
                          for matiere in matieres
                          for jour in jours
                          for creneau in creneaux
                          for prof in profs
                          for salle in salles],
                         cat='Binary')

    # Constraints (similar to your provided code)
    for salle in salles:
        for jour in jours:
            for creneau in creneaux:
                emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                         for classe in classes
                                         for matiere in matieres_classes[classe]
                                         for prof in profs
                                         if matiere in matieres_profs[prof]) <= 1

    for classe in classes:
        for jour in jours:
            for creneau in creneaux:
                emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                         for matiere in matieres_classes[classe]
                                         for prof in profs
                                         for salle in salles
                                         if matiere in matieres_profs[prof]) <= 1

    for prof in profs:
        for jour in jours:
            for creneau in creneaux:
                emploi_du_temps += lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                         for classe in classes
                                         for matiere in matieres_profs[prof]
                                         for salle in salles
                                         if matiere in matieres_classes[classe]) <= 1

    emploi_du_temps += lpSum(1 - lpSum(X[(classe, matiere, jour, creneau, prof, salle)]
                                       for matiere in matieres_classes[classe]
                                       for prof in profs
                                       for salle in salles
                                       if matiere in matieres_profs[prof])
                             for classe in classes for jour in jours for creneau in creneaux)

    # Solve problem
    emploi_du_temps.solve()

    # Extract results
    emploi_du_temps_resultat = []
    for (classe, matiere, jour, creneau, prof, salle), variable in X.items():
        if variable.varValue == 1:
            emploi_du_temps_resultat.append([classe, matiere, jour, creneau, prof, salle])

    return pd.DataFrame(emploi_du_temps_resultat, columns=['Classe', 'Matière', 'Jour', 'Créneau', 'Professeur', 'Salle'])
