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
#traitement_type = "service"
traitement_type = "exe"

service_base = "YouDoc_Flatten"

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
	global fichiers_traites
	fichiers_traites = set()
	
	# Initialisation des variables de numérotation des threads
	thread_source = 1
	thread_traitement = 1
	thread_flatten = 1
	thread_cible = 1
	
	# Variable de contrôle de nombre de thread
	thread_source_nb = 0
	thread_traitement_nb = 0
	thread_flatten_nb = 0
	thread_cible_nb = 0
	
	# initialisation des queues
	source_queue = Queue()
	flatten_queue = Queue()
	cible_queue = Queue()
	
	
	if not enable_threading :
		log_event("1","DEBUG",f"> 'traitement_routine' > 'enable_threading' est desactive")
		while True :
			liste_source(source_queue,)
			deplacement_source(source_queue,flatten_queue)
			traitement_flatten(flatten_queue,cible_queue)
			deplacement_cible(cible_queue)
	else :
		log_event("1","DEBUG",f"> 'traitement_routine' > 'enable_threading' est active")
		while True :
			if thread_source_nb < (int(nb_thread_source)) :
				log_event("1","DEBUG",f"> 'traitement_routine' > creation thread_source_{thread_source}")
				thread = threading.Thread(target=liste_source, args=(source_queue,), name =f"thread_source_{thread_source}")
				threads.append(thread)
				thread.start()
				thread_source += 1
				thread_source_nb += 1
				
			if thread_traitement_nb < (int(nb_thread_traitement)) :
                log_event("1","DEBUG",f"> 'traitement_routine' > creation thread_traitement_{thread_traitement}")
				thread = threading.Thread(target=deplacement_source, args=(source_queue,flatten_queue), name =f"thread_traitement_{thread_traitement}")
				threads.append(thread)
				thread.start()
				thread_traitement += 1
				thread_traitement_nb += 1
				
			if thread_flatten_nb < (int(nb_thread_flatten)) :
                log_event("1","DEBUG",f"> 'traitement_routine' > creation thread_flatten_{thread_flatten}")
				thread = threading.Thread(target=traitement_flatten, args=(flatten_queue,cible_queue), name =f"thread_flatten_{thread_flatten}")
				threads.append(thread)
				thread.start()
				thread_flatten += 1
				thread_flatten_nb += 1
				
			if thread_cible_nb < (int(nb_thread_cible)) :
                log_event("1","DEBUG",f"> 'traitement_routine' > creation thread_cible_{thread_cible}")
				thread = threading.Thread(target=deplacement_cible, args=(cible_queue,), name =f"thread_cible_{thread_cible}")
				threads.append(thread)
				thread.start()
				thread_cible += 1
				thread_cible_nb += 1
			
			if (int(nb_thread_source)) == 0 :
				liste_source(source_queue,)
			if (int(nb_thread_traitement)) == 0 :
				deplacement_source(source_queue,flatten_queue)
			if (int(nb_thread_flatten)) == 0 :
				traitement_flatten(flatten_queue,cible_queue)
			if (int(nb_thread_cible)) == 0 :
				deplacement_cible(cible_queue)
	
	log_event("1","DEBUG",f"> 'traitement_routine' > Fin de la procedure")
	
def liste_source(source_queue):

	log_event("1","DEBUG",f"> 'source_queue' > Debut de la procedure")
	
	name_thread_actuel = ""
	verif_continue = True
	if enable_threading :
		try:
			thread_actuel = threading.current_thread()
			name_thread_actuel = f"th > {thread_actuel} "
		except Exception as e:
			name_thread_actuel = ""
	while verif_continue:
		for file in os.listdir(source_folder) :
			if file.endswith(fic_type) and file not in fichiers_traites:
				fichiers_traites.add(file)
				source_queue.put(file)
				log_event("1","INFO",f"{file}")
				log_event("1","DEBUG",f"{name_thread_actuel}Ajoute dans la liste de traitement '{file}'")
				if int(nb_thread_source) == 0 :
					verif_continue = False
					break 
		log_event("1","DEBUG",f"{name_thread_actuel}attent un fichier")
		time.sleep(time_sleep)
	log_event("1","DEBUG",f"{name_thread_actuel}fin du traitement 'source_queue'")
	log_event("1","DEBUG",f"> 'source_queue' > Fin de la procedure")

def deplacement_source(source_queue,flatten_queue):
	
	log_event("1","DEBUG",f"debut du traitement 'deplacement_source'")
	name_thread_actuel = ""
	verif_continue = True
	if enable_threading :
		try:
			thread_actuel = threading.current_thread()
			name_thread_actuel = f"th > {thread_actuel} > "
		except Exception as e:
			name_thread_actuel = ""
	while verif_continue == True:
		try:
			file = source_queue.get(timeout=2)
			log_event("1","DEBUG",f"{name_thread_actuel}debut du traitement 'deplacement_source' pour {file}")
			fic_name = file
			
			fic_save_name = fic_name.replace(fic_type, f'.save{fic_type}')
			pdf_name = fic_name.replace(fic_type, '.pdf')
			pdf_save_name = fic_name.replace(fic_type, '.save.pdf')
			pdf_flatten_name = fic_name.replace(fic_type, '.flatten.pdf')
			
			source_fic_name = os.path.join(source_folder, fic_name)
			source_pdf_name = os.path.join(source_folder, pdf_name)
			
			archive_fic_name = os.path.join(archive_folder, fic_name)
			archive_pdf_name = os.path.join(archive_folder, pdf_name)
			
			traitement_fic_save_name = os.path.join(traitement_folder, fic_save_name)
			traitement_pdf_save_name = os.path.join(traitement_folder, pdf_save_name)
			traitement_pdf_flatten_name = os.path.join(traitement_folder, pdf_flatten_name)
			
			cible_fic_name = os.path.join(cible_folder, fic_name)
			cible_pdf_name = os.path.join(cible_folder, pdf_name)
			
			if os.path.exists(source_pdf_name) :
				if fic_type == ".pdf" :
					if enable_archive :
						log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{source_pdf_name}' vers '{archive_pdf_name}'")
						shutil.copy(source_pdf_name, archive_pdf_name)
					log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{source_pdf_name}' vers '{traitement_pdf_save_name}'")
					shutil.copy(source_pdf_name, traitement_pdf_save_name)
					log_event("1","DEBUG",f"{name_thread_actuel}supprime le fichier '{source_pdf_name}'")
					os.remove(source_pdf_name)
					
				else :
					if enable_archive :
						log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{source_pdf_name}' vers '{archive_pdf_name}'")
						shutil.copy(source_pdf_name, archive_pdf_name)
						log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{source_fic_name}' vers '{archive_fic_name}'")
						shutil.copy(source_fic_name, archive_fic_name)
					log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{source_pdf_name}' vers '{traitement_pdf_save_name}'")
					shutil.copy(source_pdf_name, traitement_pdf_save_name)
					log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{source_fic_name}' vers '{traitement_fic_save_name}'")
					shutil.copy(source_fic_name, traitement_fic_save_name)
					log_event("1","DEBUG",f"{name_thread_actuel}supprime le fichier '{source_pdf_name}'")
					os.remove(source_pdf_name)
					log_event("1","DEBUG",f"{name_thread_actuel}supprime le fichier '{source_fic_name}'")
					os.remove(source_fic_name)

			else : # on a pas de pdf
				log_event("1","DEBUG",f"{name_thread_actuel}pas de fichier pdf pour '{file}' à traiter")
				
			log_event("1","DEBUG",f"{name_thread_actuel}fin du traitement 'deplacement_source' pour {file}")
			flatten_queue.put(file)
			
			if int(nb_thread_traitement) == 0 :
				verif_continue = False
				break 
		except Exception as e:
			log_event("1","DEBUG",f"{name_thread_actuel}Erreur en Exception : {e}")
			if int(nb_thread_traitement) == 0 :
				verif_continue = False
				break 
			continue
	log_event("1","DEBUG",f"fin du traitement 'deplacement_source'")

def traitement_flatten(flatten_queue,cible_queue):
	
	log_event("1","DEBUG",f"debut du traitement 'traitement_flatten'")
	name_thread_actuel = ""
	verif_continue = True
	if enable_threading :
		try:
			thread_actuel = threading.current_thread()
			name_thread_actuel = f"th > {thread_actuel} "
		except Exception as e:
			name_thread_actuel = ""
	while verif_continue == True:
		try:
			file = flatten_queue.get(timeout=2)
			log_event("1","DEBUG",f"{name_thread_actuel}debut du traitement 'traitement_flatten' pour {file}")
			
			fic_name = file
			
			fic_save_name = fic_name.replace(fic_type, f'.save{fic_type}')
			pdf_name = fic_name.replace(fic_type, '.pdf')
			pdf_save_name = fic_name.replace(fic_type, '.save.pdf')
			pdf_flatten_name = fic_name.replace(fic_type, '.flatten.pdf')
			
			source_fic_name = os.path.join(source_folder, fic_name)
			source_pdf_name = os.path.join(source_folder, pdf_name)
			
			archive_fic_name = os.path.join(archive_folder, fic_name)
			archive_pdf_name = os.path.join(archive_folder, pdf_name)
			
			traitement_fic_save_name = os.path.join(traitement_folder, fic_save_name)
			traitement_pdf_save_name = os.path.join(traitement_folder, pdf_save_name)
			traitement_pdf_flatten_name = os.path.join(traitement_folder, pdf_flatten_name)
			
			cible_fic_name = os.path.join(cible_folder, fic_name)
			cible_pdf_name = os.path.join(cible_folder, pdf_name)
			
			log_event("1","INFO",f"{name_thread_actuel}Debut flatten le fichier '{traitement_pdf_save_name}'")
			# Fonction pour aplatir un PDF en créant une image pour chaque page (ne pas toucher)
			images = convert_from_path(traitement_pdf_save_name, poppler_path=poppler_folder)
			c = canvas.Canvas(traitement_pdf_flatten_name, pagesize=letter)
			images_folder = os.path.join(traitement_folder, 'images')
			for i, image in enumerate(images):
				# Enregistrer l'image temporairement dans le sous-dossier images
				image_path = os.path.join(images_folder, f"{traitement_pdf_save_name}_{i}.png")
				image.save(image_path)
				c.drawImage(image_path, 0, 0, width=letter[0], height=letter[1])
				c.showPage()
				# Supprimer l'image temporaire après utilisation
				os.remove(image_path)
			
			c.save()
			log_event("1","INFO",f"{name_thread_actuel}FIn flatten le fichier '{traitement_pdf_save_name}'")
			log_event("1","DEBUG",f"{name_thread_actuel}supprime le fichier '{traitement_pdf_save_name}'")
			os.remove(traitement_pdf_save_name)
			
			log_event("1","DEBUG",f"{name_thread_actuel}fin du traitement 'traitement_flatten' pour {file}")
			
			cible_queue.put(file)
			if int(nb_thread_flatten) ==0 :
				verif_continue = False
				break
		except Exception as e:
			log_event("1","DEBUG",f"{name_thread_actuel}Erreur en Exception : {e}")
			if int(nb_thread_flatten) == 0 :
				verif_continue = False
				break
			continue
			
		log_event("1","DEBUG",f"{name_thread_actuel}attent un fichier à flatten")
		time.sleep(time_sleep)
		
	log_event("1","DEBUG",f"fin du traitement 'traitement_flatten'")

def deplacement_cible(cible_queue):
	
	log_event("1","DEBUG",f"debut du traitement 'deplacement_cible'")
	name_thread_actuel = ""
	nb_element = cible_queue.qsize()
	verif_continue = True
	if enable_threading :
		try:
			thread_actuel = threading.current_thread()
			name_thread_actuel = f"th > {thread_actuel} "
		except Exception as e:
			name_thread_actuel = ""
	while verif_continue == True:
		try:
			log_event("1","DEBUG",f"4")
			file = cible_queue.get(timeout=2)
			log_event("1","DEBUG",f"{name_thread_actuel}debut du traitement 'deplacement_cible' pour {file}")
			fic_name = file
			
			fic_save_name = fic_name.replace(fic_type, f'.save{fic_type}')
			pdf_name = fic_name.replace(fic_type, '.pdf')
			pdf_save_name = fic_name.replace(fic_type, '.save.pdf')
			pdf_flatten_name = fic_name.replace(fic_type, '.flatten.pdf')
			
			source_fic_name = os.path.join(source_folder, fic_name)
			source_pdf_name = os.path.join(source_folder, pdf_name)
			
			archive_fic_name = os.path.join(archive_folder, fic_name)
			archive_pdf_name = os.path.join(archive_folder, pdf_name)
			
			traitement_fic_save_name = os.path.join(traitement_folder, fic_save_name)
			traitement_pdf_save_name = os.path.join(traitement_folder, pdf_save_name)
			traitement_pdf_flatten_name = os.path.join(traitement_folder, pdf_flatten_name)
			
			cible_fic_name = os.path.join(cible_folder, fic_name)
			cible_pdf_name = os.path.join(cible_folder, pdf_name)
			
			
			
			if fic_type == ".pdf" :
				
				log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{traitement_pdf_flatten_name}' vers '{cible_pdf_name}'")
				shutil.copy(traitement_pdf_flatten_name, cible_pdf_name)
				log_event("1","DEBUG",f"{name_thread_actuel}supprime le fichier '{traitement_pdf_flatten_name}'")
				os.remove(traitement_pdf_flatten_name)
				
			else :
				
				log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{traitement_pdf_flatten_name}' vers '{cible_pdf_name}'")
				shutil.copy(traitement_pdf_flatten_name, cible_pdf_name)
				log_event("1","DEBUG",f"{name_thread_actuel}deplace le fichier '{traitement_pdf_flatten_name}' vers '{cible_fic_name}'")
				shutil.copy(traitement_fic_save_name, cible_fic_name)
				
				log_event("1","DEBUG",f"{name_thread_actuel}supprime le fichier '{traitement_pdf_flatten_name}'")
				os.remove(traitement_pdf_flatten_name)
				log_event("1","DEBUG",f"{name_thread_actuel}supprime le fichier '{traitement_pdf_flatten_name}'")
				os.remove(traitement_fic_save_name)
		
			
			log_event("1","DEBUG",f"{name_thread_actuel}fin du traitement 'deplacement_cible' pour {file}")
			
			if int(nb_thread_cible) == 0 :
				print("5")
				verif_continue = False
				break 
		except Exception as e:
			log_event("1","DEBUG",f"Erreur en Exception : {e}")
			if int(nb_thread_cible) == 0 :
				verif_continue = False
				break 
			continue
	log_event("1","DEBUG",f"fin du traitement 'deplacement_cible'")

def main():
	log_event("0","WARNING",f"Lancement de YouDoc FLATTEN")

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
		global traitement_folder
		traitement_folder = config['folders']['traitement_folder']
		log_event("1","INFO",f"Le dossier traitement est : {traitement_folder}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'traitement_folder' est manquante dans le fichier 'config.ini' : {e}")
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
		os.makedirs(traitement_folder, exist_ok=True)
		images_folder = os.path.join(traitement_folder, 'images')
		os.makedirs(images_folder, exist_ok=True)
	except Exception as e:
		log_event("0","ERROR",f"Creation du dossier {traitement_folder} impossible : {e}")
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
		global enable_archive
		enable_archive = config.getboolean('archives', 'enable_archive')
		if enable_archive :
			log_event("1","INFO",f"L'option 'enable_archive' est active")
		else :
			log_event("1","INFO",f"L'option 'enable_archive' est desactive")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'enable_archive' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	if enable_archive :
		try:
			global archive_folder
			archive_folder = config['archives']['archive_folder']
			log_event("1","INFO",f"Le dossier archive est : {archive_folder}")
		except Exception as e:
			log_event("0","ERROR",f"L'option 'archive_folder' est manquante dans le fichier 'config.ini' : {e}")
			if traitement_type == "exe" :
				input("Appuyez sur une touche pour quitter...")
			sys.exit(1)  # ferme lapp
		
		try:	
			os.makedirs(archive_folder, exist_ok=True)
		except Exception as e:
			log_event("0","ERROR",f"Creation du dossier {archive_folder} impossible : {e}")
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
		global enable_other_type
		enable_other_type = config.getboolean('files', 'enable_other_type')
		if enable_other_type :
			log_event("1","INFO",f"'enable_other_type' est active")
		else :
			log_event("1","INFO",f"'enable_other_type' est desactive")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'enable_other_type' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	try:
		global enable_threading
		enable_threading = config.getboolean('config', 'enable_threading')
		if enable_threading :
			log_event("1","INFO",f"'enable_threading' est active")
		else :
			log_event("1","INFO",f"'enable_threading' est desactive")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'enable_threading' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
		
	if enable_threading :
		try:
			global nb_thread_source
			nb_thread_source = config['config']['nb_thread_source']
			log_event("1","INFO",f"Le nombre de thread utilisé pour faire la liste des fichiers sources : {nb_thread_source}")
		except Exception as e:
			log_event("0","ERROR",f"L'option 'nb_thread_source' est manquante dans le fichier 'config.ini' : {e}")
			if traitement_type == "exe" :
				input("Appuyez sur une touche pour quitter...")
			sys.exit(1)  # ferme lapp
		
		try:
			global nb_thread_traitement
			nb_thread_traitement = config['config']['nb_thread_traitement']
			log_event("1","INFO",f"Le nombre de thread utilisé pour deplacer les fichiers dans archive et traitement : {nb_thread_traitement}")
		except Exception as e:
			log_event("0","ERROR",f"L'option 'nb_thread_traitement' est manquante dans le fichier 'config.ini' : {e}")
			if traitement_type == "exe" :
				input("Appuyez sur une touche pour quitter...")
			sys.exit(1)  # ferme lapp
		
		try:
			global nb_thread_flatten
			nb_thread_flatten = config['config']['nb_thread_flatten']
			log_event("1","INFO",f"Le nombre de thread utilisé pour flatten : {nb_thread_flatten}")
		except Exception as e:
			log_event("0","ERROR",f"L'option 'nb_thread_flatten' est manquante dans le fichier 'config.ini' : {e}")
			if traitement_type == "exe" :
				input("Appuyez sur une touche pour quitter...")
			sys.exit(1)  # ferme lapp
		
		try:
			global nb_thread_cible
			nb_thread_cible = config['config']['nb_thread_cible']
			log_event("1","INFO",f"Le nombre de thread utilisé pour copier dans le dossier cible : {nb_thread_cible}")
		except Exception as e:
			log_event("0","ERROR",f"L'option 'nb_thread_cible' est manquante dans le fichier 'config.ini' : {e}")
			if traitement_type == "exe" :
				input("Appuyez sur une touche pour quitter...")
			sys.exit(1)  # ferme lapp
	
	try:
		global poppler_folder
		poppler_folder = config['config']['poppler_folder']
		log_event("1","INFO",f"Le dossier Poppler se trouve : {poppler_folder}")
	except Exception as e:
		log_event("0","ERROR",f"L'option 'poppler_folder' est manquante dans le fichier 'config.ini' : {e}")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	executable_path = os.path.join(poppler_folder, 'pdftoppm.exe')
	if os.path.exists(executable_path):
		log_event("1","DEBUG",f"Le dossier Poppler est valide")
	else :
		log_event("0","ERROR",f"Le dossier poppler {poppler_folder} n'est pas valide")
		if traitement_type == "exe" :
			input("Appuyez sur une touche pour quitter...")
		sys.exit(1)  # ferme lapp
	
	log_event("0","DEBUG",f"Fin de la recupération des configurations du fichier ini")
	log_event("1","DEBUG",f"Lancement du traitement")
	traitement_routine()
	log_event("0","DEBUG",f"Fin du programme")

if __name__ == '__main__':
	main()
