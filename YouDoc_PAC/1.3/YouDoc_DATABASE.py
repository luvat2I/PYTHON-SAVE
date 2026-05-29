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
import logging.handlers
import configparser
from datetime import datetime, timedelta
import win32evtlogutil
import win32evtlog
import win32api
import win32con

service_base = "YouDoc_DATABASE"
#traitement_type = "service"
traitement_type = "exe"

log_event_level = "WARNING"
log_folder_level="WARNING"
log_console_level="WARNING"

time_sleep=0

log_levels = {
	"DEBUG": logging.DEBUG,
	"INFO": logging.INFO,
	"WARNING": logging.WARNING,
	"ERROR": logging.ERROR
}

### affiche les logs dans les Evenements windows ###
def log_service(level,log_text):
	if level == "DEBUG" and log_event_level == "DEBUG" :
		logger_service.debug(f"{log_text}")
	if level == "INFO" and (log_event_level == "DEBUG" or log_event_level == "INFO") :
		logger_service.info(f"{log_text}")
	elif level == "WARNING" and (log_event_level == "DEBUG" or log_event_level == "INFO" or log_event_level == "WARNING"):
		logger_service.warning(f"{log_text}")
	elif level == "ERROR" :
		logger_service.error(f"{log_text}")

### affiche les logs dans la console ###
def log_console(level,log_text):
	if traitement_type == "exe" :
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		if level == "DEBUG" and log_console_level == "DEBUG" :
			print(f"{current_time} > {level} > {log_text}")
		if level == "INFO" and (log_console_level == "DEBUG" or log_console_level == "INFO") :
			print(f"{current_time} > {level} > {log_text}")
		elif level == "WARNING" and (log_console_level == "DEBUG" or log_console_level == "INFO" or log_console_level == "WARNING"):
			print(f"{current_time} > {level} > {log_text}")
		elif level == "ERROR" :
			print(f"{current_time} > {level} > {log_text}")
	
### affiche les logs de façon securisé avant l'initialisations des paramètres (event et console) ###
def log_secure(type,level,log_text):
	if type == "0" :
		log_service(level,log_text)
	log_console(level,log_text)
	if traitement_type == "exe" and level == "ERROR" :
		input("Appuyez sur une touche pour quitter...")

### création d'une source d'événements si elle n'existe pas pour le mode service ###
def create_event_source(source_name):
	try:
		win32evtlogutil.ReportEvent(source_name, 1, eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE, strings=[source_name])
	except Exception as e:
		print("error")
		win32api.RegCreateKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}')
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'EventMessageFile', win32con.REG_SZ, os.path.abspath(__file__))
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'TypesSupported', win32con.REG_DWORD, 7)

### enregistre les logs dans un fichier ###
def log_enreg(level,log_text):
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	if level == "DEBUG" and log_folder_level == "DEBUG" :
		logger_folder.debug(f"{log_text}")
	if level == "INFO" and (log_folder_level == "DEBUG" or log_folder_level == "INFO") :
		logger_folder.info(f"{log_text}")
	elif level == "WARNING" and (log_folder_level == "DEBUG" or log_folder_level == "INFO" or log_folder_level == "WARNING"):
		logger_folder.warning(f"{log_text}")
	elif level == "ERROR" :
		logger_folder.error(f"{log_text}")
		
### traitement des logs en fonction du type ###
### 2 > pour la console ###
### 1 > pour log dans un fichier et la console ###
### 0 > pour les event win, log dans un fichier et la console ###
def log_event(type,level,log_text):
	if type == "0" :
		if enable_logging :
			log_enreg(level,log_text)
		log_service(level,log_text)
		log_console(level,log_text)
	elif type == "1" :
		if enable_logging :
			log_enreg(level,log_text)
		log_console(level,log_text)
	elif type == "2" :
		log_console(level,log_text)

# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
		
### lecture du fichier INI et traitement de toutes les entrées ###
config = configparser.ConfigParser()

logger_service = logging.getLogger(service_base)
logger_service.setLevel(logging.WARNING)
event_handler = logging.handlers.NTEventLogHandler(service_base)
logger_service.addHandler(event_handler)
create_event_source(f"{service_base}")

try:
	config.read('config.ini')
	if not config.sections():  # Vérifie si le fichier ini est vide
		raise FileNotFoundError("Le fichier de configuration 'config.ini' est vide.")
except Exception as e:
	log_secure("0","ERROR",f"Probleme de traitement du fichier 'config.ini': {e}")
	sys.exit(1)  # ferme lapp

try:
	enable_logging = config.getboolean('logging', 'enable_logging')
except Exception as e:
	log_secure("0","ERROR",f"Probleme de traitement du fichier 'config.ini': {e}")
	sys.exit(1)  # ferme lapp

if enable_logging :
	try:
		log_folder = config['logging']['log_folder']
	except Exception as e:
		log_secure("0","ERROR",f"L'option 'log_folder' est manquante dans le fichier 'config.ini': {e}")
		exit(1)  # Quitte l'application avec un code d'erreur

	try:
		log_folder_level = config['logging']['log_folder_level']
	except Exception as e:
		log_secure("0","ERROR",f"L'option 'log_folder_level' est manquante dans le fichier 'config.ini': {e}")
		exit(1)  # Quitte l'application avec un code d'erreur

try:
	log_console_level = config['logging']['log_console_level']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'log_console_level' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur

try:
	sgbd_db_type = config['SGBD']['db_type']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'db_type' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur

try:
	sgbd_driver = config['SGBD']['db_driver']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'db_driver' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_server = config['SGBD']['db_server']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'db_server' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_port = config['SGBD']['db_port']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'db_port' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_username = config['SGBD']['db_username']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'db_username' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur
	
try:
	sgbd_password = config['SGBD']['db_password']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'db_password' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur
	
try:
	sgbd_database = config['SGBD']['db_database']
except Exception as e:
	log_secure("0","ERROR",f"L'option 'db_database' est manquante dans le fichier 'config.ini': {e}")
	exit(1)  # Quitte l'application avec un code d'erreur

try:	
	if enable_logging:
		os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log
except Exception as e:
	log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}")
	exit(1)  # Quitte l'application avec un code d'erreur

try:	
	# Configure le log si activé
	if enable_logging:
		log_level = log_levels.get(log_folder_level, logging.ERROR)
		log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
		logger_folder = logging.getLogger('folderloger')
		logger_folder.setLevel(log_level)
		file_handler = logging.FileHandler(log_filename)
		file_handler.setLevel(log_level)
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		file_handler.setFormatter(formatter)
		logger_folder.addHandler(file_handler)
	else:
		logging.disable(logging.CRITICAL)  # Désactiver le logging si non activé
except Exception as e:
	log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}")
	exit(1)  # Quitte l'application avec un code d'erreur	

try:
	log_event_level = config['logging']['log_event_level']
	log_console("DEBUG",f"L'option 'log_event_level' est de niveau '{log_event_level}'")
except Exception as e:
	log_secure("0","ERROR",f"L'option 'log_event_level' est manquante dans le fichier 'config.ini' : {e}")
	sys.exit(1)  # ferme lapp
	
	
log_level2 = log_levels.get(log_event_level, logging.ERROR)
logger_service.setLevel(log_level2)
	
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
			log_event("0","INFO",f"Connexion réussie à la base de données.")
		except pyodbc.Error as e:
			log_event("0","ERROR",f"Erreur de connexion à la base de données: {e}")
			exit(1)  # Quitte l'application avec un code d'erreur
	def validate_connection(self): # Valide si la connexion est active.
		if self.connection:
			try:
				cursor = self.connection.cursor()
				if sgbd_db_type == 'DB2':
					cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
				else :
					cursor.execute("SELECT 1;")
				log_event("0","INFO",f"La connexion est valide")
				
			except pyodbc.Error as e:
				log_event("0","ERROR",f"La connexion n'est pas valide: {e}")
		else:
			log_event("0","INFO",f"Aucune connexion établie.")
			input("Appuyez sur une touche pour quitter...")
			exit(1)  # Quitte l'application avec un code d'erreur

	def execute_query(self, query, params=None): # Exécute une requête SQL et retourne tous les résultats
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchall()  # Retourne tous les résultats
		except Exception as e:
			log_event("0","ERROR",f"Erreur lors de l'execution de la requete sql {query}: {e}")
			exit(1)  # Quitte l'application avec un code d'erreur
			
	def execute_query_count(self, query, params=None): # Exécute une requête SQL de count et retourne un unique résultat
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchone()  # Retourne un unique résultat
		except Exception as e:
			log_event("0","ERROR",f"Erreur lors de l'execution de la requete sql {query}: {e}")
			exit(1)  # Quitte l'application avec un code d'erreur
			
	def execute_query_save(self, query, params=None): # Exécute une requête d'update et commit
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			self.connection.commit() # Commit le résultat
		except Exception as e:
			log_event("0","ERROR",f"Erreur lors de l'execution de la requete sql {query}: {e}")
			exit(1)  # Quitte l'application avec un code d'erreur

	def close(self): # Cloture la co
		if self.connection:
			try:
				self.connection.close()
				log_event("0","INFO",f"Connexion fermée.")
			except Exception as e:
				log_event("0","ERROR",f"Deconnexion impossible : {e}")
				exit(1)  # Quitte l'application avec un code d'erreur


# Utilisation de la classe
if __name__ == "__main__":

	log_event("0","INFO",f"Debut du traitement")
	log_event("0","DEBUG",f"SGBD > type : {sgbd_db_type} serveur : {sgbd_server} port : {sgbd_port} user : {sgbd_username} pass : {sgbd_password} base : {sgbd_database}")
	
	# lancement du traitement des documents
	log_event("0","INFO",f"SGBD > Creation de la connexion SGBD")
	db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
	db.connect()
	log_event("0","INFO",f"SGBD > Validation de la connexion SGBD")
	db.validate_connection()
		
	if sgbd_db_type == 'DB2':
		db_query_pacref = f"SELECT DISTINCT BASEID, PACDESC FROM {sgbd_database}.ECM_PACREF"
	else :
		db_query_pacref = f"SELECT DISTINCT baseid, pacDesc FROM ecm_pacref"
	
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query_pacref}")
	db_results_pacref = db.execute_query(db_query_pacref)
	
	caractere_special1 = '{'
	caractere_special2 = '}'
	caractere_special3 = '"'
	
	for row in db_results_pacref:
	
		if sgbd_db_type == 'DB2':
			PARAM_ID = row.BASEID
		else :
			PARAM_ID = row.baseid
		
		if sgbd_db_type == 'DB2':
			FORMATTED_JSON = f"{caractere_special3}databaseDescription_fr{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3},{caractere_special3}databaseDescription_de{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3},{caractere_special3}databaseDescription_it{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3},{caractere_special3}databaseDescription_en{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3}"
			PARAM_DATA_FIN = f"{caractere_special3}language{caractere_special3}:{caractere_special3}fr{caractere_special3},{caractere_special3}value{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3}"
		else :
			FORMATTED_JSON = f"{caractere_special3}databaseDescription_fr{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_de{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_it{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_en{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
			PARAM_DATA_FIN = f"{caractere_special3}language{caractere_special3}:{caractere_special3}fr{caractere_special3},{caractere_special3}value{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
		
		if sgbd_db_type == 'DB2':
			db_query_ARAMREP = f"SELECT * FROM {sgbd_database}.ARAMREP WHERE ARAMREP.AMAWCD = '{row.BASEID}'"
		else :
			db_query_ARAMREP = f"SELECT * FROM ARAMREP WHERE ARAMREP.AMAWCD = '{row.baseid}'"
		log_event("0","DEBUG",f"SGBD > QUERY > {db_query_ARAMREP}")
		db_results_ARAMREP = db.execute_query(db_query_ARAMREP)
		
		if sgbd_db_type == 'DB2':
			db_query_ARGGREP = f"SELECT * FROM {sgbd_database}.ARGGREP WHERE ARGGREP.GGAWCD = '{row.BASEID}'"
		else :
			db_query_ARGGREP = f"SELECT * FROM ARGGREP WHERE ARGGREP.GGAWCD = '{row.baseid}'"
		log_event("0","DEBUG",f"SGBD > QUERY > {db_query_ARGGREP}")
		db_results_ARGGREP = db.execute_query(db_query_ARGGREP)
		
		if sgbd_db_type == 'DB2':
			db_query_FLDTYP = f"SELECT DISTINCT TYPENME FROM {sgbd_database}.ECM_FLDTYP WHERE ECM_FLDTYP.BASE = '{row.BASEID}'"
		else :
			db_query_FLDTYP = f"SELECT DISTINCT typeNme FROM ECM_FLDTYP WHERE ECM_FLDTYP.BASE = '{row.baseid}'"
		log_event("0","DEBUG",f"SGBD > QUERY > {db_query_FLDTYP}")
		db_results_FLDTYP = db.execute_query(db_query_FLDTYP)
		
		PARAM_TYPE = f"DATABASE"
		PARAM_DATA = ""
		dataTypeLink = ""
		folderLinkTypes = ""
		folderTypes = ""
		
		for index, row in enumerate(db_results_ARAMREP):
		
			if index == len(db_results_ARAMREP) - 1: 
				dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2}"""
			else :
				dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2},"""
		
		for index, row in enumerate(db_results_ARGGREP):
		
			if index == len(db_results_ARGGREP) - 1: 
				folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2}"""
			else :
				folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2},"""
		
		for index, row in enumerate(db_results_FLDTYP):
			if sgbd_db_type == 'DB2':
				if index == len(db_results_FLDTYP) - 1: 
					folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.TYPENME}","autoIncrement":false{caractere_special2}"""
				else :
					folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.TYPENME}","autoIncrement":false{caractere_special2},"""
			else :
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
		
		RADIATED = "0"
		CREATION_USER = "NULL"
		MODIFICATION_USER = "NULL"
		CREATION_DATE = "NULL"
		MODIFICATION_DATE = "NULL"
		BR_ID_DOCUMENT = "NULL"
		BR_ID_FOLDER = "NULL"
		if sgbd_db_type == 'DB2':
			query_save = "INSERT INTO {sgbd_database}.ECM_PARAM (PARAM_ID, PARAM_TYPE,PARAM_DATA,RADIATED,CREATION_USER,MODIFICATION_USER,CREATION_DATE,MODIFICATION_DATE,FORMATTED_JSON,BR_ID_DOCUMENT,BR_ID_FOLDER)"
			query_save = query_save + f" select '{PARAM_ID}','{PARAM_TYPE}','{PARAM_DATA}','0',NULL,NULL,NULL,NULL,'{FORMATTED_JSON}',NULL,NULL"
			query_save = query_save + f" WHERE NOT EXISTS (SELECT 1 FROM {sgbd_database}.ECM_PARAM WHERE param_id = '{PARAM_ID}');"
		else :
			query_save = "INSERT INTO ecm_param (param_id, param_type,param_data,radiated,creation_user,modification_user,creation_date,modification_date,formatted_json,br_id_document,br_id_folder)"
			query_save = query_save + f" select '{PARAM_ID}','{PARAM_TYPE}','{PARAM_DATA}','0',NULL,NULL,NULL,NULL,'{FORMATTED_JSON}',NULL,NULL"
			query_save = query_save + f" WHERE NOT EXISTS (SELECT 1 FROM ecm_param WHERE param_id = '{PARAM_ID}');"
		
		log_event("0","DEBUG",f"SGBD > QUERY > {query_save}")
		db.execute_query_save(query_save)
		
	db.close() # Ferme le co SGBD
	
	log_event("0","INFO",f"Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()