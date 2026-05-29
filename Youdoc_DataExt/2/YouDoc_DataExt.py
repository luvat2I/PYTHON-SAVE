import os
import shutil
import sys
import re
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
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
import log_aff


# le programme est fait pour être executé en service uniquement
traitement_type = "service"
# traitement_type = "exe"
# nom du service
service_base = "Youdoc_DataExt"

log_event_level = "WARNING"
log_folder_level="WARNING"
log_console_level="WARNING"

log_folder=""
nb_thread_liste = "0"
nb_thread_traitement = "0"

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
	log_event_level = config['logging']['log_event_level']
	log_console("DEBUG",f"L'option 'log_event_level' est de niveau '{log_event_level}'")
except Exception as e:
	log_secure("0","ERROR",f"L'option 'log_event_level' est manquante dans le fichier 'config.ini' : {e}")
	sys.exit(1)  # ferme lapp

	
	
	
	
	
	
### routine qui tourne et qui contrôle les thread ou le lancement des bonnes procédures ###
def traitement_routine():

	log_event("1","DEBUG",f"> 'traitement_routine' > Debut de la procedure")
	
	log_event("1","DEBUG",f"> 'traitement_routine' > Initialisation des variables")
	# Liste pour stocker les threads
	threads = []
	
	global fin_boucle
	fin_boucle = False
	global nb_minutes
	nb_minutes = 0
	global Nb_queue
	Nb_queue = Taille_du_lot
	global Time_debut
	Time_debut = datetime.now() - timedelta(minutes=Temps_minutes)
	
	# Initialisation des variables de numérotation des threads
	thread_source = 1
	thread_traitement = 1

	# Variable de contrôle de nombre de thread
	thread_source_nb = 0
	thread_traitement_nb = 0

	# initialisation des queues
	source_queue = Queue()
	
	while True :
		if thread_source_nb < 1 :
			log_event("1","DEBUG",f"> 'traitement_routine' > creation thread_source_{thread_source}")
			thread = threading.Thread(target=liste_source, args=(source_queue,), name =f"thread_source_{thread_source}")
			threads.append(thread)
			thread.start()
			thread_source += 1
			thread_source_nb += 1
			
		if thread_traitement_nb < 1 :
			log_event("1","DEBUG",f"> 'traitement_routine' > creation thread_traitement_{thread_traitement}")
			thread = threading.Thread(target=deplacement_source, args=(source_queue,), name =f"thread_traitement_{thread_traitement}")
			threads.append(thread)
			thread.start()
			thread_traitement += 1
			thread_traitement_nb += 1
		
	log_event("1","DEBUG",f"> 'traitement_routine' > Fin de la procedure")
	
def liste_source(source_queue):

	log_event("1","DEBUG",f"> 'source_queue' > Debut de la procedure")

	global fin_boucle
	global nb_minutes
	global Nb_queue
	global Time_debut
	global Temps_minutes
	global source_folder
	global cible_folder
	
	global source_urgence
	
	verif_continue = True
	name_thread_actuel = ""
	fichiers_traites = set()
	
	# recup nom thread
	try:
		thread_actuel = threading.current_thread()
		name_thread_actuel = f"th > {thread_actuel} "
	except Exception as e:
		name_thread_actuel = ""
	
	while verif_continue:
		# calcul du temps de la boucle en cours en minutes
		maintenant = datetime.now()
		difference = maintenant - Time_debut
		nb_minutes = difference.total_seconds() / 60 
		
		if nb_minutes >= Temps_minutes and fin_boucle :
			fin_boucle = False
			Time_debut = datetime.now()
			Nb_queue = 0
			nb_minutes = 0
			fichiers_traites = set()
		
		if nb_minutes >= Temps_minutes and not fin_boucle :
			fin_boucle = True
			for file in os.listdir(cible_folder) :
				if file.endswith(fic_type) :
					fin_boucle = False
			
		try:
			for file in os.listdir(source_urgence) :
				if file.endswith(fic_type) and file not in fichiers_traites and Nb_queue < Taille_du_lot:
					fichiers_traites.add(file)
					source_queue.put(file)
					log_event("1","INFO",f"{file}")
					log_event("1","DEBUG",f"{name_thread_actuel} Ajoute dans la liste de traitement '{file}'")
					Nb_queue = Nb_queue + 1		
		
			for file in os.listdir(source_folder) :
				if file.endswith(fic_type) and file not in fichiers_traites and Nb_queue < Taille_du_lot:
					fichiers_traites.add(file)
					source_queue.put(file)
					log_event("1","INFO",f"{file}")
					log_event("1","DEBUG",f"{name_thread_actuel} Ajoute dans la liste de traitement '{file}'")
					Nb_queue = Nb_queue + 1		
		except Exception as e:
			log_event("1","DEBUG",f"{name_thread_actuel}Erreur en Exception : {e}")
			continue
			
	log_event("1","DEBUG",f"{name_thread_actuel}fin du traitement 'source_queue'")
	log_event("1","DEBUG",f"> 'source_queue' > Fin de la procedure")

def deplacement_source(source_queue):
	
	log_event("1","DEBUG",f"debut du traitement 'deplacement_source'")
	name_thread_actuel = ""
	verif_continue = True
	
	global cible_folder
	global source_folder
	global source_urgence
	
	try:
		thread_actuel = threading.current_thread()
		name_thread_actuel = f"th > {thread_actuel} > "
	except Exception as e:
		name_thread_actuel = ""
		
	while verif_continue == True:
		
		try:
			
			if source_queue.empty():
				continue
					
			file = source_queue.get(timeout=2)
			
			log_event("1","DEBUG",f"{name_thread_actuel}debut du traitement 'deplacement_source' pour {file}")
			fic_name = file
			
			urgence_fic_name = os.path.join(source_urgence, fic_name)
			source_fic_name = os.path.join(source_folder, fic_name)
			
			
			if os.path.exists(urgence_fic_name):
				source_fic = urgence_fic_name
				folder=source_urgence
			else:
				source_fic = source_fic_name
				folder=source_folder
			
			fic_base = file.replace(fic_type, '.')
			cible_fic_name = os.path.join(cible_folder, fic_name)
			
			matching_files = []
			for filename2 in os.listdir(folder):
				if filename2.startswith(fic_base):
					if fic_name != filename2 and len(fic_name) == len(filename2) :
						matching_files.append(filename2)
				
			for filename2 in matching_files:
				# Construire le chemin complet du fichier source
				source_file = os.path.join(folder, filename2)
				# Construire le chemin complet du fichier de destination
				destination_file = os.path.join(cible_folder, filename2)
				
				# Copier le fichier
				shutil.copy(source_file, destination_file)
				# Supprimer le fichier source après la copie
				os.remove(source_file)
				
			shutil.copy(source_fic, cible_fic_name)
			os.remove(source_fic)
			
			
		except Exception as e:
			log_event("1","DEBUG",f"{name_thread_actuel}Erreur en Exception : {e}")
			continue
	log_event("1","DEBUG",f"fin du traitement 'deplacement_source'")
	
def main():
	log_event("0","WARNING",f"Lancement de YouDoc DataExt")

	log_event("1","INFO",f"le niveau de log de la console est : {log_console_level}")
	if enable_logging :
		log_event("1","INFO",f"L'option 'enable_logging' est active")
	else :
		log_event("1","INFO",f"L'option 'enable_logging' est desactive")
	
	if enable_logging:
		log_event("1","INFO",f"le dossier de log est : {log_folder}")
		log_event("1","INFO",f"le niveau de log du fichier est : {log_folder_level}")

	try:
		global source_folder
		source_folder = config['folders']['source_folder']
		log_event("1","INFO",f"Le dossier source est : {source_folder}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'source_folder' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
		
	try:
		global source_urgence
		source_urgence = config['folders']['source_urgence']
		log_event("1","INFO",f"Le dossier source est : {source_urgence}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'source_urgence' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	try:
		global cible_folder
		cible_folder = config['folders']['cible_folder']
		log_event("1","INFO",f"Le dossier cible est : {cible_folder}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'cible_folder' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	    
	try:	
		os.makedirs(source_folder, exist_ok=True)
	except Exception as e:
		log_event("0","ERROR",f"Creation du dossier {source_folder} impossible : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	    
	try:	
		os.makedirs(source_urgence, exist_ok=True)
	except Exception as e:
		log_event("0","ERROR",f"Creation du dossier {source_urgence} impossible : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
		
	try:	
		os.makedirs(cible_folder, exist_ok=True)
	except Exception as e:
		log_event("0","ERROR",f"Creation du dossier {cible_folder} impossible : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp

	try:
		global fic_type
		fic_type = config['files']['fic_type']
		log_event("1","INFO",f"Le type de fichier pivot est : {fic_type}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'fic_type' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	try:
		global Temps_minutes
		Temps_minutes = int(config['traitement']['Temps_minutes'])
		log_event("1","INFO",f"Le temps de traitement est : {Temps_minutes}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'Temps_minutes' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	try:
		global Taille_du_lot
		Taille_du_lot = int(config['traitement']['Taille_du_lot'])
		log_event("1","INFO",f"La taille du lot est de : {Taille_du_lot}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'Taille_du_lot' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp

	log_event("0","DEBUG",f"Fin de la recupération des configurations du fichier ini")
	log_event("1","DEBUG",f"Lancement du traitement")
	traitement_routine()
	log_event("0","DEBUG",f"Fin du programme")

if __name__ == '__main__':
	main()
