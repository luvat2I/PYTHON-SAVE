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

# import de mes dev
import log_aff

traitement_type = "service"
#traitement_type = "exe"

# Lecture du fichier de configuration
config = configparser.ConfigParser()

service_name = "TEST"

try:
	config.read('config.ini')
	if not config.sections():  # Vérifie si le fichier ini est vide
		raise FileNotFoundError("Le fichier de configuration 'config.ini' est vide.")
except Exception as e:
	print(f"ERROR > Probleme de traitement du fichier 'config.ini': {e}")
	if traitement_type == "exe" : # secu pour l'exe et le service
		input("Appuyez sur une touche pour quitter...")
	sys.exit(1)  # ferme lapp

# création d'une source d'événements si elle n'existe pas pour le mode service
def create_event_source():
	
	# Vérifier si la source existe déjà
	# Nom de la source
	source_name = 'TEST'
	# Nom de l'application
	app_name = 'TEST'

	# Vérifier si la source existe déjà
	try:
		win32evtlogutil.ReportEvent(source_name, 1, eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE, strings=[app_name])
	except Exception as e:
		# Créer la source si elle n'existe pas
		win32api.RegCreateKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}')
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'EventMessageFile', win32con.REG_SZ, os.path.abspath(__file__))
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'TypesSupported', win32con.REG_DWORD, 7)
	
def main():
	
	if traitement_type == "service" :
		try:
			service_name = config['service']['service_name']
		except Exception as e:
			print(f"ERROR > L'option 'service_name' est manquante dans le fichier 'config.ini': {e}")
			sys.exit(1)  # ferme lapp
		
		# Configuration du logger
		logger_service = logging.getLogger(service_name)
		logger_service.setLevel(logging.INFO)
		# Handler pour écrire dans le journal des événements Windows
		handler = logging.handlers.NTEventLogHandler(service_name)
		logger_service.addHandler(handler)
		create_event_source()  # Créer la source d'événements
		logger_service.info(f"Le service {service_name} demarre.")
		while True:
			logger_service.info(f"Le service {service_name} fonctionne.")
			time.sleep(10)
		#logger_service.info(f"Le service {service_name} est terminé.")
		#sys.exit(1)  # ferme lapp
	
if __name__ == '__main__':
	main()
