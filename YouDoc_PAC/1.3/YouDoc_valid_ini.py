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

def log_event(type,level,log_text):
	print(f"{level} > {log_text}")
		
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
	
print(f"INFO > Validation de la partie '[LOGGING]'")

try:
	enable_logging = config.getboolean('logging', 'enable_logging')
	print(f"INFO > enable_logging : {enable_logging}")
except Exception as e:
    print(f"ERROR > L'option 'enable_logging' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	log_folder = config['logging']['log_folder']
	print(f"INFO > log_folder : {log_folder}")
except Exception as e:
    print(f"ERROR > L'option 'log_folder' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	log_event_level = config['logging']['log_event_level']
	print(f"INFO > log_event_level : {log_event_level}")
except Exception as e:
    print(f"ERROR > L'option 'log_event_level' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	log_folder_level = config['logging']['log_folder_level']
	print(f"INFO > log_folder_level : {log_folder_level}")
except Exception as e:
    print(f"ERROR > L'option 'log_folder_level' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	log_console_level = config['logging']['log_console_level']
	print(f"INFO > log_console_level : {log_console_level}")
except Exception as e:
    print(f"ERROR > L'option 'log_console_level' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur
	
print(f"INFO > Validation de la partie '[SGBD]'")

try:
	sgbd_db_type = config['SGBD']['db_type']
	print(f"INFO > db_type : {sgbd_db_type}")
except Exception as e:
    print(f"ERROR > L'option 'db_type' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

try:
	sgbd_driver = config['SGBD']['db_driver']
	print(f"INFO > db_driver : {sgbd_driver}")
except Exception as e:
    print(f"ERROR > L'option 'db_driver' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_server = config['SGBD']['db_server']
	print(f"INFO > db_server : {sgbd_server}")
except Exception as e:
    print(f"ERROR > L'option 'db_server' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_port = config['SGBD']['db_port']
	print(f"INFO > db_port : {sgbd_port}")
except Exception as e:
    print(f"ERROR > L'option 'db_port' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur	

try:
	sgbd_username = config['SGBD']['db_username']
	print(f"INFO > db_username : {sgbd_username}")
except Exception as e:
    print(f"ERROR > L'option 'db_username' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur
	
try:
	sgbd_password = config['SGBD']['db_password']
	print(f"INFO > db_password : {sgbd_password}")
except Exception as e:
    print(f"ERROR > L'option 'db_database' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur
	
try:
	sgbd_database = config['SGBD']['db_database']
	print(f"INFO > db_database : {sgbd_database}")
except Exception as e:
    print(f"ERROR > L'option 'db_port' est manquante dans le fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

traitement_type = "CONFIGURATION"

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
			input("Appuyez sur une touche pour quitter...")
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
	
	# debut du log
	print(f"INFO > Le fichier Ini est OK.")
	
	log_event("0","INFO",f"Debut du test de connexion à la BDD")
	log_event("0","DEBUG",f"SGBD > type : {sgbd_db_type} serveur : {sgbd_server} port : {sgbd_port} user : {sgbd_username} pass : {sgbd_password} base : {sgbd_database}")
	
	# lancement du traitement des documents
	log_event("0","INFO",f"SGBD > Creation de la connexion SGBD")
	db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
	db.connect()
	log_event("0","INFO",f"SGBD > Validation de la connexion SGBD")
	db.validate_connection()
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()