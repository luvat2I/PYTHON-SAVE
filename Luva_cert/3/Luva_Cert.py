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

#import perso
import luva_crt
import luva_cacert
import luva_pfx
import luva_keystore


# Pour les erreurs dans les evenements
service_base = "Luva_cert"

# Pour le traitement des services (vérification du nom services dans le programme)
programme = os.path.splitext(os.path.basename(sys.argv[0]))[0]
path = Path(sys.executable).resolve() if getattr(__import__("sys"), "frozen", False) else Path(__file__).resolve()
exe_filename = f"{programme}.exe"
path_filename = Path(path).parent
terme_service = "service"
contient_service = terme_service.lower() in exe_filename.lower()

if contient_service :
	traitement_type = "service"
else:
	traitement_type = "exe"

log_event_level = "ERROR"
log_folder_level = "ERROR"
log_console_level = "INFO"

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

### Recupéaration des du nom du programme ###
programme = os.path.splitext(os.path.basename(sys.argv[0]))[0]
path = Path(sys.executable).resolve() if getattr(__import__("sys"), "frozen", False) else Path(__file__).resolve()

ini_filename = f"{programme}.ini"

### Sécurisation du nom luva dans le nom du programme ###
terme = "luva"
contient_luva = terme.lower() in exe_filename.lower()

# Erreur si il n'y a pas LUVA
if not contient_luva:
	log_secure("0","ERROR",f"Probleme de nom de programme.")
	input()
	sys.exit(1)  # ferme lapp

### Sécurisation des variables de logs ###
try:
	
	if not os.path.exists(ini_filename):
		log_secure("0","INFO",f"Pas de fichier ini '{ini_filename}'")
		log_validation = False
	else :
		log_secure("0","INFO",f"Fichier ini '{ini_filename}' est présent")
		log_validation = True
		config.read(f'{ini_filename}')
		if not config.sections():  # Vérifie si le fichier ini est vide
			raise FileNotFoundError(f"Le fichier de configuration '{ini_filename}' est vide.")
except Exception as e:
	log_secure("0","ERROR",f"Probleme de traitement du fichier '{ini_filename}': {e}")
	sys.exit(1)  # ferme lapp

try:
	if log_validation :
		enable_logging = config.getboolean('logging', 'enable_logging')
	else :
		enable_logging = False
except Exception as e:
	enable_logging = False

if enable_logging :
	try:
		log_folder = config['logging']['log_folder']
	except Exception as e:
		log_secure("0","ERROR",f"L'option 'log_folder' est manquante dans le fichier 'config.ini': {e}")
		sys.exit(1)  # Quitte l'application avec un code d'erreur
	try:
		log_folder_level = config['logging']['log_folder_level']
	except Exception as e:
		log_folder_level = "ERROR"

try:
	if log_validation :
		log_console_level = config['logging']['log_console_level']
	else :
		log_console_level = "INFO"
except Exception as e:
	log_console_level = "INFO"

try:	
	if enable_logging:
		os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log
except Exception as e:
	log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}")
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
	log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}")
	sys.exit(1)  # Quitte l'application avec un code d'erreur	

try:
	log_event_level = config['logging']['log_event_level']
	log_console("DEBUG",f"L'option 'log_event_level' est de niveau '{log_event_level}'")
except Exception as e:
	log_event_level = "ERROR"
verif = False

### Validation du type de processus via le nom de l'application ###
terme_creation = "creation"
contient_creation = terme_creation.lower() in exe_filename.lower()

terme_extraction = "extraction"
contient_extraction = terme_extraction.lower() in exe_filename.lower()

terme_keystore = "keystore"
contient_keystore = terme_keystore.lower() in exe_filename.lower()

terme_cacert = "cacerts"
contient_cacert = terme_cacert.lower() in exe_filename.lower()

terme_auto = "auto"
contient_auto = terme_auto.lower() in exe_filename.lower()

# permet de tester l'application en developpement
# DEV = True
DEV = True
# Permet de définir le périmètre de test

if DEV:
	PROCESSUS = "KEYSTORE" # a desactivé pour le test

try:
	if not DEV:
		if not contient_creation and not contient_extraction and not contient_keystore and not contient_cacert and not contient_auto:
			log_secure("0","ERROR",f"Le nom du programme doit contenir 'creation' ou 'extraction'")
			sys.exit(1)  # Quitte l'application avec un code d'erreur	
	if contient_creation:
		PROCESSUS = "CREATION"
	if contient_extraction:
		PROCESSUS = "EXTRACTION"
	if contient_keystore:
		PROCESSUS = "KEYSTORE"
	if contient_cacert:
		PROCESSUS = "CACERTS"
	if contient_auto:
		PROCESSUS = "AUTO"
except Exception as e:
	log_secure("0","ERROR",f"Le nom du programme doit contenir 'creation' ou 'extraction'")
	sys.exit(1)  # Quitte l'application avec un code d'erreur


log_level2 = log_levels.get(log_event_level, logging.ERROR)
logger_service.setLevel(log_level2)

# Traitement de keystore
def traitementkeystore(filename_ini):
	log_event("0","INFO",f"Creation du fichier localhost.keystore > pas encore programmé.")
	
# Main
if __name__ == "__main__":
	if DEV: print(PROCESSUS)
	if DEV: print(ini_filename)
	if DEV: print(path_filename)
	ini_path_filename = rf"{path_filename}\{ini_filename}"
	if DEV: print(path)

	log_event("0","INFO",f"Debut du traitement")
	
	if PROCESSUS == "CREATION":
		
		fonction_return = luva_crt.creation_crt_ini(ini_path_filename,path_filename,
													DEV)
													
		fonction_return_error = fonction_return["error"]
		if fonction_return_error != "":
			log_console("ERROR",f"{fonction_return["code"]}{fonction_return["error"]} : {fonction_return["message2"]}{fonction_return["message"]}")
		else :
			log_console("INFO",f"{fonction_return["code"]} : {fonction_return["message"]}")


	if PROCESSUS == "EXTRACTION":
		fonction_return = luva_pfx.extraction_pfx_ini(ini_path_filename,
														"CERTIFICAT",
														path_filename,
															DEV)
															
		fonction_return_error = fonction_return["error"]
		if fonction_return_error != "":
			log_console("ERROR",f"{fonction_return["code"]}{fonction_return["error"]} : {fonction_return["message2"]}{fonction_return["message"]}")
		else :
			log_console("INFO",f"{fonction_return["code"]} : {fonction_return["message"]}")
		
	if PROCESSUS == "CACERTS":
		fonction_return = luva_cacert.creation_cacert_ini(ini_path_filename,path_filename,
														DEV)							
		fonction_return_error = fonction_return["error"]
		if fonction_return_error != "":
			log_console("ERROR",f"{fonction_return["code"]}{fonction_return["error"]} : {fonction_return["message2"]}{fonction_return["message"]}")
		else :
			log_console("INFO",f"{fonction_return["code"]} : {fonction_return["message"]}")
		
	if PROCESSUS == "KEYSTORE":
		traitementkeystore(ini_filename)
		luva_cacert.creation_keystore(ini_path_filename,
														"localhost",
														path_filename,
														path_filename,
														DEV)
						# traitementkeystore(file)
		
	if PROCESSUS == "AUTO":
		traitement_dossier = Path(path).parent
		fintype_ini = "INI"
		for file in os.listdir(traitement_dossier):
			if file.endswith(fintype_ini.lower()) or file.endswith(fintype_ini):
				config_ini = configparser.ConfigParser()
				config_ini.read(f'{file}')
				try:
					INI_PROCESSUS = config_ini['param']['PROCESSUS']
					log_console("DEBUG",f"'INI_PROCESSUS' = '{INI_PROCESSUS}' pour {file}")
					if INI_PROCESSUS == "CREATION":
						
						if DEV: print(f"{path_filename}\{file}")
						fonction_return = luva_crt.creation_crt_ini(f"{path_filename}\{file}",path_filename,
																	DEV)
																	
						fonction_return_error = fonction_return["error"]
						if fonction_return_error != "":
							log_console("ERROR",f"{file} > {fonction_return["code"]}{fonction_return["error"]} : {fonction_return["message2"]}{fonction_return["message"]}")
						else :
							log_console("INFO",f"{file} > {fonction_return["code"]} : {fonction_return["message"]}")
					
					if INI_PROCESSUS == "EXTRACTION":
						if DEV: print(f"{path_filename}\{file}")
						fonction_return = luva_pfx.extraction_pfx_ini(f"{path_filename}\{file}",
																		"CERTIFICAT",
																		path_filename,
																			DEV)
																			
						fonction_return_error = fonction_return["error"]
						if fonction_return_error != "":
							log_console("ERROR",f"{fonction_return["code"]}{fonction_return["error"]} : {fonction_return["message2"]}{fonction_return["message"]}")
						else :
							log_console("INFO",f"{file} > {fonction_return["code"]} : {fonction_return["message"]}")
						
					if INI_PROCESSUS == "CACERTS":
						if DEV: print(f"{path_filename}\{file}")
						
						fonction_return = luva_cacert.creation_cacert_ini(f"{path_filename}\{file}",
																		path_filename,
																		DEV)							
						fonction_return_error = fonction_return["error"]
						if fonction_return_error != "":
							log_console("ERROR",f"{fonction_return["code"]}{fonction_return["error"]} : {fonction_return["message2"]}{fonction_return["message"]}")
						else :
							log_console("INFO",f"{file} > {fonction_return["code"]} : {fonction_return["message"]}")
						
						# traitementcacerts(file)
						
					if INI_PROCESSUS == "KEYSTORE":
						if DEV: print(f"{path_filename}\{file}")
						
						luva_cacert.creation_keystore(f"{path_filename}\{file}",
														"localhost",
														path_filename,
														path_filename,
														DEV)
						# traitementkeystore(file)
					
				except Exception as e:
					log_console("ERROR",f"balise 'INI_PROCESSUS' absent du fichier ini {file}")
				
				
	log_event("0","INFO",f"Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()