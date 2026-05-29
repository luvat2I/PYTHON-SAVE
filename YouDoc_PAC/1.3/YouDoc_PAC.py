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

service_base = "YouDoc_PAC"
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
		db_query = f"DELETE FROM {sgbd_database}.ECM_PARAM WITH NC;"
	else :
		db_query = f"DELETE FROM ecm_param ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ARAHREP WITH NC;"
	else :
		db_query = f"delete FROM ARAHREP ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ARAJREP WITH NC;"
	else :
		db_query = f"delete FROM ARAJREP ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ARAMREP WITH NC;"
	else :
		db_query = f"delete FROM ARAMREP ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ARANREP WITH NC;"
	else :
		db_query = f"delete FROM ARANREP ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ARAOREP WITH NC;"
	else :
		db_query = f"delete FROM ARAOREP ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ARALREP WITH NC;"
	else :
		db_query = f"delete FROM ARALREP ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_FLDTYP WITH NC;"
	else :
		db_query = f"delete FROM ecm_fldtyp ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_DKIND WITH NC;"
	else :
		db_query = f"delete FROM ECM_DKIND ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_DOCGRP WITH NC;"
	else :
		db_query = f"delete FROM ecm_docgrp ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_PACREF WITH NC;"
	else :
		db_query = f"delete FROM ecm_pacref ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_DTTPXT WITH NC;"
	else :
		db_query = f"delete FROM ECM_DTTPXT ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_PACENV WITH NC;"
	else :
		db_query = f"delete FROM ecm_pacenv ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_KWDE WITH NC;"
	else :
		db_query = f"delete FROM ecm_KwDe ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_KITYDO WITH NC;"
	else :
		db_query = f"delete FROM ecm_kitydo ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_KIKW WITH NC;"
	else :
		db_query = f"delete FROM ecm_kikw ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_KWLST WITH NC;"
	else :
		db_query = f"delete FROM ECM_KWLST ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"DELETE FROM {sgbd_database}.ECM_FLDKW WITH NC;"
	else :
		db_query = f"delete FROM ecm_fldkw ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*UFID','Identifiant unique de document','02') WITH NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*UFID','Identifiant unique de document','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EFID','*eFolder unique ID','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EFID','*eFolder unique ID','02');"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('!GNDO','GNDO data type','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('!GNDO','GNDO data type','02');"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*COID','*Collection unique ID','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*COID','*Collection unique ID','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*REFO','Original Document Reference','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*REFO','Original Document Reference','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DSEN','Sensitive Document','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DSEN','Sensitive Document','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EIW','External index number','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EIW','External index number','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DOID','Document identifier for export','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DOID','Document identifier for export','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*FOID','Folder identifier for export','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*FOID','Folder identifier for export','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DDBN','Delete Document Batch Number','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DDBN','Delete Document Batch Number','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DFBN','Delete Folder Batch Number','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DFBN','Delete Folder Batch Number','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	
	if sgbd_db_type == 'DB2':
		db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DCAT','Document en attente','02') NC;"
	else :
		db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DCAT','Document en attente','02') ;"
	log_event("0","DEBUG",f"SGBD > QUERY > {db_query}")
	db.execute_query_save(db_query)
	log_event("0","INFO",f"Nettoyage du PAC terminé.")

	db.close() # Ferme le co SGBD
	
	log_event("0","INFO",f"Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()