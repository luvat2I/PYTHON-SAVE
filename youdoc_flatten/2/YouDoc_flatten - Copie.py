import os
import shutil
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import configparser
import time
import logging
from datetime import datetime, timedelta  # Assurez-vous d'importer timedelta
import threading

# Lire le fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Chemins des dossiers
source_folder = config['folders']['source_folder']
traitement_folder = config['folders']['traitement_folder']
export_folder = config['folders']['export_folder']

# Créer les dossiers s'ils n'existent pas (sauf pour le dossier final)
os.makedirs(traitement_folder, exist_ok=True)
os.makedirs(source_folder, exist_ok=True)

# Gestion des archives
enable_archive = config.getboolean('archives', 'enable_archive')
archive_folder = config['archives']['archive_folder']
if enable_archive:
    os.makedirs(archive_folder, exist_ok=True)

# Type de fichier qui declenche l'applatissement pdf
fic_type = config['files']['fic_type']

# Créer le sous-dossier images dans traitement_folder (pour applatir les pdf)
images_folder = os.path.join(traitement_folder, 'images')
os.makedirs(images_folder, exist_ok=True)

# Gestion des logs 
enable_logging = config.getboolean('logging', 'enable_logging')
log_folder = config['logging']['log_folder']
if enable_logging:
    os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log

# Configure le log si activé (va enregistrer la liste des fichiers json ou ixx)
if enable_logging:
    log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
    logging.basicConfig(filename=log_filename, level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.disable(logging.CRITICAL)  # Désactiver le logging si non activé

# Variables pour contrôler l'exécution (ne pas toucher)
running = True
is_processing = False

# Fonction pour aplatir un PDF en créant une image pour chaque page (ne pas toucher)
def flatten_pdf(input_pdf_path, output_pdf_path):
    images = convert_from_path(input_pdf_path)
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    
    for i, image in enumerate(images):
        # Enregistrer l'image temporairement dans le sous-dossier images
        image_path = os.path.join(images_folder, f"temp_image_{i}.png")
        image.save(image_path)
        c.drawImage(image_path, 0, 0, width=letter[0], height=letter[1])
        c.showPage()
        # Supprimer l'image temporaire après utilisation
        os.remove(image_path)
    
    c.save()

# Fonction pour surveiller l'entrée de l'utilisateur pour l'arret (ne pas toucher)
def wait_for_exit():
    global running
    while running:
        user_input = input(f"Tache de traitement des PDF a partir des {fic_type} , Appuyez sur 'Entree' pour arrêter le traitement du dossier...")
        if user_input == "":
            running = False

# Fonction principale pour surveiller le dossier
def surveiller_dossier():
    global running, is_processing
    fichiers_traites = set()

    # Démarrer le thread pour l'entrée de l'utilisateur
    exit_thread = threading.Thread(target=wait_for_exit)
    exit_thread.start()

    while running:
        
        for filename in os.listdir(source_folder):
            if filename.endswith(fic_type) and filename not in fichiers_traites:
                is_processing = True
                
                fic_path = os.path.join(source_folder, filename)
                pdf_path = os.path.join(source_folder, filename.replace(fic_type, '.pdf'))
                fic_base = filename.replace(fic_type, '.')
                if os.path.exists(pdf_path):
                    #calcul des noms et des path
                    traitement_fic_name = filename.replace(fic_type, '.sav1')
                    traitement_pdf_name = filename.replace(fic_type, '.sav2')
                    traitement_fic_path = os.path.join(traitement_folder, traitement_fic_name)
                    traitement_pdf_path = os.path.join(traitement_folder, traitement_pdf_name)
                    if enable_archive:
                        archive_fic_name = filename.replace(fic_type, f'{fic_type}')
                        archive_pdf_name = filename.replace(fic_type, '.pdf')
                        archive_fic_path = os.path.join(archive_folder, archive_fic_name)
                        archive_pdf_path = os.path.join(archive_folder, archive_pdf_name)
                    
                    export_fic_name = filename.replace(fic_type, f'{fic_type}')
                    export_pdf_name = filename.replace(fic_type, '.pdf')
                    export_fic_path = os.path.join(export_folder, export_fic_name)
                    export_pdf_path = os.path.join(export_folder, export_pdf_name)
                    
                    # Copie les fichiers dans le dossier traitement
                    shutil.copy(fic_path, traitement_fic_path)
                    shutil.copy(pdf_path, traitement_pdf_path)
                    
                    if enable_archive:
                        # Copie les fichiers dans le dossier archive
                        shutil.copy(fic_path, archive_fic_path)
                        shutil.copy(pdf_path, archive_pdf_path)
                    
                    # supprime les fichiers dans le dossier d'origine
                    os.remove(fic_path)
                    os.remove(pdf_path)
                    
                    #applati le fichier
                    flatten_pdf(traitement_pdf_path, export_pdf_path)
                    shutil.copy(traitement_fic_path, export_fic_path)
                    
                    # Supprimer les fichiers du traitement_folder après la copie
                    os.remove(traitement_fic_path)
                    os.remove(traitement_pdf_path)

                    fichiers_traites.add(filename)
                    logging.info(f"{export_fic_name}")
                    logging.info(f"{export_pdf_name}")
                else:
                    
                    matching_files = []
                    for filename2 in os.listdir(source_folder):
                        if filename2.startswith(fic_base):
                            matching_files.append(filename2)
                        
                    for filename2 in matching_files:
                        # Construire le chemin complet du fichier source
                        source_file = os.path.join(source_folder, filename2)
                        # Construire le chemin complet du fichier de destination
                        destination_file = os.path.join(export_folder, filename2)
                        
                        # Copier le fichier
                        shutil.copy(source_file, destination_file)
                        logging.info(f"{filename2}")
                        
                        # Supprimer le fichier source après la copie
                        os.remove(source_file)
                        
                # Indiquer que le traitement est terminé    
                is_processing = False    

        # Attendre 10 secondes avant de vérifier à nouveau
        time.sleep(10)

    exit_thread.join()  # Attendre que le thread d'entrée se termine

if __name__ == "__main__":
    surveiller_dossier()