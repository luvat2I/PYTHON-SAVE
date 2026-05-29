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


# Lecture du fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Récupération de la configuration des log et du print (du fichier ini) 
enable_logging = config.getboolean('logging', 'enable_logging')
log_folder = config['logging']['log_folder']
enable_print = config.getboolean('logging', 'enable_print')

# Récupération des informations des connexion BDD (du fichier ini)
sgbd_db_type = config['SGBD']['db_type']
sgbd_server = config['SGBD']['db_server']
sgbd_port = config['SGBD']['db_port']
sgbd_username = config['SGBD']['db_username']
sgbd_password = config['SGBD']['db_password']
sgbd_database = config['SGBD']['db_database']

# Récupération des informations des connexion SOLR (du fichier ini)
solr_server = config['SOLR']['solr_server']
solr_port = config['SOLR']['solr_port']
solr_username = config['SOLR']['solr_username']
solr_password = config['SOLR']['solr_password']
solr_tenant = config['SOLR']['solr_tenant']

# Récupération des informations de paramétrage des traitements (du fichier ini)
traitement_lot = config['traitement']['traitement_lot']

bdd_folders = config.getboolean('traitement', 'bdd_folders')
bdd_folders_doc = config.getboolean('traitement', 'bdd_folders_doc')
solr_folders = config.getboolean('traitement', 'solr_folders')

bdd_documents = config.getboolean('traitement', 'bdd_documents')
solr_documents = config.getboolean('traitement', 'solr_documents')

enable_date = config['traitement']['enable_date']
date_debut = config['traitement']['date_debut']
date_fin = config['traitement']['date_fin']


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


# Fonction principale pour surveiller le dossier
def lance_traitement():
	logging.info("#########################")
	logging.info("debut du traitement")
	if enable_print:
		print("début du traitement")
		print(f"SGBD {sgbd_db_type} sur le serveur {sgbd_server} port {sgbd_port} user {sgbd_username} pass {sgbd_password} base {sgbd_database}")
		print(f"SOLR sur le serveur {solr_server} port {solr_port} user {solr_username} pass {solr_password} tenant {solr_tenant}")
		print(f"le traitement sera effectue sur des les de {traitement_lot}")
		print(f"traitement folder : {bdd_folders} > {solr_folders}")
		print(f"traitement document : {bdd_documents} > {solr_documents}")
		print(f"traitement date : {enable_date} pour {date_debut} > {date_fin} ")
	logging.info(f"SGBD {sgbd_db_type} sur le serveur {sgbd_server} port {sgbd_port} user {sgbd_username} pass {sgbd_password} base {sgbd_database}")
	logging.info(f"SOLR sur le serveur {solr_server} port {solr_port} user {solr_username} pass {solr_password} tenant {solr_tenant}")
	logging.info(f"le traitement sera effectue sur des les de {traitement_lot}")
	logging.info(f"traitement folder : {bdd_folders} > {solr_folders}")
	logging.info(f"traitement document : {bdd_documents} > {solr_documents}")
	logging.info(f"traitement date : {enable_date} pour {date_debut} > {date_fin} ")
	
	if bdd_folders:
		if enable_print:
			print("> debut > controle des dossiers bdd")
			print("> connexion bdd")
			print("> creation table CO_IN_DOSS si elle n'existe pas")
			if enable_date:
				print("> creation de toutes les entrées CO_IN_DOSS qui ne sont pas présent et qui ont une date entre {date_debut} et {date_fin} avec la date de modif")
				if bdd_folders_doc:
					print("> pour tous les documents modifié entre {date_debut} et {date_fin} mettre à jour les entrées dossiers de CO_IN_DOSS")
			else:
				print("> creation de toutes les entrées CO_IN_DOSS qui ne sont pas présent dans la table")
				if bdd_folders_doc:
					print("> pour tous les documents modifié mettre à jour les entrées dossiers de CO_IN_DOSS")
	if solr_folders:
		if enable_print:
			print("> debut > controle des dossiers solr")
			print("> pour toutes les entrees CO_IN_DOSS vide ou a M verifier solr")
			print("> pas de retour solr > N")
			print("> retour solr avec time < date de CO_IN_DOSS alors R ")
			print("> sinon I")


if __name__ == "__main__":
	lance_traitement()