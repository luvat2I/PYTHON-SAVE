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
traitement_lot = config['traitement']['traitement_lot']
traitement_pause = config['traitement']['traitement_pause'] 
traitement_type = config['traitement']['traitement_type']
traitement_maj_index = config.getboolean('traitement', 'maj_index', fallback=False)
solr_query_delete = config.get('traitement', 'delete', fallback='')

time_pause = int(traitement_pause)
print(time_pause)

if enable_logging:
	os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log

# Configure le log si activé
if enable_logging:
	log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
	logging.basicConfig(filename=log_filename, level=logging.INFO, 
						format='%(asctime)s - %(levelname)s > %(message)s')
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
	log_aff.log_base("INFO","#########################")
	log_aff.log_base("INFO","début du traitement")
	
	if traitement_type != "EVENT":
		log_aff.log_info("INFO",f"SGBD > type : {sgbd_db_type} serveur : {sgbd_server} port : {sgbd_port} user : {sgbd_username} pass : {sgbd_password} base : {sgbd_database}",enable_print)
	
	log_aff.log_info("INFO",f"SOLR > serveur : {solr_hostname} user : {solr_username} pass : {solr_password} tenant : {solr_tenant}",enable_print)
	
	if traitement_type == "EVENT":
		log_aff.log_info("INFO",f"Traitement > traitement de {traitement_type} query : {solr_query_delete}",enable_print)
	else :
		log_aff.log_info("INFO",f"Traitement > traitement de {traitement_type} par lot de {traitement_lot} avec une pause de {traitement_pause}",enable_print)
	if traitement_maj_index and traitement_type != "EVENT" :
		log_aff.log_info("INFO",f"Traitement > Avec réindexation automatique",enable_print)
		
	# Preparation à la connexion SOLR
	solr_url = f'https://{solr_hostname}/solr/{solr_tenant}' # creation adresse de connexion
	client = SolrClient(solr_url, solr_username, solr_password) # creation de la classe solr
	
	# Connexion BDD
	if traitement_type != "EVENT":
		log_aff.log_info("INFO","Création de la connexion SGBD",enable_print)
		
		db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
		db.connect()
		db.validate_connection()
		
		log_aff.log_info("INFO","lancement de la validation de la connexion SGBD",enable_print)
		
	# lancement du traitement des documents
	if traitement_type == "DOCUMENT":
		
		if sgbd_db_type == 'DB2':
			db_query_count = f"SELECT count(*) FROM {sgbd_database}.{sgbd_data} WHERE DDR68A = '' OR DDR68A IS NULL"
			db_query_count.upper()
		else :
			db_query_count = f"SELECT count(*) FROM {sgbd_data} where DDr68a = ''  OR DDr68a IS NULL;"
			
		log_aff.log_info("INFO",f"db query : {db_query_count}",enable_print)
		
		db_results_count = db.execute_query_count(db_query_count)
		
		log_aff.log_base("INFO",f"Nombre de DOCUMENT à traiter = {db_results_count}")
		
		if traitement_lot == '0' :
			traitement_lot = db_results_count

		if sgbd_db_type == 'DB2' :
			db_query = f"FROM {sgbd_database}.{sgbd_data} WHERE DDR68A = '' OR DDR68A IS NULL order by DD1RA"
			db_query.upper()
		else :
			db_query = f"FROM {sgbd_data} where DDr68a = '' OR DDr68a IS NULL order by DD1ra ;"
		
		if traitement_lot == '0' :
			db_query = f"SELECT * {db_query}"
		elif sgbd_db_type == 'DB2' and traitement_lot != '0' :
			db_query = f"SELECT * {db_query} fetch first {traitement_lot} rows only"
			db_query.upper()
		elif sgbd_db_type != 'DB2' and traitement_lot != '0' :
			db_query = f"SELECT TOP({traitement_lot}) * {db_query}"
		
		if traitement_lot == '0' : # Securisation du traitement des lots
			traitement_lot = db_results_count
		
		calcul_fait = 0
		
		for i in range(0, int(db_results_count), int(traitement_lot)):
			
			calcul_min = calcul_fait
			calcul_max = calcul_fait + int(traitement_lot)
			
			log_aff.log_base("INFO",f"traitement du lot {i} > de {calcul_min} à {calcul_max} sur {db_results_count}")
			
			log_aff.log_info("INFO",f"db query : {db_query}",enable_print)
			
			db_results = db.execute_query(db_query)
			
			for row in db_results:
				
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				if sgbd_db_type == 'DB2':
					log_aff.log_info("INFO",f"ID document > {row.DD1RA}",enable_print)
				else :
					log_aff.log_info("INFO",f"ID document > {row.DD1rA}",enable_print)
					
				if sgbd_db_type == 'DB2':
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.DD1RA}"
				else :
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.DD1rA}"
					
				solr_results = client.search(solr_query)
				retour = client.display_results(solr_results)
				
				if sgbd_db_type == 'DB2':
					log_aff.log_base("INFO",f"ID document > {row.DD1RA} > indexation à {retour}")
					db_query_save = f"UPDATE {sgbd_database}.{sgbd_data} set DDR68A = '{retour}' where DD1RA = '{row.DD1RA}' WITH NC"
					db_query_save.upper()
				else :
					log_aff.log_base("INFO",f"ID document > {row.DD1rA} > indexation à {retour}")
					db_query_save = f"UPDATE {sgbd_data} set DDr68a = '{retour}' where DD1rA = '{row.DD1rA}';"
				
				log_aff.log_info("INFO",f"{db_query_save}",enable_print)
				db.execute_query_save(db_query_save)
				if traitement_maj_index :
					if sgbd_db_type == 'DB2':
						log_aff.log_base("INFO",f"ID document > {row.DD1RA} > ARG0CPP à {retour}")
						db_query_save = f"UPDATE {sgbd_database}.ARG0CPP set DDR68A = '{retour}' where DD1RA = '{row.DD1RA}' WITH NC"
						db_query_save.upper()
					else :
						log_aff.log_base("INFO",f"ID document > {row.DD1rA} > ARG0CPP à {retour}")
						db_query_save = f"UPDATE ARG0CPP set DDr68a = '{retour}' where DD1rA = '{row.DD1rA}';"
					log_aff.log_info("INFO",f"{db_query_save}",enable_print)
					db.execute_query_save(db_query_save)
				calcul_fait += 1
			if calcul_fait < db_results_count :
				log_aff.log_base("INFO",f"Pause de {traitement_pause} secondes")
				time.sleep(time_pause)
				log_aff.log_base("INFO",f"Fin de la Pause de {traitement_pause} secondes")
				
	# lancement du traitement des dossiers
	if traitement_type == "FOLDER":

		if sgbd_db_type == 'DB2':
			db_query_count = f"SELECT count(*) FROM {sgbd_database}.{sgbd_data} WHERE STATUS = ''  OR STATUS IS NULL"
			db_query_count.upper()
		else :
			db_query_count = f"SELECT count(*) FROM {sgbd_data} where status = ''  OR status IS NULL;"
		print(f"{db_query_count}")
		
		log_aff.log_info("INFO",f"db query : {db_query_count}",enable_print)
		
		db_results_count = db.execute_query_count(db_query_count)
		
		log_aff.log_base("INFO",f"Nombre de FOLDER à traiter > {db_results_count}")

		if sgbd_db_type == 'DB2':
			db_query = f"FROM {sgbd_database}.{sgbd_data} WHERE STATUS = '' OR STATUS IS NULL ORDER BY FOLDERID"
			db_query.upper()
		else :
			db_query = f"FROM {sgbd_data} where status = ''  OR status IS NULL order by folderId ;"
		
		if traitement_lot == '0' :
			db_query = f"SELECT * {db_query}"
		elif sgbd_db_type == 'DB2' and traitement_lot != '0' :
			db_query = f"SELECT * {db_query} fetch first {traitement_lot} rows only"
			db_query.upper()
		elif sgbd_db_type != 'DB2' and traitement_lot != '0' :
			db_query = f"SELECT TOP({traitement_lot}) * {db_query}"

		if traitement_lot == '0' :
			traitement_lot = db_results_count
		
		calcul_fait = 0

		for i in range(0, int(db_results_count), int(traitement_lot)):
			
			calcul_min = calcul_fait
			calcul_max = calcul_fait + int(traitement_lot)
			
			log_aff.log_base("INFO",f"traitement du lot {i} > de {calcul_min} à {calcul_max} sur {db_results_count}")
			
			log_aff.log_info("INFO",f"db query : {db_query}",enable_print)
			
			db_results = db.execute_query(db_query)
			
			for row in db_results:
				
				if sgbd_db_type == 'DB2':
					log_aff.log_info("INFO",f"ID dossier > {row.FOLDERID}",enable_print)
				else:
					log_aff.log_info("INFO",f"ID dossier > {row.folderId}",enable_print)


					
				if sgbd_db_type == 'DB2':
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.FOLDERID}"
				else :
					solr_query = f"id:XECM-{traitement_type}--{solr_tenant}-{row.folderId}"
					
				solr_results = client.search(solr_query)
				retour = client.display_results(solr_results)
				
				if sgbd_db_type == 'DB2':
					log_aff.log_base("INFO",f"ID dossier > {row.FOLDERID} > indexation à {retour}")
					db_query_save = f"UPDATE {sgbd_database}.{sgbd_data} set STATUS = '{retour}' where FOLDERID = '{row.FOLDERID}' WITH NC"
					db_query_save.upper()
				else :
					log_aff.log_base("INFO",f"ID dossier > {row.folderId} > indexation à {retour}")
					db_query_save = f"UPDATE {sgbd_data} set status = '{retour}' where folderId = '{row.folderId}';"

				log_aff.log_info("INFO",f"{db_query_save}",enable_print)
				db.execute_query_save(db_query_save)
				
				if traitement_maj_index :
					if sgbd_db_type == 'DB2':
						log_aff.log_base("INFO",f"ID dossier > {row.FOLDERID} > ECM_IDX_F à {retour}")
						db_query_save = f"UPDATE {sgbd_database}.ECM_IDX_F set STATUS = '{retour}' where FOLDERID = '{row.FOLDERID}' WITH NC"
						db_query_save.upper()
					else :
						log_aff.log_base("INFO",f"ID dossier > {row.folderId} > ECM_IDX_F à {retour}")
						db_query_save = f"UPDATE ECM_IDX_F set status = '{retour}' where folderId = '{row.folderId}';"
					log_aff.log_info("INFO",f"{db_query_save}",enable_print)
					db.execute_query_save(db_query_save)
					
				calcul_fait += 1

			if calcul_fait < db_results_count :

				log_aff.log_base("INFO",f"Pause de {traitement_pause} secondes")
				time.sleep(time_pause)
				log_aff.log_base("INFO",f"Fin de la Pause de {traitement_pause} secondes")

	if traitement_type == "EVENT":
		log_aff.log_base("INFO",f"lancement de traitement de DELETE des EVENTs")
		if solr_query_delete != "" :
			log_aff.log_base("INFO",f"Query de delete : {solr_query_delete}")
			client.delete(solr_query_delete)
		else :
			log_aff.log_base("ERROR","il manque la requete dans le fichier ini > 'traitement' 'delete'")
	
	if traitement_type != "EVENT": # si ce n'est pas un event
		db.close() # Ferme le co SGBD
	
	log_aff.log_base("INFO","Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()