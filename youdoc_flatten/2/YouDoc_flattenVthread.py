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

# import de mes dev
import log_aff

# Lire le fichier de configuration
config = configparser.ConfigParser()

try:
    config.read('config.ini')
    if not config.sections():  # Vérifie si le fichier ini est vide
        raise FileNotFoundError("Le fichier de configuration 'config.ini' est vide.")
except Exception as e:
    print(f"ERROR > Probleme de traitement du fichier 'config.ini': {e}")
    input("Appuyez sur une touche pour quitter...")
    exit(1)  # Quitte l'application avec un code d'erreur

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
start_directory = "D:\\HTML2MHTML\\application\\installation\\webdriver\\chromedriver-win64"  # Vous pouvez changer cela pour un autre répertoire si nécessaire
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


def save_pages_as_mhtml(file, chromedriver_path):
	# Set Chrome options
	options = configure_chrome_options()

	# Set up the Chrome service and driver
	service = Service(chromedriver_path)
	driver = webdriver.Chrome(service=service, options=options)

	# Cycle through all files on the same chrome driver.
	# The four threads each read first come, first served until the queue is empty then the thread quits
	
	abs_in = os.path.abspath(file)
	if not os.path.exists(abs_in):
		logging.error(f"Nonexistent file {abs_in}")

	abs_out = re.sub(r"(.*).html", r"\1.mhtml", abs_in, flags=re.IGNORECASE)
	if os.path.exists(abs_out):
		logging.warning(f"Output file exists. Skipping {abs_in} due to {abs_out}")

	try:
		if sys.platform == 'cygwin':
			file_url = 'file:///' + cygwin_to_windows(abs_in)
		else:
			file_url = 'file:///' + abs_in
		log_aff.log_info("INFO",f" > Opening {file_url} > FIN ")
		logging.info(f"Opening {file_url}")
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
		logging.info(f"MHTML saved to: {abs_out}")
		log_aff.log_info("INFO",f"> MHTML saved to: {abs_out} > FIN ")
	except Exception as e:
		logging.error(f"Error processing {abs_in}: {e}")

	# clean up 
	driver.quit()

	
def traitement_fichier(source_base):
	
	thread_name = threading.current_thread().name  # Récupère le nom du thread
	
	fic_name = source_base
	log_aff.log_info("INFO",f"[{thread_name}] > début du traitement de {source_base} > Debut ")
	html_name = fic_name.replace(fic_type, '.html')
	mhtml_name = fic_name.replace(fic_type, '.mhtml')

	source_fic_name = fic_name
	source_html_name = html_name
	source_fic_path = os.path.join(source_folder, source_fic_name)
	source_html_path = os.path.join(source_folder, source_html_name)

	traitement_fic_name = fic_name
	traitement_html_name = html_name
	traitement_mhtml_name = mhtml_name
	traitement_fic_path = os.path.join(traitement_folder, traitement_fic_name)
	traitement_html_path = os.path.join(traitement_folder, traitement_html_name)
	traitement_mhtml_path = os.path.join(traitement_folder, traitement_mhtml_name)

	cible_fic_name = fic_name
	cible_mhtml_name = mhtml_name
	cible_fic_path = os.path.join(cible_folder, cible_fic_name)
	cible_mhtml_path = os.path.join(cible_folder, cible_mhtml_name)
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > Copie de SOURCE à TEMP ")
	shutil.copy(source_fic_path, traitement_fic_path)
	shutil.copy(source_html_path, traitement_html_path)
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > Copie de SOURCE à TEMP > FIN ")
	# supprime les fichiers dans le dossier d'origine
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > Supprime de SOURCE ")
	os.remove(source_fic_path)
	os.remove(source_html_path)
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > Supprime de SOURCE > FIN ")
	
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > Transforme HTML en MHTML ")
	save_pages_as_mhtml(traitement_html_path, args.chromedriver)
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > Transforme HTML en MHTML > FIN ")
	
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > copie de TEMP à CIBLE ")

	shutil.copy(traitement_mhtml_path, cible_mhtml_path)
	shutil.copy(traitement_fic_path, cible_fic_path)
	
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > copie de TEMP à CIBLE > FIN ")
	
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > supprime de CIBLE ")
	
	os.remove(traitement_fic_path)
	os.remove(traitement_html_path)
	os.remove(traitement_mhtml_path)
	
	log_aff.log_info("INFO",f"[{thread_name}] > {source_base} > supprime de CIBLE > FIN ")
	
def traitement_routine():
	valide = True
	# Liste pour stocker les threads
	threads = []
	fichiers_traites = set()
	while True:
		for file in os.listdir(source_folder):
			if file.endswith(fic_type) and file not in fichiers_traites:
				
				source_fic_name = file
				current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				
				logging.debug(f"> lance le traitement du fichier {source_fic_name}")
				fichiers_traites.add(file)
				
				# Vérifie si le nombre de threads actifs est inférieur à 5
				if len(threads) < int(nb_threads):
					# Crée et démarre un nouveau thread pour le traitement du fichier
					thread = threading.Thread(target=traitement_fichier, args=(source_fic_name,))
					threads.append(thread)
					thread.start()
				else:
					# Attend que l'un des threads se termine avant de continuer
					for thread in threads:
						thread.join()
					threads.clear()  # Réinitialise la liste des threads
				
		for thread in threads:
			thread.join()
		
		# Réinitialise la liste des threads pour le prochain cycle
		threads.clear()
			
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