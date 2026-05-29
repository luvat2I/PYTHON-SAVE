#pyinstaller PAC.spec
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

# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lecture du fichier de configuration
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    if not config.sections():  # Vérifie si le fichier ini est vide
        raise FileNotFoundError("Le fichier de configuration 'config.ini' est vide.")
except Exception as e:
    print(f"ERROR > Probleme de traitement du fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur
	 	 
try:
	enable_logging = config.getboolean('logging', 'enable_logging')
except Exception as e:
    print(f"ERROR > L'option 'enable_logging' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	log_folder = config['logging']['log_folder']
except Exception as e:
    print(f"ERROR > L'option 'log_folder' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	enable_print = config.getboolean('logging', 'enable_print')
except Exception as e:
    print(f"ERROR > L'option 'enable_print' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur
 
try:
	sgbd_db_type = config['SGBD']['db_type']
except Exception as e:
    print(f"ERROR > L'option 'db_type' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	sgbd_driver = config['SGBD']['db_driver']
except Exception as e:
    print(f"ERROR > L'option 'db_driver' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_server = config['SGBD']['db_server']
except Exception as e:
    print(f"ERROR > L'option 'db_server' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_port = config['SGBD']['db_port']
except Exception as e:
    print(f"ERROR > L'option 'db_port' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_username = config['SGBD']['db_username']
except Exception as e:
    print(f"ERROR > L'option 'db_username' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur
	
try:
	sgbd_password = config['SGBD']['db_password']
except Exception as e:
    print(f"ERROR > L'option 'db_database' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur
	
try:
	sgbd_database = config['SGBD']['db_database']
except Exception as e:
    print(f"ERROR > L'option 'db_port' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

traitement_type = "DATABASE"

try:	
	if enable_logging:
		os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log
except Exception as e:
    print(f"ERROR > creation du dossier {log_folder} impossible : {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:	
	# Configure le log si activé
	if enable_logging:
		log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
		logging.basicConfig(filename=log_filename, level=logging.INFO, 
							format='%(asctime)s - %(levelname)s > %(message)s')
	else:
		logging.disable(logging.CRITICAL)  # Désactiver le logging si non activé
except Exception as e:
    print(f"ERROR > creation du dossier {log_folder} impossible : {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

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
			log_aff.log_base("INFO","Connexion réussie à la base de données.")
		except Exception as e:
			log_aff.log_base("ERROR",f"Erreur de connexion à la base de données: {e}")
			input("Appuyez sur une touche pour quitter...")
			exit(1)  # Quitte l'application avec un code d'erreur

	def validate_connection(self): # Valide si la connexion est active.
		if self.connection:
			try:
				cursor = self.connection.cursor()
				cursor.execute("SELECT 1;")
				log_aff.log_base("INFO","La connexion est valide.")
				
			except Exception as e:
				log_aff.log_base("ERROR",f"La connexion n'est pas valide: {e}")
				input("Appuyez sur une touche pour quitter...")
				exit(1)  # Quitte l'application avec un code d'erreur
		else:
			log_aff.log_base("ERROR",f"Aucune connexion")
			input("Appuyez sur une touche pour quitter...")
			exit(1)  # Quitte l'application avec un code d'erreur

	def execute_query(self, query, params=None): # Exécute une requête SQL et retourne tous les résultats
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchall()  # Retourne tous les résultats
		except Exception as e:
			log_aff.log_base("ERROR",f"Erreur lors de l'execution de la requete sql {query}: {e}")
			input("Appuyez sur une touche pour quitter...")
			exit(1)  # Quitte l'application avec un code d'erreur
			
	def execute_query_count(self, query, params=None): # Exécute une requête SQL de count et retourne un unique résultat
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			if self.cursor.fetchone():
				retour = self.cursor.fetchone()  # Retourne un unique résultat
			else :
				retour = ""
			return retour  # Retourne un unique résultat
		except Exception as e:
			log_aff.log_base("ERROR",f"Erreur lors de l'execution de la requete sql {query}: {e}")
			input("Appuyez sur une touche pour quitter...")
			exit(1)  # Quitte l'application avec un code d'erreur
			
	def execute_query_save(self, query, params=None): # Exécute une requête d'update et commit
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			self.connection.commit() # Commit le résultat
		except Exception as e:
			log_aff.log_base("ERROR",f"Erreur lors de l'execution de la requete sql {query}: {e}")
			input("Appuyez sur une touche pour quitter...")
			exit(1)  # Quitte l'application avec un code d'erreur

	def close(self): # Cloture la co
		if self.connection:
			try:
				self.connection.close()
				log_aff.log_base("INFO",f"Connexion fermée.")
			except Exception as e:
				log_aff.log_base("ERROR",f"Deconnexion impossible : {e}")
				input("Appuyez sur une touche pour quitter...")
				exit(1)  # Quitte l'application avec un code d'erreur

# Utilisation de la classe
if __name__ == "__main__":

	# debut du log
	log_aff.log_base("INFO","#########################")
	log_aff.log_base("INFO","début du traitement")
	
	log_aff.log_info("INFO",f"SGBD > type : {sgbd_db_type} serveur : {sgbd_server} port : {sgbd_port} user : {sgbd_username} pass : {sgbd_password} base : {sgbd_database}",enable_print)
	
	if traitement_type == "DATABASE" : 
		log_aff.log_info("INFO","Création de la connexion SGBD SQL",enable_print)
		
		if sgbd_db_type == 'SQL':
			db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
			db.connect()
			db.validate_connection()
		
		if sgbd_db_type == 'SQL':
			
			db_query_pacref = "SELECT DISTINCT baseid, pacDesc FROM ecm_pacref"
			db_results_pacref = db.execute_query(db_query_pacref)
			
			caractere_special1 = '{'
			caractere_special2 = '}'
			caractere_special3 = '"'
			
			for row in db_results_pacref:
			
				PARAM_ID = row.baseid
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > debut du traitement",enable_print)
				
				FORMATTED_JSON = f"{caractere_special3}databaseDescription_fr{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_de{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_it{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_en{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
				
				PARAM_DATA_FIN = f"{caractere_special3}language{caractere_special3}:{caractere_special3}fr{caractere_special3},{caractere_special3}value{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
				
				db_query_ARAMREP = f"SELECT * FROM ARAMREP WHERE ARAMREP.AMAWCD = '{row.baseid}'"
				
				db_results_ARAMREP = db.execute_query(db_query_ARAMREP)
				
				db_query_ARGGREP = f"SELECT * FROM ARGGREP WHERE ARGGREP.GGAWCD = '{row.baseid}'"
				
				db_results_ARGGREP = db.execute_query(db_query_ARGGREP)
				
				db_query_FLDTYP = f"SELECT DISTINCT typeNme FROM ECM_FLDTYP WHERE ECM_FLDTYP.BASE = '{row.baseid}'"
				
				db_results_FLDTYP = db.execute_query(db_query_FLDTYP)
				
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > PARAM_ID = {PARAM_ID}",enable_print)
				
				PARAM_TYPE = f"DATABASE"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > PARAM_TYPE = {PARAM_TYPE}",enable_print)
				
				PARAM_DATA = ""
				
				dataTypeLink = ""
				folderLinkTypes = ""
				folderTypes = ""
				
				for index, row in enumerate(db_results_ARAMREP):
				
					if index == len(db_results_ARAMREP) - 1: 
						print("info 1")
						dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2}"""
					else :
						print("info 2")
						dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2},"""
						
				for index, row in enumerate(db_results_ARGGREP):
				
					if index == len(db_results_ARGGREP) - 1: 
						folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2}"""
						
					else :
						folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2},"""
				
				for index, row in enumerate(db_results_FLDTYP):
				
					if index == len(db_results_FLDTYP) - 1: 
						folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.typeNme}","autoIncrement":false{caractere_special2}"""
						
					else :
						folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.typeNme}","autoIncrement":false{caractere_special2},"""
				
				PARAM_DATA = f"{caractere_special1}{caractere_special3}dataTypeLink{caractere_special3}:" + dataTypeLink + f","
				PARAM_DATA = PARAM_DATA + f"{caractere_special3}folderLinkTypes{caractere_special3}:[" + folderLinkTypes + f"],"
				PARAM_DATA = PARAM_DATA + f"{caractere_special3}folderTypes{caractere_special3}:[" + folderTypes + f"],"
				PARAM_DATA = PARAM_DATA + f"{caractere_special3}isPacMode{caractere_special3}:false,{caractere_special3}descriptions{caractere_special3}:[" + "{"
				PARAM_DATA = PARAM_DATA + PARAM_DATA_FIN
				PARAM_DATA = PARAM_DATA + "}]}"

				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > PARAM_DATA = {PARAM_DATA}",enable_print)
				
				RADIATED = "0"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > RADIATED = {RADIATED}",enable_print)
				
				CREATION_USER = "NULL"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > CREATION_USER = {CREATION_USER}",enable_print)
				
				MODIFICATION_USER = "NULL"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > MODIFICATION_USER = {MODIFICATION_USER}",enable_print)
				
				CREATION_DATE = "NULL"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > CREATION_DATE = {CREATION_DATE}",enable_print)
				
				MODIFICATION_DATE = "NULL"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > MODIFICATION_DATE = {MODIFICATION_DATE}",enable_print)
				
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > FORMATTED_JSON = {FORMATTED_JSON}",enable_print)
				
				BR_ID_DOCUMENT = "NULL"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > BR_ID_DOCUMENT = {BR_ID_DOCUMENT}",enable_print)
				
				BR_ID_FOLDER = "NULL"
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > BR_ID_FOLDER = {BR_ID_FOLDER}",enable_print)
				
				query_save = "INSERT INTO ecm_param (param_id, param_type,param_data,radiated,creation_user,modification_user,creation_date,modification_date,formatted_json,br_id_document,br_id_folder)"
				query_save = query_save + f" select '{PARAM_ID}','{PARAM_TYPE}','{PARAM_DATA}','0',NULL,NULL,NULL,NULL,'{FORMATTED_JSON}',NULL,NULL"
				
				query_save = query_save + f" WHERE NOT EXISTS (SELECT 1 FROM ecm_param WHERE param_id = '{PARAM_ID}');"
				
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > QUERY = {query_save}",enable_print)
				db.execute_query_save(query_save)
				
				log_aff.log_info("INFO",f" ECM_PARAM : {PARAM_ID} > fin du traitement",enable_print)
				
		if sgbd_db_type == 'SQL':	
			db.close() # Ferme le co SGBD
		
		if sgbd_db_type == 'DB2':
			log_aff.log_base("INFO",f"Connexion SGBD DB2 non pris en compte pour le moment")
		
	log_aff.log_base("INFO","Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()