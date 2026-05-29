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
import xml.etree.ElementTree as ET

service_base = "Youdoc_PAC_FINAL"
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
	langue = config['AUTRES']['langue']
except Exception as e:
	langue = 'FR'

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
	
	
try:
	parameter_file = config['PAC']['parameter_file']
	log_console("DEBUG",f"L'option 'parameter_file' contient le fichier '{parameter_file}'")
except Exception as e:
	log_secure("0","ERROR",f"L'option 'parameter_file' est manquante dans le fichier 'config.ini' : {e}")
	sys.exit(1)  # ferme lapp

try:	
	# verif présence du fichier XML
	if os.path.isfile(parameter_file):
		print(f"INFO > Le fichier {parameter_file} est accessible")
	else:
		print(f"ERROR > Le fichier {parameter_file} est inaccessible")
except Exception as e:
	log_secure("0","ERROR",f"L'option 'parameter_file' a provoqué une erreur: {e}")
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
	
    log_event("0","INFO",f"SGBD > Début de la traduction")
    
    CODE = "CALL_SERVICE"
    MODEL = "1"
    NAME = "Interroger le service ECM"
	db_query_translate = f"UPDATE {sgbd_database}.dbo.[framework_security_permission] set [framework_security_permission].name = '{NAME}' where [framework_security_permission].code = '{CODE}' and [framework_security_permission].model_id = '{MODEL}'"
    
    log_event("0","DEBUG",f"SGBD > QUERY > {db_query_translate}")
	db_results_translate = db.execute_query_save(db_query_translate)
    
    
    sys.exit(1)
    
    
    
	log_event("0","INFO",f"SGBD > Début du traitement de correction des X1")
    
	if sgbd_db_type == 'DB2':
		db_query_pacref = f"SELECT DISTINCT BASEID, PACDESC FROM {sgbd_database}.ECM_PACREF"
	else :
		db_query_pacref = f"SELECT DISTINCT baseid, pacDesc FROM ecm_pacref"
	
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query_pacref}")
	db_results_pacref = db.execute_query(db_query_pacref)
	
	caractere_special1 = '{'
	caractere_special2 = '}'
	caractere_special3 = '"'
	
    
    db_query = ""
    
    log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
    
	
	
	db_query = """
	IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[framework_security_X1]') AND type in (N'U'))  
	Drop Table framework_security_X1  
	IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[framework_security_X1]') AND type in (N'U'))  
	BEGIN  
	CREATE TABLE [dbo].[framework_security_X1](  
	[businessDataRuleId] [bigint] NULL,  
	[param_id] [varchar](500) NULL,  
	[objectType] [varchar](500) NULL,  
	[businessDataId] [bigint] NULL,  
	[nb] [bigint] NULL,  
	) ON [PRIMARY]  
	END
	
	
	delete from [framework_security_X1]




select [framework_security_business_data].objectType,[framework_security_business_data_expression].dataValue,[framework_security_business_data_expression].id, *  from [dbo].[framework_security_business_data_expression] 
left join [framework_security_business_data] on [framework_security_business_data_expression].businessDataId = [framework_security_business_data].id



    

	insert into [dbo].[framework_security_X1](businessDataRuleId) select businessDataRuleId from [dbo].[framework_security_business_data_expression] where [dbo].[framework_security_business_data_expression].[businessDataRuleId] not in (select [framework_security_X1].[businessDataRuleId] from [framework_security_X1])  
	
	UPDATE [framework_security_X1] set [framework_security_X1].[nb] = (select count(businessDataRuleId) from [dbo].[framework_security_business_data_expression] where [dbo].[framework_security_business_data_expression].[businessDataRuleId] = [dbo].[framework_security_X1].[businessDataRuleId])  
	
	delete from [framework_security_X1] where [framework_security_X1].[nb] <> 1
	
	Update [ecm_param] set [ecm_param].br_id_document = NULL where [ecm_param].br_id_document not in (select [framework_security_X1].[businessDataRuleId] from [framework_security_X1])
	
	Update [ecm_param] set [ecm_param].br_id_folder = NULL where [ecm_param].br_id_folder not in (select [framework_security_X1].[businessDataRuleId] from [framework_security_X1])
	
	UPDATE [framework_security_X1] set [framework_security_X1].[param_id] = (select datavalue from [dbo].[framework_security_business_data_expression] where [dbo].[framework_security_business_data_expression].[businessDataRuleId] = [dbo].[framework_security_X1].[businessDataRuleId])  
	
	UPDATE [framework_security_X1] set [framework_security_X1].[businessDataId] = (select [businessDataId] from [dbo].[framework_security_business_data_expression] where [dbo].[framework_security_business_data_expression].[businessDataRuleId] = [dbo].[framework_security_X1].[businessDataRuleId])
	
	UPDATE [framework_security_X1] set [framework_security_X1].[objectType] = (select [objectType] from [dbo].[framework_security_business_data] where [dbo].[framework_security_business_data].[id] = [dbo].[framework_security_X1].[businessDataId])  
	
	Update [ecm_param] set [ecm_param].br_id_document = (select [framework_security_X1].[businessDataRuleId] from [framework_security_X1] where [framework_security_X1].[param_id] = [ecm_param].[param_id] and [framework_security_X1].[objecttype] = 'Document')  

	Update [ecm_param] set [ecm_param].br_id_folder = (select top 1 [framework_security_X1].[businessDataRuleId] from [framework_security_X1] where [framework_security_X1].[param_id] = [ecm_param].[param_id] and [framework_security_X1].[objecttype] = 'Folder')  

	Drop Table framework_security_X1  """
	
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	
	log_event("0","INFO",f" Fin du traitement correction X1.")
	
	log_event("0","INFO",f" Début du traitement suppression des UNIQUE.")
	
	# Charger le fichier XML

	if sgbd_db_type == 'DB2':
		query_ECM_PARAM = f"""update {sgbd_database}.ECM_PARAM set PARAM_DATA = replace(param_data , ',"unique":true' , ',"unique":false') where param_type = 'DATATYPE' and PARAM_DATA like '%"unique":true%' """
		log_event("0","DEBUG",f"{query_ECM_PARAM}")
		db.execute_query_save(query_ECM_PARAM)
	else :
		query_ECM_PARAM = """update ecm_param set param_data = replace(param_data , ',"unique":true' , ',"unique":false') where param_type = 'DATATYPE' and param_data like '%"unique":true%' """
		log_event("0","DEBUG",f"SGBD > QUERY > {query_ECM_PARAM}")
		db.execute_query_save(query_ECM_PARAM)
				
	log_event("0","INFO",f" Fin du traitement suppression des UNIQUE.")

	db.close() # Ferme le co SGBD
	
	log_event("0","INFO",f"Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()