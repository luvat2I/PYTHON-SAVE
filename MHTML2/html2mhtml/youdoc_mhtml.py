import os
import sys
import re
import argparse
import shutil
import configparser
import time
import logging
from datetime import datetime, timedelta  # Assurez-vous d'importer timedelta
import threading
from multiprocessing import Process, Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import de mes dev
import log_aff

# Lire le fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

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

nb_threads = config['param']['nb_threads']

# Variables pour contrôler l'exécution (ne pas toucher)
running = True
is_processing = False

# Fonction de conversion des adresses cygwin en windows
def cygwin_to_windows(cyg_path):
	return cyg_path.replace("/cygdrive/c/", "C:\\").replace("/", "\\")

def find_chromedriver(start_dir):
	for root, dirs, files in os.walk(start_dir):
		if 'chromedriver.exe' in files:
			return os.path.join(root, 'chromedriver.exe')
	return None
	
# recherche du path chromedriver
start_directory = "C:\\"  # Vous pouvez changer cela pour un autre répertoire si nécessaire
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
	options.add_argument('--user-agent=Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)')
	return options


def liste_source(file_source):
	
	fichiers_traites = set()
	
	log_aff.log_info("INFO",f" > traitement liste_source ")
	while True:
		for file in os.listdir(source_folder):
		
			fic_name = file
			html_name = fic_name.replace(fic_type, '.html')
			fic_path = os.path.join(source_folder, file)
			html_path = os.path.join(source_folder, file.replace(fic_type, '.html'))
			
			if file.endswith(fic_type) and os.path.exists(html_path) and file not in fichiers_traites:
				source_fic_name = file
				log_aff.log_info("INFO",f" > {file} > ajout à la liste source ")
				fichiers_traites.add(file)
				file_source.put(file)
				log_aff.log_info("INFO",f" > {file} > ajout à la liste source > FIN ")
				
	log_aff.log_info("INFO",f" > traitement liste_source > FIN ")


def deplacement_source(file_source,file_htmltomhtml):
	log_aff.log_info("INFO",f" > traitement deplacement_source ")
	
	while True:
	
		try:
			file = file_source.get()
			log_aff.log_info("INFO",f" > {file} > deplacement dans {traitement_folder} ")
			
			fic_name = file
			html_name = fic_name.replace(fic_type, '.html')
			mhtml_name = fic_name.replace(fic_type, '.mhtml')
			
			source_fic_path = os.path.join(source_folder, fic_name)
			source_html_path = os.path.join(source_folder, html_name)
			
			traitement_fic_path = os.path.join(traitement_folder, fic_name)
			traitement_html_path = os.path.join(traitement_folder, html_name)
			
			shutil.copy(source_fic_path, traitement_fic_path)
			shutil.copy(source_html_path, traitement_html_path)
			os.remove(source_fic_path)
			os.remove(source_html_path)
			
			log_aff.log_info("INFO",f" > {file} > deplacement dans TEMP > FIN ")
			
			log_aff.log_info("INFO",f" > {file} > ajout à la liste source ")
			file_htmltomhtml.put(file)
			log_aff.log_info("INFO",f" > {file} > ajout à la liste source > FIN ")
		except file_source.Empty:
			continue
	log_aff.log_info("INFO",f" > traitement deplacement_source > Fin ")
	
def traitement_htmltomhtml(file_htmltomhtml,file_cible):
	
	log_aff.log_info("INFO",f" > traitement htmltomhtml ")
	
	 # Set Chrome options
	options = configure_chrome_options()

	# Set up the Chrome service and driver
	service = Service(chromedriver_path)
	driver = webdriver.Chrome(service=service, options=options)
	
	while True:
		
		
		file = file_htmltomhtml.get()
		if file is None:
			break
		log_aff.log_info("INFO",f" > {file} > transforme en HTML ")
		
		fic_name = file
		html_name = fic_name.replace(fic_type, '.html')
		mhtml_name = fic_name.replace(fic_type, '.mhtml')
		
		traitement_fic_path = os.path.join(traitement_folder, fic_name)
		traitement_html_path = os.path.join(traitement_folder, html_name)
		traitement_mhtml_path = os.path.join(traitement_folder, mhtml_name)
		
		abs_in = os.path.abspath(traitement_html_path)
		if not os.path.exists(abs_in):
			logging.error(f"Nonexistent file {abs_in}")
			continue
		
		abs_out = re.sub(r"(.*).html", r"\1.mhtml", abs_in, flags=re.IGNORECASE)
		if os.path.exists(abs_out):
			continue

		try:
			if sys.platform == 'cygwin':
				file_url = 'file:///' + cygwin_to_windows(abs_in)
			else:
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
				
		except Exception as e:
			logging.error(f"Error processing {abs_in}: {e}")
			
		log_aff.log_info("INFO",f" > {file} > transforme en HTML > FIN ")
		
		log_aff.log_info("INFO",f" > {file} > ajout à la liste cible ")
		file_cible.put(file)
		log_aff.log_info("INFO",f" > {file} > ajout à la liste cible > FIN ")
		
	driver.quit()	
	
	log_aff.log_info("INFO",f" > traitement htmltomhtml > Fin ")

	
def deplacement_cible(file_cible):
	
	log_aff.log_info("INFO",f" > traitement deplacement_cible ")
	while True:
		try :
			file = file_cible.get()
			log_aff.log_info("INFO",f" > {file} > deplace dans Cible ")
			
			fic_name = file
			html_name = fic_name.replace(fic_type, '.html')
			mhtml_name = fic_name.replace(fic_type, '.mhtml')
			
			traitement_fic_path = os.path.join(traitement_folder, fic_name)
			traitement_html_path = os.path.join(traitement_folder, html_name)
			traitement_mhtml_path = os.path.join(traitement_folder, mhtml_name)
			
			cible_fic_path = os.path.join(cible_folder, fic_name)
			cible_mhtml_path = os.path.join(cible_folder, mhtml_name)
			
			shutil.copy(traitement_fic_path, cible_fic_path)
			shutil.copy(traitement_mhtml_path, cible_mhtml_path)
			
			os.remove(traitement_fic_path)
			os.remove(traitement_html_path)
			os.remove(traitement_mhtml_path)
			
			log_aff.log_info("INFO",f" > {file} > deplace dans Cible > FIN ")
			
		except file_cible.Empty:
			continue

	log_aff.log_info("INFO",f" > traitement deplacement_cible > Fin ")

	
def traitement_routine():
	valide = True
	# Liste pour stocker les threads
	threads = []
	fichiers_traites = set()
	
	thread_liste = 0
	file_source = Queue()
	thread_source = 0
	file_htmltomhtml = Queue()
	thread_htmltomhtml = 0
	file_cible = Queue()
	thread_cible = 0
	
	while True:
		
		# Vérifie si le nombre de threads actifs est inférieur à 5
		if thread_liste == 0 :
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=liste_source, args=(file_source,))
			threads.append(thread)
			thread.start()
			thread_liste = 1
		
		if thread_source == 0 :
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=deplacement_source, args=(file_source,file_htmltomhtml))
			threads.append(thread)
			thread.start()
			thread_source = 1
			
		if thread_cible == 0 :
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=deplacement_cible, args=(file_cible,))
			threads.append(thread)
			thread.start()
			thread_cible = 1
		
		# Vérifie si le nombre de threads actifs est inférieur à 5
		if thread_htmltomhtml < int(nb_threads):
			# Crée et démarre un nouveau thread pour le traitement du fichier
			thread = threading.Thread(target=traitement_htmltomhtml, args=(file_htmltomhtml,file_cible))
			threads.append(thread)
			thread.start()
			thread_htmltomhtml += 1
		while threads:
			for thread in threads:
				if not thread.is_alive():
					print(f"Le thread {thread.name} a terminé son exécution.")
					threads.remove(thread)  # Retirer le thread de la liste
					thread_htmltomhtml -= 1
		
	time.sleep(0)
	
if __name__ == "__main__":
	
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	print(f"{current_time} > début du traitement")
	
	print(f" > chargement chrome driver")
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

	if defaultchromedriver is None:
		print(f"Error: No support for your system (sys.platform={sys.platform})")
		sys.exit(1)  # Exit the script with a non-zero status code
	
	parser = argparse.ArgumentParser(description="Convert HTML files to MHTML format.")
	parser.add_argument('--chromedriver', type=str, default=defaultchromedriver, help='Path to chromedriver')
	parser.add_argument('--threads', type=int, default=4, help='Number of threads to use')
	
	# Parse kwnown args 
	args, unknown = parser.parse_known_args()
	if unknown:
		args.files = unknown

	logging.debug(f"Chromedriver: {args.chromedriver}")
	logging.debug(f"Threads: {args.threads}")
	
	traitement_routine()