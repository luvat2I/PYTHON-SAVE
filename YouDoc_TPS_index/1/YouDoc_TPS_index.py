#pyinstaller verif_index.spec
import os
import pyodbc
import pysolr
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import re
import time
import logging
import configparser
from datetime import datetime, timedelta

# import de mes dev
import log_aff

time_pause = 0

# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lecture du fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Récupération de la configuration des log et du print (du fichier ini) 
enable_logging = config.getboolean('logging', 'enable_logging')
log_folder = config['logging']['log_folder']
enable_print = config.getboolean('logging', 'enable_print')

# Récupération des informations des connexion BDD (du fichier ini)
sgbd_db_type = config['SGBD']['db_type']
sgbd_driver = config['SGBD']['db_driver']
sgbd_server = config['SGBD']['db_server']
sgbd_port = config['SGBD']['db_port']
sgbd_username = config['SGBD']['db_username']
sgbd_password = config['SGBD']['db_password']
sgbd_database = config['SGBD']['db_database']
sgbd_data = config['SGBD']['db_data']
# Récupération des informations des connexion SOLR (du fichier ini)
solr_hostname = config['SOLR']['solr_hostname']
solr_username = config['SOLR']['solr_username']
solr_password = config['SOLR']['solr_password']
solr_tenant = config['SOLR']['solr_tenant']

# Récupération des informations de paramétrage des traitements (du fichier ini) 
traitement_type = config['traitement']['traitement_type']
DOCUMENT_QUERY_recup = config['traitement']['DOCUMENT_QUERY_recup']


if enable_logging:
	os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log

# Configure le log si activé
if enable_logging:
	log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
	logging.basicConfig(filename=log_filename, level=logging.INFO, 
						format='%(message)s')
else:
	logging.disable(logging.CRITICAL)  # Désactiver le logging si non activé


class SolrClient: # classe qui interroge solr
	def __init__(self, solr_url, username, password): # initialisation de la connexion
		self.solr_url = solr_url
		self.username = username
		self.password = password

	def search(self, query, rows=10): # Effectuer la recherche dans Solr avec désactivation de la vérification SSL
		response = requests.get(
			f"{self.solr_url}/select",
			params={'q': query, 'rows': rows},
			auth=HTTPBasicAuth(self.username, self.password),
			verify=False  # Désactiver la vérification SSL
		)
		response.raise_for_status()  # Vérifier si la requête a réussi
		return response.json()['response']['docs']
	
	
		
	def display_results(self, results):
		var_retour = "N"
		# Afficher les résultats
		# print(f"Nombre de résultats: {len(results)}")
		if not results:
			# print(f"SOLR > pas dans solr")
			var_retour = "N"
		else:
			for result in results:
				clean_id = self.clean_document_id(f"{result['id']}")
				# print(f"SOLR > ID:{clean_id}")
				var_retour = "I"
				data_jsonObject =  f"{result.get('jsonObject', 'N/A')}"
				data = json.loads(data_jsonObject)
				modification_date = data['objectDescription'].get('objectFilterDate')
				# if modification_date:
					# print("Date de modification :", modification_date)
				# else:
					# print("La clé 'modificationDateTime' n'existe pas.")
		return var_retour
		
	def clean_document_id(self, document_id: str) -> str:
		match = re.search(r'-([^-]+)$', document_id, re.IGNORECASE)
		if match:
			return match.group(1)
		return document_id  # Retourne l'ID original si le pattern ne correspond pas

class DatabaseConnection: #classe de connexion SGBD SQL et DB2
	def __init__(self, db_type,driver, server, port, database, user, password):
		self.db_type = db_type
		self.driver = driver
		self.server = server
		self.port = port
		self.database = database
		self.user = user
		self.password = password
		self.connection = None

	def connect(self): # Connexion au SGBD
		try:
		
			if self.db_type == 'DB2': # connexion DB2
				connection_string = (
					f'DRIVER={{iSeries access ODBC Driver}};'
					f'SYSTEM={self.server};'
					f'PORT={self.port};'
					f'DATABASE={self.database};'
					f'PROTOCOL=TCPIP;'
					f'UID={self.user};'
					f'PWD={self.password};'
				)
			else: # connexion SQL
				connection_string = (
					f'DRIVER={{{self.driver}}};'
					f'SERVER={self.server};'
					f'PORT={self.port};'
					f'DATABASE={self.database};'
					f'UID={self.user};'
					f'PWD={self.password};'
					'TrustServerCertificate=yes;'
				)
			self.connection = pyodbc.connect(connection_string)
			self.cursor = self.connection.cursor()
			print("Connexion réussie à la base de données.")
		except pyodbc.Error as e:
			print(f"Erreur de connexion à la base de données: {e}")

	def validate_connection(self): # Valide si la connexion est active.
		if self.connection:
			try:
				cursor = self.connection.cursor()
				if sgbd_db_type == 'DB2':
					cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
				else :
					cursor.execute("SELECT 1;")
				print("La connexion est valide.")
				
			except pyodbc.Error as e:
				print(f"La connexion n'est pas valide: {e}")
		else:
			print("Aucune connexion établie.")

	def execute_query(self, query, params=None): # Exécute une requête SQL et retourne tous les résultats
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchall()  # Retourne tous les résultats
		except pyodbc.Error as e:
			print(f"Une erreur est survenue : {e}")
			return None
			
	def execute_query_count(self, query, params=None): # Exécute une requête SQL de count et retourne un unique résultat
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchone()[0]  # Retourne un unique résultat
		except pyodbc.Error as e:
			print(f"Une erreur est survenue : {e}")
			return None
			
	def execute_query_save(self, query, params=None): # Exécute une requête d'update et commit
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			self.connection.commit() # Commit le résultat
		except pyodbc.Error as e:
			print(f"Une erreur est survenue : {e}")
			return None

	def close(self): # Cloture la co
		if self.connection:
			self.connection.close()
			print("Connexion fermée.")
			
def routine() :

	global verif_continue
	global DOCUMENT_QUERY
	global  ECM_DOCIDX_TIME
	
	print(f"Attend un DOC_IDX")
	db_query = f"select top 1 * from ECM_DOCIDX WITH (NOLOCK);"
	while verif_continue == True:
		try:
			db_results = db.execute_query(db_query)
			for row in db_results:
				DOCUMENT_QUERY = f"{row.DOCUMENT_ID}"
				# Obtenir l'heure actuelle
				maintenant = datetime.now()
				ECM_DOCIDX_TIME = maintenant.strftime("%Y-%m-%d %H:%M:%S") + f".{maintenant.microsecond // 1000:03d}"
				db_session = f"{row.SESSION_ID}"
			if DOCUMENT_QUERY != "":
				verif_continue = False
				log_aff.log_enreg(f"{DOCUMENT_QUERY};{ECM_DOCIDX_TIME};ECM_DOCIDX")
		except Exception as e:
			print(f"Erreur en Exception : {e}")
			
	print(f"Attend un TOBJDESC")
	verif_continue2 = True
	TOBJDESC_TIME = ""
	
	db_query_2 = f"select * from TOBJDESC WITH (NOLOCK) where INDEXATION_ID = 'XECM-{traitement_type}--{solr_tenant}-{DOCUMENT_QUERY}' ;"
	while verif_continue2 == True:
		try:
			db_results = db.execute_query(db_query_2)
			for row in db_results:
				maintenant = datetime.now()
				TOBJDESC_TIME = maintenant.strftime("%Y-%m-%d %H:%M:%S") + f".{maintenant.microsecond // 1000:03d}"
			if TOBJDESC_TIME != "":
				verif_continue2 = False
				log_aff.log_enreg(f"{DOCUMENT_QUERY};{TOBJDESC_TIME};TOBJDESC")
		except Exception as e:
			print(f"Erreur en Exception : {e}")
	
	print(f"Attend SOLR")
	verif_continue4 = True
	solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{DOCUMENT_QUERY}"
	# Preparation à la connexion SOLR
	solr_url = f'https://{solr_hostname}/solr/{solr_tenant}' # creation adresse de connexion
	client = SolrClient(solr_url, solr_username, solr_password) # creation de la classe solr
	SOLR_TIME = ""
	while verif_continue4 == True:
		try:
			
			solr_results = client.search(solr_query)
			retour = client.display_results(solr_results)
			if f"{retour}" == "I":
				maintenant = datetime.now()
				SOLR_TIME = maintenant.strftime("%Y-%m-%d %H:%M:%S") + f".{maintenant.microsecond // 1000:03d}"
			if SOLR_TIME != "":
				verif_continue4 = False
				log_aff.log_enreg(f"{DOCUMENT_QUERY};{SOLR_TIME};SOLR GOOD")
			
		except Exception as e:
			print(f"Erreur en Exception : {e}")
	
	print(f"Recup ARG0CPP")
	db_query_4 = f"select top 1 * from ARG0CPP WITH (NOLOCK) where DD1rA = '{DOCUMENT_QUERY}' ;"
	try:
		db_results = db.execute_query(db_query_4)
		DDR66A = ""
		DDR67A = ""
		for row in db_results:
			DDR66A = f"{row.DDr66A}"
			DDR67A = f"{row.DDr67A}"
			log_aff.log_enreg(f"{DOCUMENT_QUERY};{DDR66A}.000;ARG0CPP_DDR66A")
			log_aff.log_enreg(f"{DOCUMENT_QUERY};{DDR67A}.000;ARG0CPP_DDR67A")
	except Exception as e:
		print(f"Erreur en Exception : {e}")
	
	print(f"Recup ARAPREP")
	db_query_5 = f"select top 1 * from ARAPREP WITH (NOLOCK) where APASVN = '{DOCUMENT_QUERY}' ;"
	try:
		db_results = db.execute_query(db_query_5)
		for row in db_results:
			date_string = f"{row.processTimeStamp}"
			date_object = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f")
			log_aff.log_enreg(f"{DOCUMENT_QUERY};{date_object};ARAPREP_processTimeStamp")
	except Exception as e:
		print(f"Erreur en Exception : {e}")
	
	print(f"Recup framework_eventlog")
	db_query_6 = f" select * from framework_eventlog WITH (NOLOCK) where objectId = '{DOCUMENT_QUERY}' ;"
	try:
		db_results = db.execute_query(db_query_6)
		for row in db_results:
			log_aff.log_enreg(f"{DOCUMENT_QUERY};{row.timeStamp};framework_eventlog_{row.eventSubType}")
	except Exception as e:
		print(f"Erreur en Exception : {e}")

	if DOCUMENT_QUERY_recup == "":
		DOCUMENT_QUERY = ""
		verif_continue = True
	else :
		verif_routine = False
	
# Utilisation de la classe
if __name__ == "__main__":

	# debut du log
	print("début du traitement")
	print("Création de la connexion SGBD")
	db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
	print("Connexion au SGBD")
	db.connect()
	print("Validation au SGBD")
	db.validate_connection()
	print("Validation au SGBD  : OK")
	
	DOCUMENT_QUERY = ""
	ECM_DOCIDX_TIME = ""
	verif_continue = False
	
	db_query = f"select top 1 * from ECM_DOCIDX WITH (NOLOCK);"
	db_session = ""
	
	if DOCUMENT_QUERY_recup == "":
		verif_continue = True
		print("EN attente d'un ECM_DOCIDX ")
	else :
		print("EN attente d'un ECM_DOCIDX pour {DOCUMENT_QUERY_recup}")
		
	verif_routine = True
	
	while verif_routine == True :
		routine()
	
	db.close() # Ferme le co SGBD
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()