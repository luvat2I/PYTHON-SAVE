import os
import shutil
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
import win32evtlogutil
import win32evtlog
import win32api
import win32con

print(f"INFO > Debut de validation du fichier 'config.ini'")

# Lecture du fichier de configuration
config = configparser.ConfigParser()
try:
	config.read('config.ini')
	if not config.sections():  # Vérifie si le fichier ini est vide
		raise FileNotFoundError("Le fichier de configuration 'config.ini' est vide.")
except Exception as e:
	print(f"ERROR > Probleme de traitement du fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp


print(f"INFO > Validation de la partie '[LOGGING]'")

try:
	enable_logging = config.getboolean('logging', 'enable_logging')
	print(f"INFO > enable_logging : {enable_logging}")
except Exception as e:
	print(f"ERROR > L'option 'enable_logging' est manquante dans le fichier 'config.ini'")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:
	if enable_logging :
		log_folder = config['logging']['log_folder']
	print(f"INFO > log_folder : {log_folder}")
except Exception as e:
	print(f"ERROR > L'option 'log_folder' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:	
	if enable_logging:
		os.makedirs(log_folder, exist_ok=True)
except Exception as e:
	print(f"ERROR > creation du dossier {log_folder} impossible : {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:
	log_event_level = config['logging']['log_event_level']
	print(f"INFO > log_event_level : {log_event_level}")
except Exception as e:
	print(f"ERROR > L'option 'log_event_level' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:
	log_folder_level = config['logging']['log_folder_level']
	print(f"INFO > log_folder_level : {log_folder_level}")
except Exception as e:
	print(f"ERROR > L'option 'log_folder_level' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:
	log_console_level = config['logging']['log_console_level']
	print(f"INFO > log_console_level : {log_console_level}")
except Exception as e:
	print(f"ERROR > L'option 'log_console_level' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
print(f"INFO > Validation de la partie '[FOLDERS]'")

try:
	source_folder = config['folders']['source_folder']
	print(f"INFO > source_folder : {source_folder}")
except Exception as e:
	print(f"ERROR > L'option 'source_folder' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:
	traitement_folder = config['folders']['traitement_folder']
	print(f"INFO > traitement_folder : {traitement_folder}")
except Exception as e:
	print(f"ERROR > L'option 'traitement_folder' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:
	cible_folder = config['folders']['cible_folder']
	print(f"INFO > cible_folder : {cible_folder}")
except Exception as e:
	print(f"ERROR > L'option 'cible_folder' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:	
	os.makedirs(source_folder, exist_ok=True)
except Exception as e:
	print(f"ERROR > creation du dossier {source_folder} impossible : {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:	
	os.makedirs(traitement_folder, exist_ok=True)
except Exception as e:
	print(f"ERROR > creation du dossier {traitement_folder} impossible : {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:	
	os.makedirs(cible_folder, exist_ok=True)
except Exception as e:
	print(f"ERROR > creation du dossier {cible_folder} impossible : {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

print(f"INFO > Validation de la partie '[archives]'")
	
try:
	enable_archive = config.getboolean('archives', 'enable_archive')
	print(f"INFO > enable_archive : {enable_archive}")
except Exception as e:
	print(f"ERROR > L'option 'enable_archive' est manquante dans le fichier 'config.ini'")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:
	if enable_archive :
		archive_folder = config['archives']['archive_folder']
		print(f"INFO > archive_folder : {archive_folder}")
except Exception as e:
	print(f"ERROR > L'option 'archive_folder' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:
	if enable_archive :
		os.makedirs(archive_folder, exist_ok=True)
except Exception as e:
	print(f"ERROR > creation du dossier {archive_folder} impossible : {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

print(f"INFO > Validation de la partie '[files]'")
	
try:
	fic_type = config['files']['fic_type']
	print(f"INFO > fic_type : {fic_type}")
except Exception as e:
	print(f"ERROR > L'option 'fic_type' est manquante dans le fichier 'config.ini'")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp

try:
	enable_other_type = config.getboolean('files', 'enable_other_type')
	print(f"INFO > enable_other_type : {enable_other_type}")
except Exception as e:
	print(f"ERROR > L'option 'enable_other_type' est manquante dans le fichier 'config.ini'")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp	

print(f"INFO > Validation de la partie '[config]'")

try:
	if enable_archive :
		poppler_folder = config['config']['poppler_folder']
		print(f"INFO > poppler_folder : {poppler_folder}")
except Exception as e:
	print(f"ERROR > L'option 'poppler_folder' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:
	enable_threading = config.getboolean('config', 'enable_threading')
	print(f"INFO > enable_threading : {enable_threading}")
except Exception as e:
	print(f"ERROR > L'option 'enable_threading' est manquante dans le fichier 'config.ini'")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp	
	
try:
	nb_thread_source = config['config']['nb_thread_source']
	print(f"INFO > nb_thread_source : {nb_thread_source}")
except Exception as e:
	print(f"ERROR > L'option 'nb_thread_source' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:
	nb_thread_traitement = config['config']['nb_thread_traitement']
	print(f"INFO > nb_thread_traitement : {nb_thread_traitement}")
except Exception as e:
	print(f"ERROR > L'option 'nb_thread_traitement' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:
	nb_thread_flatten = config['config']['nb_thread_flatten']
	print(f"INFO > nb_thread_flatten : {nb_thread_flatten}")
except Exception as e:
	print(f"ERROR > L'option 'nb_thread_flatten' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
try:
	nb_thread_cible = config['config']['nb_thread_cible']
	print(f"INFO > nb_thread_cible : {nb_thread_cible}")
except Exception as e:
	print(f"ERROR > L'option 'nb_thread_cible' est manquante dans le fichier 'config.ini': {e}")
	print(f"ERROR > Retour APP : {e}")
	input("Appuyez sur une touche pour quitter...")
	exit(1)  # ferme lapp
	
def main():
	print(f"INFO > Fin du traitement de vérification")
	input("Appuyez sur une touche pour quitter...")
	
if __name__ == '__main__':
	main()
