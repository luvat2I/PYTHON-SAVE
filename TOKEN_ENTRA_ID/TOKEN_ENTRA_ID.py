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
import token_gestion
import luva_code
import TOKEN_ENTRA_ID_complement

# Pour les erreurs dans les evenements
service_base = "TOKEN_ENTRA_ID"

contrainte_active_ini = True
contrainte_contient_luva = True # Doit faire la vérification du nom du programme : True / False
contrainte_active_lic = True # Doit faire la vérification de la license : True / False
event_active_log = True # Doit activer les logs des events : True / False
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
	
	
	
	token_filename = TOKEN_ENTRA_ID_complement.get_token_path()
	id_token_filename = TOKEN_ENTRA_ID_complement.get_id_token_path()
	access_token_filename = TOKEN_ENTRA_ID_complement.get_access_token_path()
	
	TENANT = TOKEN_ENTRA_ID_complement.get_TENANT(config)
	CLIENT_ID = TOKEN_ENTRA_ID_complement.get_CLIENT_ID(config)
	CLIENT_SECRET = TOKEN_ENTRA_ID_complement.get_CLIENT_SECRET(config)
	GRANT_TYPE = "password"
	SCOPE = "openid profile email"
	TIMEOUT_TIME = 10
	VERIF_SSL = False
	
	if TENANT == "ERROR" or CLIENT_ID == "ERROR" or CLIENT_SECRET == "ERROR" :
		luva_code.log_console("ERROR",f"Erreur de récupération des données de l'Entra ID dans le fichier {ini_filename}",log_console_level,traitement_type)
		sys.exit(1)
	luva_code.log_console("INFO",f"Récupération des données de la connexion = OK",log_console_level,traitement_type)
	
	while True:
		USERNAME = input("Entrez le nom utilisateur de connexion : ").strip()
		if USERNAME:
			break
	
	while True:
		PASSWORD = getpass.getpass("Entrez le mot de passe de connexion : ").strip()
		if PASSWORD:
			break
	
	try :
		token_gestion_return = token_gestion.token_gestion_microsoft(TENANT, CLIENT_ID, CLIENT_SECRET, GRANT_TYPE, SCOPE, USERNAME, PASSWORD ,TIMEOUT_TIME , VERIF_SSL)
	except Exception as e:
		luva_code.log_console("ERROR",f"Soucis de connexion {e}",traitement_type)
		sys.exit(1)
	
	try :
		token_gestion_error = token_gestion_return["error"]
	except Exception as e:
		luva_code.log_console("ERROR",f"Soucis de recuperation du token {e}",log_console_level,traitement_type)
		sys.exit(1)
	
	
	if token_gestion_error != "":
		with open(token_filename, "w", encoding="utf-8") as f:
			f.write(f"ERROR\n")
			f.write(f"{token_gestion_return["code"]}{token_gestion_return["error"]} : {token_gestion_return["message2"]}{token_gestion_return["message"]}")
		luva_code.log_console("ERROR",f"{token_gestion_return["code"]}{token_gestion_return["error"]} : {token_gestion_return["message2"]}{token_gestion_return["message"]}",log_console_level,traitement_type)
		sys.exit(1)
	else :
		luva_code.log_console("INFO",f"Connexion = réussi",log_console_level,traitement_type)
		token_gestion_result = token_gestion_return["result"]
	
	
	if MODE_DEV : print(f"{token_gestion_result}")
	
	try :
		with open(token_filename, "w", encoding="utf-8") as f:
			f.write(str(token_gestion_result))
		luva_code.log_console("INFO",f"enregistrement du retour dans {token_filename}",log_console_level,traitement_type)
	except Exception as e:
		luva_code.log_console("ERROR",f"enregistrement de l'erreur dans {token_filename} : {e}",log_console_level,traitement_type)
		sys.exit(1)
	
	try :
		token_gestion_access_token = token_gestion_result.get("access_token")
		if MODE_DEV : print(f"access_token : {token_gestion_access_token}")
		decode_gestion_access_token = token_gestion.token_decode(token_gestion_access_token)
		if MODE_DEV : print(f"{decode_gestion_access_token}")
		if decode_gestion_access_token == "ERROR":
			luva_code.log_console("ERROR",f"Pas d'access token récupéré",log_console_level,traitement_type)
		else : 
			with open(access_token_filename, "w", encoding="utf-8") as f:
				json.dump(decode_gestion_access_token, f, ensure_ascii=False, indent=4, sort_keys=True)
			luva_code.log_console("INFO",f"enregistrement de l'access token dans {access_token_filename}",log_console_level,traitement_type)
	except Exception as e:
		luva_code.log_console("ERROR",f"Write dans {access_token_filename} : {e}",log_console_level,traitement_type)
		sys.exit(1)
		
	try :	
		token_gestion_id_token = token_gestion_result.get("id_token")
		if MODE_DEV : print(f"id_token : {token_gestion_id_token}")
		decode_gestion_id_token = token_gestion.token_decode(token_gestion_id_token)
		if MODE_DEV : print(f"{decode_gestion_id_token}")
		if decode_gestion_id_token == "ERROR":
			luva_code.log_console("ERROR",f"Pas d'id token récupéré",log_console_level,traitement_type)
		else :
			with open(id_token_filename, "w", encoding="utf-8") as f:
				json.dump(decode_gestion_id_token, f, ensure_ascii=False, indent=4, sort_keys=True)
			luva_code.log_console("INFO",f"enregistrement de l'id token dans {id_token_filename}",log_console_level,traitement_type)
	except Exception as e:
		luva_code.log_console("ERROR",f"Write dans {id_token_filename} : {e}",log_console_level,traitement_type)
		sys.exit(1)
	
	print("Fin du traitement")
	input()