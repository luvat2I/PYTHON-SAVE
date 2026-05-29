import os
import shutil
import sys

import configparser
import time
import logging
import logging.handlers
from datetime import datetime, timedelta
import threading
from multiprocessing import Process, Queue
import win32evtlogutil
import win32evtlog
import win32api
import win32con

import pandas as pd

#traitement_type = "service"
traitement_type = "exe"

service_base = "YouDoc_SECU"

log_event_level = "WARNING"
log_folder_level="WARNING"
log_console_level="WARNING"

log_folder=""
nb_thread_source = "0"
nb_thread_traitement = "0"
nb_thread_flatten = "0"
nb_thread_cible = "0"

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
		log_enreg(level,log_text)
		log_service(level,log_text)
		log_console(level,log_text)
	elif type == "1" :
		log_enreg(level,log_text)
		log_console(level,log_text)
	elif type == "2" :
		log_console(level,log_text)
		
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

if traitement_type == "exe" :
	try:
		log_console_level = config['logging']['log_console_level']
		log_console("DEBUG",f"L'option 'log_console_level' est de niveau '{log_console_level}'")
	except Exception as e:
		log_secure("0","ERROR",f"L'option 'log_console_level' est manquante dans le fichier 'config.ini' : {e}")
		sys.exit(1)  # ferme lapp
	
try:
	global enable_logging
	enable_logging = config.getboolean('logging', 'enable_logging')
	if enable_logging :
		log_console("DEBUG",f"L'option 'enable_logging' est active")
	else :
		log_console("DEBUG",f"L'option 'enable_logging' est desactive")
except Exception as e:
	log_secure("0","ERROR",f"L'option 'enable_logging' est manquante dans le fichier 'config.ini' : {e}")
	sys.exit(1)  # ferme lapp

if enable_logging :
	try:
		log_folder_level = config['logging']['log_folder_level']
		log_console("DEBUG",f"L'option 'log_folder_level' est de niveau '{log_folder_level}'")
	except Exception as e:
		log_secure("0","ERROR",f"L'option 'log_folder_level' est manquante dans le fichier 'config.ini' : {e}")
		sys.exit(1)  # ferme lapp
		
	try:
		log_folder = config['logging']['log_folder']
		log_console("DEBUG",f"Le dossier de log est : {log_folder}")
	except Exception as e:
		log_event("2","ERROR",f"L'option 'log_folder' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	try:	
		os.makedirs(log_folder, exist_ok=True)
	except Exception as e:
		log_event("2","ERROR",f"Creation du dossier {log_folder} impossible : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	log_level = log_levels.get(log_folder_level, logging.ERROR)
	
	if enable_logging:
		log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
	
		logger_folder = logging.getLogger('folderloger')
		logger_folder.setLevel(log_level)
		file_handler = logging.FileHandler(log_filename)
		file_handler.setLevel(log_level)
		
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		file_handler.setFormatter(formatter)
		
		logger_folder.addHandler(file_handler)
	
	try:
		matrice_secu = config['files']['matrice_secu']
		log_console("DEBUG",f"L'option 'matrice_secu' est de niveau '{matrice_secu}'")
	except Exception as e:
		log_secure("0","ERROR",f"L'option 'matrice_secu' est manquante dans le fichier 'config.ini' : {e}")
		sys.exit(1)  # ferme lapp
		
try:
	log_event_level = config['logging']['log_event_level']
	log_console("DEBUG",f"L'option 'log_event_level' est de niveau '{log_event_level}'")
except Exception as e:
	log_secure("0","ERROR",f"L'option 'log_event_level' est manquante dans le fichier 'config.ini' : {e}")
	sys.exit(1)  # ferme lapp

### routine qui tourne et qui contrôle les thread ou le lancement des bonnes procédures ###
def traitement_routine():

	log_event("1","DEBUG",f"> 'traitement_routine' > Debut de la procedure")
	print (matrice_secu)
	
	# Remplacez 'votre_fichier.xlsx' par le chemin de votre fichier Excel
	df = pd.read_excel(matrice_secu, sheet_name='emotion')
	
	# Compter le nombre de valeurs non nulles dans chaque colonne
	compte_colonnes = df.count()
	
	# Trouver la colonne avec le plus grand nombre de valeurs non nulles
	colonne_max = compte_colonnes.idxmax()  # Nom de la colonne
	nombre_valeurs_colonne_max = compte_colonnes.max()  # Nombre de valeurs non nulles
	
	# Afficher le résultat
	print(f'La colonne avec le plus grand nombre de valeurs remplies est : {colonne_max} avec {nombre_valeurs_colonne_max} valeurs remplies.')
	
	# Compter le nombre de valeurs non nulles dans chaque colonne
	# Compter le nombre de valeurs non nulles dans chaque ligne
	compte_lignes = df.count(axis=1)
	
	# Trouver l'index de la ligne avec le plus grand nombre de valeurs non nulles
	ligne_max_index = compte_lignes.idxmax()  # Index de la ligne
	nombre_valeurs_ligne_max = compte_lignes.max()  # Nombre de valeurs non nulles
	
	# Afficher le résultat
	print(f'La ligne avec le plus grand nombre de valeurs remplies est : {ligne_max_index} avec {nombre_valeurs_ligne_max} valeurs remplies.')
	
	valeur_a1 = df.iloc[0, 0]  # Les index commencent à 0, donc A1 est (0, 0)
	print(valeur_a1)
	
	log_event("1","DEBUG",f"> 'traitement_routine' > Fin de la procedure")
	
def main():
	log_event("0","DEBUG",f"Fin de la recupération des configurations du fichier ini")
	log_event("1","DEBUG",f"Lancement du traitement")
	traitement_routine()
	log_event("0","DEBUG",f"Fin du programme")

if __name__ == '__main__':
	main()
