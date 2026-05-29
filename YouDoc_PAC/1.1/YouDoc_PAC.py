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

traitement_type = "SUPPRESSION"

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
				print("La connexion est valide.")

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
			return self.cursor.fetchone()  # Retourne un unique résultat
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
				print("Connexion fermée.")
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
	
	# lancement du traitement des documents
	if traitement_type == "SUPPRESSION":
		log_aff.log_info("INFO","Création de la connexion SGBD",enable_print)
		
		db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
		db.connect()
		db.validate_connection()
		
		log_aff.log_info("INFO","lancement de la validation de la connexion SGBD",enable_print)
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_PARAM WITH NC;"
		else :
			db_query = f"DELETE FROM ecm_param ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ARAHREP WITH NC;"
		else :
			db_query = f"delete FROM ARAHREP ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ARAJREP WITH NC;"
		else :
			db_query = f"delete FROM ARAJREP ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ARAMREP WITH NC;"
		else :
			db_query = f"delete FROM ARAMREP ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ARANREP WITH NC;"
		else :
			db_query = f"delete FROM ARANREP ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ARAOREP WITH NC;"
		else :
			db_query = f"delete FROM ARAOREP ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ARALREP WITH NC;"
		else :
			db_query = f"delete FROM ARALREP ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_FLDTYP WITH NC;"
		else :
			db_query = f"delete FROM ecm_fldtyp ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_DKIND WITH NC;"
		else :
			db_query = f"delete FROM ECM_DKIND ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_DOCGRP WITH NC;"
		else :
			db_query = f"delete FROM ecm_docgrp ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_PACREF WITH NC;"
		else :
			db_query = f"delete FROM ecm_pacref ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_DTTPXT WITH NC;"
		else :
			db_query = f"delete FROM ECM_DTTPXT ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_PACENV WITH NC;"
		else :
			db_query = f"delete FROM ecm_pacenv ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_KWDE WITH NC;"
		else :
			db_query = f"delete FROM ecm_KwDe ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_KITYDO WITH NC;"
		else :
			db_query = f"delete FROM ecm_kitydo ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_KIKW WITH NC;"
		else :
			db_query = f"delete FROM ecm_kikw ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_KWLST WITH NC;"
		else :
			db_query = f"delete FROM ECM_KWLST ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"DELETE FROM {sgbd_database}.ECM_FLDKW WITH NC;"
		else :
			db_query = f"delete FROM ecm_fldkw ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*UFID','Identifiant unique de document','02') WITH NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*UFID','Identifiant unique de document','02') ;"
		
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EFID','*eFolder unique ID','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EFID','*eFolder unique ID','02');"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('!GNDO','GNDO data type','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('!GNDO','GNDO data type','02');"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*COID','*Collection unique ID','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*COID','*Collection unique ID','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*REFO','Original Document Reference','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*REFO','Original Document Reference','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DSEN','Sensitive Document','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DSEN','Sensitive Document','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EIW','External index number','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*EIW','External index number','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DOID','Document identifier for export','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DOID','Document identifier for export','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*FOID','Folder identifier for export','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*FOID','Folder identifier for export','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DDBN','Delete Document Batch Number','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DDBN','Delete Document Batch Number','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DFBN','Delete Folder Batch Number','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DFBN','Delete Folder Batch Number','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		if sgbd_db_type == 'DB2':
			db_query = f"INSERT INTO {sgbd_database}.ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DCAT','Document en attente','02') NC;"
		else :
			db_query = f"INSERT INTO ARALREP(ALATCD,ALAMNA,ALAUCD) VALUES ('*DCAT','Document en attente','02') ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)
		
		log_aff.log_base("INFO","Nettoyage du PAC terminé.")
		
	# lancement du traitement des dossiers
	if traitement_type == "PROCEDURE":
		db_query = f"DELETE FROM ecm_param ;"
		log_aff.log_info("INFO",f"{db_query}",enable_print)
		db.execute_query_save(db_query)

	db.close() # Ferme le co SGBD
	
	log_aff.log_base("INFO","Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()