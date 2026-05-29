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
	
	# Charger le fichier XML
	tree = ET.parse("D:\\PYTHON\\YouDoc_PAC\\test\\XpertECM.PAC.YDGLUVA24Q.PRD_YDG_001.ENV001.xml")
	root = tree.getroot()
	print(f'   ')	
	# Parcourir les éléments
	for Environment in root.findall('Environment'):
		for Base in Environment.findall('Base'):
			for L_FLD in Base.findall('L_FLD'):
				for E_FLD in L_FLD.findall('E_FLD'):
					for L_TYP in E_FLD.findall('L_TYP'):
						for E_TYP in L_TYP.findall('E_TYP'):
							for L_KWD in E_TYP.findall('L_KWD'):
								for E_KWD in L_KWD.findall('E_KWD'):
									envname = Environment.get('Name')
									basename = Base.get('Name')
									E_FLDname = E_FLD.get('lbl')
									E_TYPname = E_TYP.get('nme')
									E_KWDname = E_KWD.get('nme')
									E_KWDidx = E_KWD.get('idx')
									if E_KWDidx == "1" :
										print(f'Env: {envname}, Base: {basename}, E_FLD: {E_FLDname}, E_TYP : {E_TYPname}, E_KWD : {E_KWDname}; unique ')
	print(f'   ')			
										
										
	for Environment in root.findall('Environment'):
		for Base in Environment.findall('Base'):
			for L_FLD in Base.findall('L_FLD'):
				for E_FLD in L_FLD.findall('E_FLD'):
					for L_TYP in E_FLD.findall('L_TYP'):
						for E_TYP in L_TYP.findall('E_TYP'):
							
							envname = Environment.get('Name')
							basename = Base.get('Name')
							E_FLDname = E_FLD.get('lbl')
							E_TYPname = E_TYP.get('nme')
							E_TYPmul = E_TYP.get('mul')
							if E_TYPmul == "1" :
								print(f'Env: {envname}, Base: {basename}, E_FLD: {E_FLDname}, E_TYP : {E_TYPname}, multi ')
		
				
	print(f'   ')				
				
				
	log_event("0","INFO",f"Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()