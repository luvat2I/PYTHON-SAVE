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

# Lire le fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Chemins des dossiers
source_folder = config['folders']['source_folder']                  # dossier source
traitement_folder = config['folders']['traitement_folder']          # dossier de conversion
cible_folder = config['folders']['cible_folder']                  # dossier cible

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


# Fonction pour surveiller l'entrée de l'utilisateur pour l'arret (ne pas toucher)
def wait_for_exit():
    global running
    while running:
        user_input = input(f"Tache de traitement des html a partir des {fic_type} , Appuyez sur 'Entree' pour arrêter le traitement du dossier...")
        if user_input == "":
            running = False


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

def save_pages_as_mhtml(queue, chromedriver_path):
    # Set Chrome options
    options = configure_chrome_options()

    # Set up the Chrome service and driver
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    # Cycle through all files on the same chrome driver.
    # The four threads each read first come, first served until the queue is empty then the thread quits
    while True:
        file = queue.get()
        if file is None:
            break
        if not file.endswith(".html"):
            logging.warning(f"Not a .html file: {file}")
            continue

        abs_in = os.path.abspath(file)
        if not os.path.exists(abs_in):
            logging.error(f"Nonexistent file {abs_in}")
            continue

        abs_out = re.sub(r"(.*).html", r"\1.mhtml", abs_in, flags=re.IGNORECASE)
        if os.path.exists(abs_out):
            logging.warning(f"Output file exists. Skipping {abs_in} due to {abs_out}")
            continue

        try:
            if sys.platform == 'cygwin':
                file_url = 'file:///' + cygwin_to_windows(abs_in)
            else:
                file_url = 'file:///' + abs_in

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

        except Exception as e:
            logging.error(f"Error processing {abs_in}: {e}")
    
    # clean up 
    driver.quit()

# Fonction principale pour surveiller le dossier
def surveiller_dossier():
    global running, is_processing
    fichiers_traites = set()

    # Démarrer le thread pour l'entrée de l'utilisateur
    exit_thread = threading.Thread(target=wait_for_exit)
    exit_thread.start()
    
    fileQ = Queue()
    
    while running:
        
        for file in os.listdir(source_folder):
            if file.endswith(fic_type) and file not in fichiers_traites:
                # debut du traitement
                is_processing = True
                
                fic_path = os.path.join(source_folder, file)
                html_path = os.path.join(source_folder, file.replace(fic_type, '.html'))
                
                fic_base = file.replace(fic_type, '.')
                if os.path.exists(html_path):
                    
                    #calcul des noms et des path
                    traitement_fic_name = file.replace(fic_type, '.sav.ixx')
                    traitement_html_name = file.replace(fic_type, '.sav.html')
                    traitement_mhtml_name = file.replace(fic_type, '.sav.mhtml')
                    traitement_fic_path = os.path.join(traitement_folder, traitement_fic_name)
                    traitement_html_path = os.path.join(traitement_folder, traitement_html_name)
                    traitement_mhtml_path = os.path.join(traitement_folder, traitement_mhtml_name)
                    
                    if enable_archive:
                        archive_fic_name = file.replace(fic_type, f'{fic_type}')
                        archive_html_name = file.replace(fic_type, '.html')
                        archive_fic_path = os.path.join(archive_folder, archive_fic_name)
                        archive_html_path = os.path.join(archive_folder, archive_html_name)
                    
                    export_fic_name = file.replace(fic_type, f'{fic_type}')
                    export_html_name = file.replace(fic_type, '.html')
                    export_fic_path = os.path.join(cible_folder, export_fic_name)
                    export_html_path = os.path.join(cible_folder, export_html_name)
                    
                    cible_fic_name = file.replace(fic_type, f'{fic_type}')
                    cible_mhtml_name = file.replace(fic_type, '.mhtml')
                    cible_fic_path = os.path.join(cible_folder, cible_fic_name)
                    cible_mhtml_path = os.path.join(cible_folder, cible_mhtml_name)
                    
                    # Copie les fichiers dans le dossier traitement
                    shutil.copy(fic_path, traitement_fic_path)
                    shutil.copy(html_path, traitement_html_path)
                    
                    if enable_archive:
                        # Copie les fichiers dans le dossier archive
                        shutil.copy(fic_path, archive_fic_path)
                        shutil.copy(html_path, archive_html_path)
                    
                    # supprime les fichiers dans le dossier d'origine
                    os.remove(fic_path)
                    os.remove(html_path)
                    
                    fileQ.put(traitement_html_path)

                    processes = []
                    for i in range(args.threads):
                        p = Process(target=save_pages_as_mhtml, args=(fileQ, args.chromedriver))
                        p.start()
                        processes.append(p)

                    # Add sentinel values to signal workers to exit - one per thread
                    for _ in range(args.threads):
                        fileQ.put(None)

                    # Wait for all processes to complete
                    for p in processes:
                        p.join()
                       
                    shutil.copy(traitement_fic_path, cible_fic_path)
                    shutil.copy(traitement_mhtml_path, cible_mhtml_path)
                    
                    # Supprimer les fichiers du traitement_folder après la copie
                    os.remove(traitement_fic_path)
                    os.remove(traitement_html_path)
                    os.remove(traitement_mhtml_path)
                    
                    fichiers_traites.add(file)
                else:
                    
                    matching_files = []
                    for filename2 in os.listdir(source_folder):
                        if filename2.startswith(fic_base):
                            matching_files.append(filename2)
                        
                    for filename2 in matching_files:
                        # Construire le chemin complet du fichier source
                        filename = os.path.join(source_folder, filename2)
                        # Construire le chemin complet du fichier de destination
                        destination_file = os.path.join(cible_folder, filename2)
                        
                        # Copier le fichier
                        shutil.copy(filename, destination_file)
                        
                        # Supprimer le fichier source après la copie
                        os.remove(filename)
                        
                # fin du traitement
                is_processing = False
                
        # Attendre x secondes avant de vérifier à nouveau
        time.sleep(2)

    exit_thread.join()  # Attendre que le thread d'entrée se termine

if __name__ == "__main__":
    
    
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
    #parser.add_argument('--verbosity', type=str, default='WARNING', help='Set the logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    #parser.add_argument('files', metavar='File', type=str, nargs='+', help='HTML files to convert')

    # Parse kwnown args 
    args, unknown = parser.parse_known_args()
    if unknown:
        args.files = unknown

    # Set up logging based on verbosity level
    #setup_logging(args.verbosity)

    logging.debug(f"Chromedriver: {args.chromedriver}")
    logging.debug(f"Threads: {args.threads}")
    #logging.debug(f"Verbosity: {args.verbosity}")
    #logging.debug(f"Files: {args.files}")

    surveiller_dossier()