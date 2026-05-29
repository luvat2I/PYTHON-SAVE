import os
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import re
import time
import logging
import logging.handlers
import configparser
from datetime import datetime, timedelta, timezone
from datetime import date
import win32evtlogutil
import win32evtlog
import win32api
import win32con
import argparse
import subprocess
import shutil
import sys
from pathlib import Path
import jks
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12, Encoding, PrivateFormat, NoEncryption, BestAvailableEncryption
from cryptography.hazmat.backends import default_backend

import getpass

import luva_lic
import luva_code

import db_class
import zip_class
import Youdoc_ZIP_complement

# Pour les erreurs dans les evenements
service_base = "Youdoc_ZIP"

contrainte_active_ini = True
contrainte_contient_luva = False # Doit faire la vérification du nom du programme : True / False
contrainte_active_lic = True # Doit faire la vérification de la license : True / False
event_active_log = False # Doit activer les logs des events : True / False
MODE_DEV = False

if contrainte_active_lic and not MODE_DEV : contrainte_active_ini = True

### Génération du nom du fichier ini
ini_filename = luva_code.get_ini_path()
if MODE_DEV : print(f"ini_filename : {ini_filename}")

### Récupération du nom du programme
nom_programme = luva_code.get_nom_programme()
if MODE_DEV : print(f"nom_programme : {nom_programme}")

### Vérification de contient service
contient_service = luva_code.nom_programme_contient(nom_programme,"SERVICE")
if contient_service :
	traitement_type = "service"
else:
	traitement_type = "exe"

### Vérification de contient LUVA
contient_luva = luva_code.nom_programme_contient(nom_programme,"LUVA")
if contrainte_contient_luva and not contient_luva :
	print(f"ERROR : Nom du programme non conforme")
	input()
	sys.exit(1)
	


### Variables complémentaires
log_event_level = "ERROR"
log_folder_level = "ERROR"
log_console_level = "WARNING"

time_sleep=0

log_levels = {
	"DEBUG": logging.DEBUG,
	"INFO": logging.INFO,
	"WARNING": logging.WARNING,
	"ERROR": logging.ERROR
}

# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

### lecture du fichier INI pour le traitement de toutes les entrées
config = configparser.ConfigParser()

## creation des loggers
logger_service = logging.getLogger(service_base)
logger_service.setLevel(logging.WARNING)
event_handler = logging.handlers.NTEventLogHandler(service_base)
logger_service.addHandler(event_handler)

if event_active_log : luva_code.create_event_source(f"{service_base}")

### Lecture du fichier INI et gestion des logs ###
try:
	if not os.path.exists(ini_filename):
		luva_code.log_secure("0","INFO",f"Pas de fichier ini '{ini_filename}'",log_event_level,logger_service,log_console_level,traitement_type)
		log_validation = False
	else :
		luva_code.log_secure("0","INFO",f"Fichier ini '{ini_filename}' est présent",log_event_level,logger_service,log_console_level,traitement_type)
		log_validation = True
		config.read(f'{ini_filename}')
		if not config.sections():  # Vérifie si le fichier ini est vide
			if contrainte_active_ini : 
				luva_code.log_secure("0","ERROR",f"Le fichier de configuration '{ini_filename}' est vide.",log_event_level,logger_service,log_console_level,traitement_type)
				sys.exit(1)  # ferme lapp
			else :
				luva_code.log_secure("0","INFO",f"Le fichier de configuration '{ini_filename}' est vide.",log_event_level,logger_service,log_console_level,traitement_type)
except Exception as e:
	luva_code.log_secure("0","ERROR",f"Probleme de traitement du fichier '{ini_filename}': {e}",log_event_level,logger_service,log_console_level,traitement_type)
	sys.exit(1)  # ferme lapp
enable_logging = False
### Valide l'activation des logs
if log_validation : enable_logging = luva_code.get_enable_logging(log_validation,config)

if enable_logging :
	try:
		log_folder = config['logging']['log_folder']
	except Exception as e: enable_logging = False
	
	try: 
		log_folder_level = config['logging']['log_folder_level']
	except Exception as e: log_folder_level = "ERROR"

try:
	if log_validation : log_console_level = config['logging']['log_console_level']
	else : log_console_level = "INFO"
except Exception as e: log_console_level = "INFO"

try:	
	if enable_logging: os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log
except Exception as e:
	luva_code.log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}",log_event_level,logger_service,log_console_level,traitement_type)
	sys.exit(1)  # Quitte l'application avec un code d'erreur

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
	luva_code.log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}",log_event_level,logger_service,log_console_level,traitement_type)
	sys.exit(1)  # Quitte l'application avec un code d'erreur	

try:
	log_event_level = config['logging']['log_event_level']
	luva_code.log_console("DEBUG",f"L'option 'log_event_level' est de niveau '{log_event_level}'",log_console_level,traitement_type)
except Exception as e:
	log_event_level = "ERROR"
verif = False

log_level2 = log_levels.get(log_event_level, logging.ERROR)
logger_service.setLevel(log_level2)

if contrainte_active_ini :
	licence_valide = False
	licence = luva_code.get_licence(config)
	if MODE_DEV : print(licence)
	
	try:
		licence_valide = luva_lic.valide_licence(licence,MODE_DEV)
	except Exception as e:
		licence_valide = False
	if not licence_valide :
		luva_code.log_secure("0","ERROR",f"Pas de licence VALIDE",log_event_level,logger_service,log_console_level,traitement_type)
		sys.exit(1)  # Quitte l'application avec un code d'erreur
	elif MODE_DEV :
		print(f"Licence VALIDE")

### fin traitement des logs

# Main
if __name__ == "__main__":
	
	### récupération des données du fichier INI
	logaffiche = "Lecture des parametres en cours "
	print(f"{logaffiche}...")
	
	try:
		sgbd_db_type = config['PARAM']['sgbd_db_type']
		sgbd_driver = config['PARAM']['sgbd_driver']
		sgbd_server = config['PARAM']['sgbd_server']
		sgbd_port = config['PARAM']['sgbd_port']
		sgbd_database = config['PARAM']['sgbd_database']
		sgbd_username = config['PARAM']['sgbd_username']
		sgbd_password = config['PARAM']['sgbd_password']
		sgbd_data = config['PARAM']['sgbd_data']
		
		path_data = config['PARAM']['path_data']
		path_save = config['PARAM']['path_save']
		
		lance_indexation = config['PARAM']['lance_indexation']
		print(f"{logaffiche}... connexion {sgbd_db_type} sur {sgbd_database}.dbo.{sgbd_data}")
		print(f"{logaffiche}... dossier depart = {path_data}")
		print(f"{logaffiche}... dossier temp = {path_save}")
		print(f"{logaffiche}... Indexation = {lance_indexation}")
		print(f"{logaffiche}... FIN")
	except Exception as e: 
		print(f"{logaffiche}... erreur {e}")
		sys.exit(1)

	
	
	logaffiche = "test de la connexion SQL "
	print(f"{logaffiche}...")
	try:
		db = db_class.DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
		return_db = db.connect()
		if return_db["error"] == "" : 
			print(f"{logaffiche}... {return_db["result"]}")
			
		else :
			print(f"{logaffiche}... connexion {return_db["result"]} {return_db["message"]}")
			sys.exit(1)
			
		return_db = db.validate_connection()
		
		if return_db["error"] == "" : 
			print(f"{logaffiche}... {return_db["result"]}")
			
		else :
			print(f"{logaffiche}... connexion {return_db["result"]} {return_db["message"]}")
			sys.exit(1)
		print(f"{logaffiche}... FIN")
		
	except Exception as e: 
		print(f"{logaffiche}... erreur {e}")
		sys.exit(1)

	
	### Récupération de la liste des ZIP 
	logaffiche = "Traitement des ZIP STATUS 0 "
	print(f"{logaffiche}...")
	
	db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 0"
	return_zip_document_count = db.execute_query_count(db_query_count)
	if return_zip_document_count == 0 : reste_zip = False
	else : reste_zip = True
	
	while reste_zip :
		
		
		db_query_zip_document = f"SELECT TOP (1000) * FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 0"
		return_zip_document = db.execute_query(db_query_zip_document)
		reste_zip = False
		for row in return_zip_document:
			FILE_DOCUMENT_ZIP = row.object_id_zip
			PATH_DOCUMENT_ZIP = row.path_and_file_name
			DOCUMENT_ZIP_DATA = path_data + r"\\" + PATH_DOCUMENT_ZIP
			
			ID_DOCUMENT_ZIP = Youdoc_ZIP_complement.supprime_extension(FILE_DOCUMENT_ZIP)
			
			DOCUMENT_ZIP_TEMP = path_save + r"\\" + Youdoc_ZIP_complement.supprime_extension(PATH_DOCUMENT_ZIP)
			
			print("Traitement des ZIP STATUS 0 ... " + ID_DOCUMENT_ZIP)
			
			zip_class.extract_zip(DOCUMENT_ZIP_DATA, DOCUMENT_ZIP_TEMP)
			
			db_query_maj_document = f"update [{sgbd_database}].[dbo].[{sgbd_data}] set STATUS = 1 where [{sgbd_database}].[dbo].[{sgbd_data}].[object_id_zip] = '{FILE_DOCUMENT_ZIP}'"
			print(db_query_maj_document)
			
			return_zip_document_maj = db.execute_query_save(db_query_maj_document)
			print(return_zip_document_maj)
			
			
		db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 0"
		return_zip_document_count = db.execute_query_count(db_query_count)
		if return_zip_document_count == 0 : reste_zip = False
		else : reste_zip = True
	print("Traitement des ZIP STATUS 0 ... FIN")
	# etape de listage des fichiers
	logaffiche = "Traitement liste fichiers status 1  "
	print(f"{logaffiche}...")
	
	db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 1"
	return_zip_document_count = db.execute_query_count(db_query_count)
	if return_zip_document_count == 0 : reste_zip = False
	else : reste_zip = True
	
	while reste_zip :
	
		db_query_zip_document = f"SELECT TOP (1000) * FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 1"
		return_zip_document = db.execute_query(db_query_zip_document)
		reste_zip = False
		for row in return_zip_document:
			FILE_DOCUMENT_ZIP = row.object_id_zip
			PATH_DOCUMENT_ZIP = row.path_and_file_name
			DOCUMENT_ZIP_DATA = path_data + r"\\" + PATH_DOCUMENT_ZIP
			
			ID_DOCUMENT_ZIP = Youdoc_ZIP_complement.supprime_extension(FILE_DOCUMENT_ZIP)
			
			DOCUMENT_ZIP_TEMP = path_save + r"\\" + Youdoc_ZIP_complement.supprime_extension(PATH_DOCUMENT_ZIP)
			
			print("Traitement liste fichiers status 1 ... " + ID_DOCUMENT_ZIP)
			
			for file in os.listdir(DOCUMENT_ZIP_TEMP) :
				print("Traitement liste fichiers status 1 ... " + ID_DOCUMENT_ZIP + " > " + file)
				
				db_query_list_document = f"insert into [{sgbd_database}].[dbo].[{sgbd_data}] SELECT top 1 [object_id_zip], '', '{file}', 'application/pdf', [path_and_file_name] ,2 FROM [{sgbd_database}].[dbo].[{sgbd_data}] where object_id_zip = '{row.object_id_zip}'"
				
				
				return_list_document_maj = db.execute_query_save(db_query_list_document)
				
			
			db_query_maj_document = f"update [{sgbd_database}].[dbo].[{sgbd_data}] set STATUS = 3 where [{sgbd_database}].[dbo].[{sgbd_data}].[object_id_zip] = '{FILE_DOCUMENT_ZIP}' and [{sgbd_database}].[dbo].[{sgbd_data}].[object_name] = ''"
			
			
			return_zip_document_maj = db.execute_query_save(db_query_maj_document)
			
			
		db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 1"
		return_zip_document_count = db.execute_query_count(db_query_count)
		
		if return_zip_document_count == 0 : reste_zip = False
		else : reste_zip = True
	
	print("Traitement liste fichiers status 1 ... FIN")
	
	
	db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 3"
	return_zip_document_count = db.execute_query_count(db_query_count)
	if return_zip_document_count == 0 : reste_zip = False
	else : reste_zip = True
	
	print("Traitement nomage fichiers status 3 ...")
	logaffiche = "Traitement liste fichiers status 1  "
	print(f"{logaffiche}...")
	
	ID_DOCUMENT = ""
	#recuperation id de OP5oA
	
	print("Traitement recup OP5oA ...")
	db_query_OP5oA = f"SELECT [OP5oA] FROM [{sgbd_database}].[dbo].[OPb5T]"
	return_OP5oA = db.execute_query(db_query_OP5oA)
	
	for row in return_OP5oA:
		ID_DOCUMENT1 = row.OP5oA
		
	
	db_query_APASVN = f"SELECT max(APASVN) as APASVN FROM [{sgbd_database}].[dbo].[ARAPREP]"
	return_APASVN = db.execute_query(db_query_APASVN)

	for row in return_APASVN:
		ID_DOCUMENT2 = row.APASVN
		ID_DOCUMENT2 = ID_DOCUMENT2[:-4]
	if ID_DOCUMENT1 == ID_DOCUMENT2 :
		ID_DOCUMENT = ID_DOCUMENT1
	else :
		ID_DOCUMENT = ID_DOCUMENT2
	print("Traitement recup OP5oA ... " + ID_DOCUMENT)
	print("Traitement recup OP5oA ... FIN")
	while reste_zip :
		
		db_query_zip_document = f"SELECT TOP (1000) * FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 2"
		return_zip_document = db.execute_query(db_query_zip_document)
		reste_zip = False
		for row in return_zip_document:
			
			ID_DOCUMENT = Youdoc_ZIP_complement.ID_suivant(ID_DOCUMENT)
			
			FILE_DOCUMENT_ZIP = row.object_id_zip
			PATH_DOCUMENT_ZIP = row.path_and_file_name
			DOCUMENT_ZIP_DATA = path_data + r"\\" + PATH_DOCUMENT_ZIP
			FILE_DOCUMENT = row.object_name
			ID_DOCUMENT_ZIP = Youdoc_ZIP_complement.supprime_extension(FILE_DOCUMENT_ZIP)
			DOCUMENT_ZIP_TEMP = path_save + r"\\" + Youdoc_ZIP_complement.supprime_extension(PATH_DOCUMENT_ZIP)
			
			print("Traitement nomage fichiers status 3 ... " + ID_DOCUMENT)
			
			FILE_TEMP = DOCUMENT_ZIP_TEMP + r"\\" + row.object_name
			FILE_DEF = DOCUMENT_ZIP_DATA.replace(row.object_id_zip,"") + ID_DOCUMENT + ".PDF"

			zip_class.deplace_fic_rename(FILE_TEMP,FILE_DEF)
			db_query_maj_document = f"update [{sgbd_database}].[dbo].[{sgbd_data}] set STATUS = 4,object_id = '{ID_DOCUMENT}.PDF'  where [{sgbd_database}].[dbo].[{sgbd_data}].[object_id_zip] = '{FILE_DOCUMENT_ZIP}' and [{sgbd_database}].[dbo].[{sgbd_data}].[object_name] = '{row.object_name}'"
			
			return_zip_document_maj = db.execute_query_save(db_query_maj_document)
			
	db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 2"
	return_zip_document_count = db.execute_query_count(db_query_count)
	if return_zip_document_count == 0 : reste_zip = False
	else : reste_zip = True
	
	print("Traitement nomage fichiers status 3 ... FIN")
	
	print("Traitement maj OP5oA ...")
	logaffiche = "Traitement liste fichiers status 1  "
	print(f"{logaffiche}...")
	# MAJ id de OP5oA
	ID_DOCUMENT = Youdoc_ZIP_complement.ID_suivant(ID_DOCUMENT)
	print("Traitement maj OP5oA ..." + ID_DOCUMENT)
	
	db_query_maj_ID = f"update [{sgbd_database}].[dbo].[OPb5T] set OP5oA = '{ID_DOCUMENT}'"
	
	return_zip_document_ID = db.execute_query_save(db_query_maj_ID)
	
	print("Traitement maj OP5oA ... FIN")
	# Création des données Documents
	logaffiche = "Traitement donnees doc STATUS = 4 "
	print(f"{logaffiche}...")
	
	db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 4"
	return_zip_document_count = db.execute_query_count(db_query_count)
	if return_zip_document_count == 0 : reste_zip = False
	else : reste_zip = True
	
	
	while reste_zip :
	
		db_query_zip_document = f"SELECT TOP (1000) * FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 4"
		return_zip_document = db.execute_query(db_query_zip_document)
		
		reste_zip = False
		
		for row in return_zip_document:
			
			FILE_object_id_zip = row.object_id_zip
			FILE_object_id = row.object_id
			print("Traitement donnees doc STATUS = 4 ... " + FILE_object_id)
			# IMPORTANT : faire la requete DB
			# ARAPREP
			db_query_create_data= f"insert into ARAPREP ([APASVN],[APADCD],[APAFCD],[APAOCD],[APACTX],[APATVN],[APAADT],[APAUVN],[APABDT],[APBAST],[APABTM],[APACTM],[APBBST],[APAVVN],[APAWVN],[APBCST],[APXINB],[PROCSTATE],[APKCST],[APCLDT],[processTimeStamp]) (select '{FILE_object_id}','PDF',[APAFCD],[APAOCD],[APACTX],[APATVN],[APAADT],[APAUVN],[APABDT],[APBAST],[APABTM],[APACTM],[APBBST],[APAVVN],[APAWVN],[APBCST],[APXINB],[PROCSTATE],[APKCST],[APCLDT],[processTimeStamp] from ARAPREP where APASVN = '{FILE_object_id_zip}')"
			return_create_data = db.execute_query_save(db_query_create_data)
			
			# ARARREP
			db_query_create_data= f"insert into ARARREP ([ARAETX],[ARASVN],[ARAPCD],[ARAQCD],[ARARCD],[ARASCD],[ARACDT],[ARACTM]) (select [ARAETX],'{FILE_object_id}',[ARAPCD],[ARAQCD],'PDF',[ARASCD],[ARACDT],[ARACTM] from ARARREP where ARASVN = '{FILE_object_id_zip}')"
			return_create_data = db.execute_query_save(db_query_create_data)
			

			# ecm_daddl
			db_query_create_data= f"insert into ecm_daddl  ([documentId],[orgId],[isConfidential],[workflowStatus],[eventGroupId],[isSigned],[defaultDescriptionId])(select '{FILE_object_id}',[orgId],[isConfidential],[workflowStatus],NULL,[isSigned],[defaultDescriptionId] from ecm_daddl where documentId = '{FILE_object_id_zip}')"
			return_create_data = db.execute_query_save(db_query_create_data)
			
			# OP8wT
			db_query_create_data= f"insert into OP8wT ([USzA],[US10A],[US11A],[US12A],[US13A],[US14A],[OP5oA],[OP5pA],[OPe2A],[OP68A],[OP69A],[OP6aA],[OP6bA],[OP64A],[OP65A],[OP6xA],[OP7uA],[OP5qA],[OP1K9A],[OP1KAA],[OP1KBA],[FingerprintType],[Fingerprint],[KeyID])(select [USzA],[US10A],[US11A],[US12A],[US13A],[US14A],'{FILE_object_id}',[OP5pA],[OPe2A],[OP68A],[OP69A],[OP6aA],[OP6bA],[OP64A],[OP65A],[OP6xA],[OP7uA],[OP5qA],'{FILE_object_id}',[OP1KAA],[OP1KBA],[FingerprintType],[Fingerprint],[KeyID] from OP8wT where OP5oA = '1AAAD2LF.ZIP')"
			return_create_data = db.execute_query_save(db_query_create_data)
			
			# ARRAUREP
			db_query_create_data= f"insert into ARAUREP ([AUATCD],[AUASVN],[AUALNA],[AUAPCD],[AUAQCD],[AUARCD],[AUASCD],[AUCKDT])(select [AUATCD],'{FILE_object_id}',[AUALNA],[AUAPCD],[AUAQCD],'PDF',[AUASCD],[AUCKDT] from ARAUREP where AUASVN = '{FILE_object_id_zip}')"
			return_create_data = db.execute_query_save(db_query_create_data)
			
			# OST_DOCUMENT > faire le replace
			db_query_create_data= f"insert into framework_ost_document ([media_type],[object_id],[software_code],[kind_type],[object_name],[source_name],[source_type],[path_and_file_name]) (select 'application/pdf','{FILE_object_id}','XECM','Document','{FILE_object_id}','001','XOST',replace(path_and_file_name,'{FILE_object_id_zip}','{FILE_object_id}') from framework_ost_document where object_id = '{FILE_object_id_zip}')"
			return_create_data = db.execute_query_save(db_query_create_data)
			
			#ARG0CP
			db_query_create_data= f"insert into ARG0CPP ([DD1rA],[DDr66A],[DDr67A],[DDr68A],[DDHZ9A],[errDetail])(select '{FILE_object_id}',[DDr66A],[DDr67A],'{lance_indexation}',[DDHZ9A],[errDetail] from ARG0CPP where DD1rA = '{FILE_object_id_zip}')"
			return_create_data = db.execute_query_save(db_query_create_data)
			
			#update
			db_query_maj_document = f"update [{sgbd_database}].[dbo].[{sgbd_data}] set STATUS = 5  where [{sgbd_database}].[dbo].[{sgbd_data}].[object_id_zip] = '{FILE_object_id_zip}' and [{sgbd_database}].[dbo].[{sgbd_data}].[object_id] = '{FILE_object_id}'"
			return_zip_document_maj = db.execute_query_save(db_query_maj_document)
			
	db_query_count = f"SELECT count(*) FROM [{sgbd_database}].[dbo].[{sgbd_data}] where STATUS = 4"
	return_zip_document_count = db.execute_query_count(db_query_count)
	if return_zip_document_count == 0 : reste_zip = False
	else : reste_zip = True
	
	print("Traitement donnees doc STATUS = 4 ... FIN")
	db.close()
	
	print("Fin du traitement")
	input()