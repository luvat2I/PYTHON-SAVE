import pyodbc
import pysolr
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import re
# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SolrClient:
    def __init__(self, solr_url, username, password):
        self.solr_url = solr_url
        self.username = username
        self.password = password

    def search(self, query, rows=10):
        # Effectuer la recherche dans Solr avec désactivation de la vérification SSL
        response = requests.get(
            f"{self.solr_url}/select",
            params={'q': query, 'rows': rows},
            auth=HTTPBasicAuth(self.username, self.password),
            verify=False  # Désactiver la vérification SSL
        )
        response.raise_for_status()  # Vérifier si la requête a réussi
        return response.json()['response']['docs']

    def display_results(self, results):
        # Afficher les résultats
        # print(f"Nombre de résultats: {len(results)}")
        if not results:
            print(f"SOLR > pas dans solr")
        else:
            for result in results:
                clean_id = self.clean_document_id(f"{result['id']}")
                print(f"SOLR > ID:{clean_id}")
                #print(f"SOLR > Time:{result.get('processTimeStamp', 'N/A')}")
                #print(f"SOLR > jsonObject:{result.get('jsonObject', 'N/A')}")
                data_jsonObject =  f"{result.get('jsonObject', 'N/A')}"
                data = json.loads(data_jsonObject)
                modification_date = data['objectDescription'].get('objectFilterDate')
                if modification_date:
                    print("Date de modification :", modification_date)
                else:
                    print("La clé 'modificationDateTime' n'existe pas.")
    def clean_document_id(self, document_id: str) -> str:
        match = re.search(r'-([^-]+)$', document_id, re.IGNORECASE)
        if match:
            return match.group(1)
        return document_id  # Retourne l'ID original si le pattern ne correspond pas

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
    db_host = 'ydgluva2022'
    db_user = 'sa'
    db_password = 'passwordT2I'
    db_database = 'PRD_xlinedta001_001'
    solr_hostname = 'ydgluva2022:8984'
    solr_tenant = '001'
    solr_url = f'https://{solr_hostname}/solr/{solr_tenant}'  # Remplacez par l'URL de votre serveur Solr
    solr_user = 'prd-dft-svc'  # Remplacez par votre nom d'utilisateur
    solr_password = 'prddftsvcT2I'  # Remplacez par votre mot de passe
    db = DatabaseConnection(db_host, db_database, db_user, db_password)
    db.connect()
    db.validate_connection()
    client = SolrClient(solr_url, solr_user, solr_password)
    db_query = 'SELECT * FROM ARG0CPP;'
    db_results = db.execute_query(db_query)
    for row in db_results:
        print(f"DB > ID: {row.DD1rA}")
        print(f"DB > Time: {row.DDr67A}")
        solr_query = f'id:XECM-DOCUMENT--{solr_tenant}-{row.DD1rA}'  # Remplacez par votre requête de recherche
        #solr_query = 'id:[XECM-DOCUMENT--{row.DD1RA}-{row.DD1RA} TO *] AND id:*FOLD*'  # Remplacez par votre requête de recherche
        solr_results = client.search(solr_query)
        client.display_results(solr_results)
    db.close()