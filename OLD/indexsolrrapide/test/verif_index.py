#pyinstaller --onefile verif_index.py
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
traitement_lot = config['traitement']['traitement_lot']
traitement_pause = config['traitement']['traitement_pause'] 
traitement_type = config['traitement']['traitement_type']

solr_query_delete = config.get('traitement', 'delete', fallback='')

if enable_logging:
	os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log

# Configure le log si activé
if enable_logging:
	log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
	logging.basicConfig(filename=log_filename, level=logging.INFO, 
						format='%(asctime)s - %(levelname)s - %(message)s')
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
	
	def delete(self, query): # Effectuer la suppression dans Solr avec désactivation de la vérification SSL
		response = requests.get(
			f"{self.solr_url}/update?stream.body=<delete><query>{query}</query></delete>",
			auth=HTTPBasicAuth(self.username, self.password),
			verify=False  # Désactiver la vérification SSL
		)
		# Vérifier la réponse
		if response.status_code == 200:
			current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			logtext = f"{current_time} > suppression de {query} réalisé avec succès"
			logging.info(f"{logtext}")
			print(f"{logtext}")
		else:
			current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			logtext = f"Erreur lors de la suppression : {response.text}"
			logging.info(f"{logtext}")
			print({logtext})
		
	def display_results(self, results):
		var_retour = "N"
		# Afficher les résultats
		# print(f"Nombre de résultats: {len(results)}")
		if not results:
			print(f"SOLR > pas dans solr")
			var_retour = "N"
		else:
			for result in results:
				clean_id = self.clean_document_id(f"{result['id']}")
				print(f"SOLR > ID:{clean_id}")
				var_retour = "I"
				data_jsonObject =  f"{result.get('jsonObject', 'N/A')}"
				data = json.loads(data_jsonObject)
				modification_date = data['objectDescription'].get('objectFilterDate')
				if modification_date:
					print("Date de modification :", modification_date)
				else:
					print("La clé 'modificationDateTime' n'existe pas.")
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

# Utilisation de la classe
if __name__ == "__main__":
	# debut du log
	logging.info("#########################")
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	logtext = f"{current_time} > début du traitement"
	print(f"{logtext}")
	logging.info(f"{logtext}")
	
	if enable_print:
		print(f"SGBD param > {sgbd_db_type} sur le serveur {sgbd_server} port {sgbd_port} user {sgbd_username} pass {sgbd_password} base {sgbd_database}")
		print(f"SOLR param > sur le serveur {solr_hostname} user {solr_username} pass {solr_password} tenant {solr_tenant}")
		print(f"Traitement param > traitement de {traitement_type} par lot de {traitement_lot} avec une pause de {traitement_pause}")
	logging.info(f"SGBD param > {sgbd_db_type} sur le serveur {sgbd_server} port {sgbd_port} user {sgbd_username} pass {sgbd_password} base {sgbd_database}")
	logging.info(f"SOLR param > sur le serveur {solr_hostname} user {solr_username} pass {solr_password} tenant {solr_tenant}")
	logging.info(f"Traitement param > traitement de {traitement_type} par lot de {traitement_lot} avec une pause de {traitement_pause}")
	
	if enable_print and traitement_type == "EVENT":
		print(f"Traitement param > va effectuer la suppression de {solr_query_delete}")
		logging.info(f"Traitement param > va effectuer la suppression de {solr_query_delete}")
	
	# Preparation à la connexion SOLR
	solr_url = f'https://{solr_hostname}/solr/{solr_tenant}' # creation adresse de connexion
	client = SolrClient(solr_url, solr_username, solr_password) # creation de la classe solr
	
	# Connexion BDD
	if traitement_type != "EVENT":
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logtext = f"{current_time} > Connexion SGBD"
		logging.info(f"{logtext}")
		if enable_print:
			print(f"{logtext}")
	
		db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
		db.connect()
		db.validate_connection()
	
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logtext = f"{current_time} > lancement de la verification de connexion SGBD"
		logging.info(f"{logtext}")
		if enable_print:
			print(f"{logtext}")
	
	# lancement du traitement des documents
	if traitement_type == "DOCUMENT":
		if sgbd_db_type == 'DB2':
			db_query_count = f"SELECT count(*) FROM {sgbd_database}.{sgbd_data} where DDr68a = ''  OR DDr68a IS NULL"
		else :
			db_query_count = f"SELECT count(*) FROM {sgbd_data} where DDr68a = ''  OR DDr68a IS NULL;"
		print(f"{db_query_count}")
		db_results_count = db.execute_query_count(db_query_count)
		
		if traitement_lot == '0' :
			traitement_lot = db_results_count
		
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logtext = f"{current_time} > Nombre de DOCUMENT à traiter > {db_results_count}"
		logging.info(f"{logtext}")
		print(f"{logtext}")
		
		for i in range(0, int(db_results_count), int(traitement_lot)):
			calcule_range = int(db_results_count) // int(traitement_lot)
			calcule = int(db_results_count) // calcule_range
			calcule_range_min = calcule * i
			calcule_range_max = calcule * (i + 1)
			
			current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			logtext = f"{current_time} > traitement du lot {i} > de {calcule_range_min} à {calcule_range_max} sur {db_results_count}"
			logging.info(f"{logtext}")
			print(f"{logtext}")

			if sgbd_db_type == 'DB2':
				db_query = f"SELECT * FROM {sgbd_database}.{sgbd_data} where DDR68A = ''  OR DDR68A IS NULL order by DD1RA fetch first {traitement_lot} rows only"
			else :
				db_query = f"SELECT TOP({traitement_lot}) * FROM {sgbd_data} where DDr68a = ''  OR DDr68a IS NULL order by DD1ra ;"
			print(f"{db_query}")
			db_results = db.execute_query(db_query)
			for row in db_results:
				
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				if sgbd_db_type == 'DB2':
					logtext = f"{current_time} > ID document > {row.DD1RA} "
				else :
					logtext = f"{current_time} > ID document > {row.DD1rA} "
				logging.info(f"{logtext}")
				if enable_print:
					print(f"{logtext}")
				if sgbd_db_type == 'DB2':
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.DD1RA}"
				else :
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.DD1rA}"
				solr_results = client.search(solr_query)
				retour = client.display_results(solr_results)
				
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logtext = f"{current_time} > ID document > indexation à {retour} "
				logging.info(f"{logtext}")
				if enable_print:
					print(f"{logtext}")
				if sgbd_db_type == 'DB2':
					db_query_save = f"UPDATE {sgbd_database}.{sgbd_data} set DDR68A = '{retour}' where DD1RA = '{row.DD1RA}' WITH NC"
				else :
					db_query_save = f"UPDATE {sgbd_data} set DDr68a = '{retour}' where DD1rA = '{row.DD1rA}';"
				print(f"{db_query_save}")
				db.execute_query_save(db_query_save)
				
			if calcule_range_max < int(db_results_count) :
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logtext = f"{current_time} > Pause de {traitement_pause} secondes"
				logging.info(f"{logtext}")
				print(f"{logtext}")
				time.sleep(int(traitement_pause))
				
	# lancement du traitement des dossiers
	if traitement_type == "FOLDER":
		if sgbd_db_type == 'DB2':
			db_query_count = f"SELECT count(*) FROM {sgbd_database}.{sgbd_data} where status = ''  OR status IS NULL"
		else :
			db_query_count = f"SELECT count(*) FROM {sgbd_data} where status = ''  OR status IS NULL;"
		print(f"{db_query_count}")
		db_results_count = db.execute_query_count(db_query_count)
		
		if traitement_lot == '0' :
			traitement_lot = db_results_count
		
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logtext = f"{current_time} > Nombre de FOLDER à traiter > {db_results_count}"
		logging.info(f"{logtext}")
		print(f"{logtext}")
		
		for i in range(0, int(db_results_count), int(traitement_lot)):
			calcule_range = int(db_results_count) // int(traitement_lot)
			calcule = int(db_results_count) // calcule_range
			calcule_range_min = calcule * i
			calcule_range_max = calcule * (i + 1)
			
			current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			logtext = f"{current_time} > traitement du lot {i} > de {calcule_range_min} à {calcule_range_max} sur {db_results_count}"
			logging.info(f"{logtext}")
			print(f"{logtext}")
			
			if sgbd_db_type == 'DB2':
				db_query = f"SELECT * FROM {sgbd_database}.{sgbd_data} where status = ''  OR status IS NULL order by FOLDERID  fetch first {traitement_lot} rows only"
			else :
				db_query = f"SELECT TOP({traitement_lot}) * FROM {sgbd_data} where status = ''  OR status IS NULL order by folderId ;"
			print(f"{db_query}")
			db_results = db.execute_query(db_query)
			for row in db_results:
				
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				if sgbd_db_type == 'DB2':
					logtext = f"{current_time} > ID dossier > {row.FOLDERID} "
				else:
					logtext = f"{current_time} > ID dossier > {row.folderId} "
				logging.info(f"{logtext}")
				if enable_print:
					print(f"{logtext}")
				if sgbd_db_type == 'DB2':
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.FOLDERID}"
				else :
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.folderId}"
				solr_results = client.search(solr_query)
				retour = client.display_results(solr_results)
				
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logtext = f"{current_time} > ID dossier > indexation à {retour} "
				logging.info(f"{logtext}")
				if enable_print:
					print(f"{logtext}")
				if sgbd_db_type == 'DB2':
					db_query_save = f"UPDATE {sgbd_database}.{sgbd_data} set status = '{retour}' where FOLDERID = '{row.FOLDERID}' WITH NC"
				else :
					db_query_save = f"UPDATE {sgbd_data} set status = '{retour}' where folderId = '{row.folderId}';"
				print(f"{db_query_save}")
				db.execute_query_save(db_query_save)
				
			if calcule_range_max < int(db_results_count) :
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				logtext = f"{current_time} > Pause de {traitement_pause} secondes"
				logging.info(f"{logtext}")
				print(f"{logtext}")
				time.sleep(int(traitement_pause))
				
	if traitement_type == "EVENT":
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		logtext = f"{current_time} > lancement suppression de {solr_query_delete}"
		logging.info(f"{logtext}")
		print(f"{logtext}")
		if solr_query_delete != "" :
			client.delete(solr_query_delete)
		else :
			print("il manque la requete dans le fichier ini > 'traitement' 'delete'")
	
	if traitement_type != "EVENT":
		db.close()
		
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	logtext = f"{current_time} > Traitement terminé."
	print(f"{logtext} Appuyez sur Entrée pour fermer la fenêtre.")
	logging.info(f"{logtext}")
	input()