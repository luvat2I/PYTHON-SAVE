import os
import sys
import re
import argparse
import shutil
import configparser
import time
import logging
import logging.handlers
from datetime import datetime, timedelta
import threading
from multiprocessing import Process, Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import win32evtlogutil
import win32evtlog
import win32api
import win32con

traitement_type = "exe"
service_base = "HTML2MHTML"

log_service_level = "WARNING"
log_folder_level="DEBUG"
log_console_level="DEBUG"

log_folder=""

nb_thread_liste="0"
nb_thread_source="0"
nb_thread_htmltomhtml="0"
nb_thread_cible="0"

log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR
}

time_sleep=0

# Fonction de conversion des adresses cygwin en windows
def cygwin_to_windows(cyg_path):
	return cyg_path.replace("/cygdrive/c/", "C:\\").replace("/", "\\")

def find_chromedriver(start_dir):
	executable_path = os.path.join(start_dir, 'chromedriver.exe')
	if os.path.exists(executable_path):
		return executable_path
	return None

#log dans les informations des events de services
def log_service(level,log_text):
	if level == "DEBUG" and log_service_level == "DEBUG" :
		logger_service.debug(f"{log_text}")
	if level == "INFO" and (log_service_level == "DEBUG" or log_service_level == "INFO") :
		logger_service.info(f"{log_text}")
	elif level == "WARNING" and (log_service_level == "DEBUG" or log_service_level == "INFO" or log_service_level == "WARNING"):
		logger_service.warning(f"{log_text}")
	elif level == "ERROR" :
		logger_service.error(f"{log_text}")

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
	
#log dans les informations des events de services
def log_secure(type,level,log_text):
	if type == "0" :
		log_service(level,log_text)
	log_console(level,log_text)
	if traitement_type == "exe" and level == "ERROR" :
		input("Appuyez sur une touche pour quitter...")

# création d'une source d'événements si elle n'existe pas pour le mode service
def create_event_source(source_name):
	try:
		win32evtlogutil.ReportEvent(source_name, 1, eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE, strings=[source_name])
	except Exception as e:
		win32api.RegCreateKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}')
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'EventMessageFile', win32con.REG_SZ, os.path.abspath(__file__))
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'TypesSupported', win32con.REG_DWORD, 7)

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
		

# Lecture du fichier de configuration
config = configparser.ConfigParser()

logger_service = logging.getLogger(service_base)
logger_service.setLevel(logging.WARNING)
event_handler = logging.handlers.NTEventLogHandler(service_base)
logger_service.addHandler(event_handler)
create_event_source(f"{service_base}")

logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

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
		
# Chemins des dossiers
source_folder = config['folders']['source_folder']				  # dossier source
traitement_folder = config['folders']['traitement_folder']		  # dossier de conversion
cible_folder = config['folders']['cible_folder']				  # dossier cible

# Créer les dossiers s'ils n'existent pas (sauf pour le dossier final)
os.makedirs(source_folder, exist_ok=True)
os.makedirs(traitement_folder, exist_ok=True)

# Gestion des archives
enable_archive = config.getboolean('archives', 'enable_archive')
archive_folder = config['archives']['archive_folder']
if enable_archive:
	os.makedirs(archive_folder, exist_ok=True)

# Type de fichier qui declenche l'applatissement html
fic_type = config['files']['fic_type']

chrome_folder = config['param']['chrome_folder']
nb_thread_liste = config['param']['nb_thread_liste']
nb_thread_source = config['param']['nb_thread_source']
nb_thread_htmltomhtml = config['param']['nb_thread_htmltomhtml']
nb_thread_cible = config['param']['nb_thread_cible']

# recherche du path chromedriver
start_directory = f"{chrome_folder}"  # Vous pouvez changer cela pour un autre répertoire si nécessaire
chromedriver_path = find_chromedriver(start_directory)

if chromedriver_path:
	print(f"Chromedriver trouvé à : {chromedriver_path}")
else:
	print("Chromedriver non trouvé.")

	
# Function to set up logging
def setup_logging(verbosity):
	log_levels = {
		'DEBUG': logging.DEBUG,
		'INFO': logging.INFO,
		'WARNING': logging.WARNING,
		'ERROR': logging.ERROR,
		'CRITICAL': logging.CRITICAL
	}
	level = log_levels.get(verbosity.upper(), logging.INFO)
	logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')


	
def configure_chrome_options():
	options = Options()
	options.add_argument('--headless')
	options.add_argument('--disable-gpu')
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-extensions')
	options.add_argument('--disable-infobars')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--log-level=3')
	options.add_argument('--user-agent=Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)')
	return options


def liste_source(file_source):
	
	verif_continue = True
	
	while verif_continue:
		for file in os.listdir(source_folder):
		
			fic_name = file
			html_name = fic_name.replace(fic_type, '.html')
			fic_path = os.path.join(source_folder, file)
			html_path = os.path.join(source_folder, file.replace(fic_type, '.html'))
			
			if file.endswith(fic_type) and os.path.exists(html_path) and file not in fichiers_traites:
				source_fic_name = file
				print(f"traitement {file}")
				
				log_event("1","DEBUG",f"{file} > Ajout dans la file de traitement")
				
				fichiers_traites.add(file)
				file_source.put(file)
				if (int(nb_thread_liste)) == 0:
					verif_continue = False
					break
		if (int(nb_thread_liste)) == 0:
			verif_continue = False
			break
		time.sleep(time_sleep)

def deplacement_source(file_source,file_htmltomhtml):
	verif_continue = True
	while verif_continue:
		file = ""
		try:
			if file_source.qsize() == 0 and int(nb_thread_source) == 0 :
				verif_continue = False
				break 
			file = file_source.get()
			
			log_event("1","DEBUG",f"{file} > deplacement de source vers traitement")
			
			fic_name = file
			
			html_name = fic_name.replace(fic_type, '.html')
			mhtml_name = fic_name.replace(fic_type, '.mhtml')
			
			source_fic_path = os.path.join(source_folder, fic_name)
			source_html_path = os.path.join(source_folder, html_name)
			
			archive_fic_path = os.path.join(archive_folder, fic_name)
			archive_html_path = os.path.join(archive_folder, html_name)
			
			traitement_fic_path = os.path.join(traitement_folder, fic_name)
			traitement_html_path = os.path.join(traitement_folder, html_name)
			
			if enable_archive:
				shutil.copy(source_fic_path, archive_fic_path)
				shutil.copy(source_html_path, archive_html_path)
			
			shutil.copy(source_fic_path, traitement_fic_path)
			shutil.copy(source_html_path, traitement_html_path)
			
			os.remove(source_fic_path)
			os.remove(source_html_path)
			
			file_htmltomhtml.put(file)
			
			if int(nb_thread_source) == 0 :
				verif_continue = False
				break 
		except Exception as e:
			if file != "":
				log_event("1","DEBUG",f"{file} > Erreur {e}")
			if int(nb_thread_source) == 0 :
				verif_continue = False
				break 
			continue
	
def traitement_htmltomhtml(file_htmltomhtml,file_cible):
	verif_continue = True
	# Set Chrome options
	options = configure_chrome_options()
	# Set up the Chrome service and driver
	service = Service(chromedriver_path)
	driver = None
	
	while verif_continue:
		try:
			file = ""
			if file_htmltomhtml.qsize() == 0 and int(nb_thread_htmltomhtml) == 0 :
				verif_continue = False
				break 
				
			elif file_htmltomhtml.qsize() != 0 :
				driver = webdriver.Chrome(service=service, options=options)
				file = file_htmltomhtml.get()
				
				log_event("1","DEBUG",f"{file} > html to mhtml")
				
				fic_name = file
				
				html_name = fic_name.replace(fic_type, '.html')
				mhtml_name = fic_name.replace(fic_type, '.mhtml')
				traitement_fic_path = os.path.join(traitement_folder, fic_name)
				traitement_html_path = os.path.join(traitement_folder, html_name)
				traitement_mhtml_path = os.path.join(traitement_folder, mhtml_name)
				
				abs_in = os.path.abspath(traitement_html_path)
				abs_out = re.sub(r"(.*).html", r"\1.mhtml", abs_in, flags=re.IGNORECASE)
				
				file_url = 'file:///' + abs_in
				driver.get(file_url)
				
				WebDriverWait(driver, 10).until(
						lambda d: d.execute_script("return document.readyState") == "complete"
						)
				WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.TAG_NAME, "body"))
				)
				mhtml = driver.execute_cdp_cmd("Page.captureSnapshot", {"format": "mhtml"})
				with open(abs_out, "wb") as mhtml_file:
					mhtml_file.write(mhtml['data'].encode('utf-8'))
					
				file_cible.put(file)
				
				if int(nb_thread_htmltomhtml) == 0 :
					verif_continue = False
					if driver:
						driver.quit()
					break 
					
				elif file_htmltomhtml.qsize() == 0 :
					if driver:
						driver.quit()
						
			else : 
				continue
				
		except Exception as e:
			if file != "":
				log_event("1","DEBUG",f"{file} > Erreur {e}")
				file_cible.put(file)
				
			if driver:
				driver.quit()
				
			if int(nb_thread_htmltomhtml) == 0 :
				verif_continue = False
				if driver:
					driver.quit()
				break 
			continue
	if driver:
		driver.quit()
	
def deplacement_cible(file_cible):
	verif_continue = True
	while verif_continue:
		try :
			file = ""
			if file_cible.qsize() == 0 and int(nb_thread_cible) == 0 :
				verif_continue = False
				break  
			
			file = file_cible.get()
			log_event("1","DEBUG",f"{file} > deplacement vers cible")
			
			fic_name = file
			html_name = fic_name.replace(fic_type, '.html')
			mhtml_name = fic_name.replace(fic_type, '.mhtml')
			
			traitement_fic_path = os.path.join(traitement_folder, fic_name)
			traitement_html_path = os.path.join(traitement_folder, html_name)
			traitement_mhtml_path = os.path.join(traitement_folder, mhtml_name)
			
			cible_fic_path = os.path.join(cible_folder, fic_name)
			cible_mhtml_path = os.path.join(cible_folder, mhtml_name)
			
			source_fic_path = os.path.join(source_folder, fic_name)
			source_html_path = os.path.join(source_folder, html_name)
			
			if os.path.exists(traitement_mhtml_path) :
			
				shutil.copy(traitement_fic_path, cible_fic_path)
				shutil.copy(traitement_mhtml_path, cible_mhtml_path)
				
				os.remove(traitement_fic_path)
				os.remove(traitement_html_path)
				os.remove(traitement_mhtml_path)
			
			else : 
				
				shutil.copy(traitement_fic_path, source_fic_path)
				shutil.copy(traitement_html_path, source_html_path)
				
				os.remove(traitement_fic_path)
				os.remove(traitement_html_path)
				
				fichiers_traites.remove(file)
				
			if int(nb_thread_cible) == 0 :
				verif_continue = False
				break 
				
		except Exception as e:
			if file != "" :
				log_event("1","DEBUG",f"{file} > Erreur {e}")
			if int(nb_thread_cible) == 0 :
				verif_continue = False
				break 
			continue
def traitement_routine():
	
	# Liste pour stocker les threads
	threads = []
	global fichiers_traites
	fichiers_traites = set()
	
	thread_liste = 0
	thread_source = 0
	thread_htmltomhtml = 0
	thread_cible = 0
	
	thread_liste_nb = 0
	thread_source_nb = 0
	thread_htmltomhtml_nb = 0
	thread_cible_nb = 0
	
	file_source = Queue()
	file_htmltomhtml = Queue()
	file_cible = Queue()
	
	while True:
		
		# Vérifie si le nombre de threads actifs est inférieur à 5
		if thread_liste_nb < (int(nb_thread_liste)) :
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=liste_source, args=(file_source,))
			threads.append(thread)
			thread.start()
			thread_liste += 1
			thread_liste_nb += 1
			log_event("1","DEBUG",f"création du thread thread_liste_{thread_liste}")
		
		if thread_source < (int(nb_thread_source)) :
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=deplacement_source, args=(file_source,file_htmltomhtml))
			threads.append(thread)
			thread.start()
			thread_source += 1
			thread_source_nb += 1
			log_event("1","DEBUG",f"création du thread thread_source_{thread_source}")
		
		
		# Vérifie si le nombre de threads actifs est inférieur à 5
		if thread_htmltomhtml< (int(nb_thread_htmltomhtml)) :
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=traitement_htmltomhtml, args=(file_htmltomhtml,file_cible))
			threads.append(thread)
			thread.start()
			thread_htmltomhtml += 1
			thread_htmltomhtml_nb += 1
			log_event("1","DEBUG",f"création du thread thread_htmltomhtml_{thread_htmltomhtml}")
		
		if thread_cible < (int(nb_thread_cible)) :
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=deplacement_cible, args=(file_cible,))
			threads.append(thread)
			thread.start()
			thread_cible += 1
			thread_cible_nb += 1
			log_event("1","DEBUG",f"création du thread thread_cible_{thread_cible}")
		
		if (int(nb_thread_liste)) == 0 :
			log_event("1","DEBUG",f"lance liste_source")
			liste_source(file_source,)
			
		if (int(nb_thread_source)) == 0 :
			log_event("1","DEBUG",f"lance deplacement source")
			deplacement_source(file_source,file_htmltomhtml)
			
		if (int(nb_thread_htmltomhtml)) == 0 :
			log_event("1","DEBUG",f"lance traitement_htmltomhtml")
			traitement_htmltomhtml(file_htmltomhtml,file_cible)
			
		if (int(nb_thread_cible)) == 0 :
			
			log_event("1","DEBUG",f"lance deplacement_cible")
			deplacement_cible(file_cible)
			
	time.sleep(0)
	
if __name__ == "__main__":

	log_event("0","WARNING",f"Lancement de HTML2MHTML")
	
	log_event("1","DEBUG",f"> début du traitement")
	log_event("1","INFO",f"> chargement chrome driver")
	# set up default paths if not given on command line
	platform=sys.platform.lower()
	defaultchromedriver ={
				"linux": f"{chromedriver_path}",
				"aix": f"{chromedriver_path}",
				"cygwin" : f"{chromedriver_path}",
				"msys" : f"{chromedriver_path}",
				"win32": f"{chromedriver_path}",
				"win64": f"{chromedriver_path}"
				}.get(platform,None)
	log_event("1","INFO",f"> Fin chargement chrome driver")
	if defaultchromedriver is None:
		print(f"Error: No support for your system (sys.platform={sys.platform})")
		sys.exit(1)  # Exit the script with a non-zero status code
	
	parser = argparse.ArgumentParser(description="Convert HTML files to MHTML format.")
	parser.add_argument('--chromedriver', type=str, default=defaultchromedriver, help='Path to chromedriver')
	parser.add_argument('--threads', type=int, default=4, help='Number of threads to use')
	parser.add_argument('--disable-rzl')						 
	
	# Parse kwnown args 
	args, unknown = parser.parse_known_args()
	if unknown:
		args.files = unknown

	logging.debug(f"Chromedriver: {args.chromedriver}")
	logging.debug(f"Threads: {args.threads}")
	log_event("1","INFO",f"> lancement traitement_routine")
	traitement_routine()