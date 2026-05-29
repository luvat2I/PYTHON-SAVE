import pyodbc

class DatabaseConnection:
    def __init__(self, server, database, user, password):
        self.server = server
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        

    def connect(self):
        """Établit une connexion à la base de données sans vérifier le certificat SSL."""
        try:
            connection_string = (
                f'DRIVER={{ODBC Driver 18 for SQL Server}};'
                f'SERVER={self.server};'
                f'DATABASE={self.database};'
                f'UID={self.user};'
                f'PWD={self.password};'
                'TrustServerCertificate=yes;'  # Désactive la vérification SSL
            )
            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
            print("Connexion réussie à la base de données.")
        except pyodbc.Error as e:
            print(f"Erreur de connexion à la base de données: {e}")

    def validate_connection(self):
        """Valide si la connexion est active."""
        if self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1;")  # Exécute une requête simple
                print("La connexion est valide.")
            except pyodbc.Error as e:
                print(f"La connexion n'est pas valide: {e}")
        else:
            print("Aucune connexion établie.")

    def execute_query(self, query, params=None):
        """Exécute une requête SQL et retourne un nombre spécifié de lignes."""
        if params is None:
            params = ()
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()  # Retourne tous les résultats
        except pyodbc.Error as e:
            print(f"Une erreur est survenue : {e}")
            return None

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.connection:
            self.connection.close()
            print("Connexion fermée.")

# Utilisation de la classe
if __name__ == "__main__":
    #host = input("Entrez l'hôte de la base de données (ex: localhost): ")
    #user = input("Entrez le nom d'utilisateur: ")
    #password = input("Entrez le mot de passe: ")
    #database = input("Entrez le nom de la base de données: ")
    host = 'ydgluva2022'
    user = 'sa'
    password = 'passwordT2I'
    database = 'PRD_xlinedta001_001'
    db = DatabaseConnection(host, database, user, password)
    db.connect()
    db.validate_connection()
    select_query = 'SELECT * FROM ARG0CPP;'
    results = db.execute_query(select_query)
    for row in results:
        print(row)
    db.close()