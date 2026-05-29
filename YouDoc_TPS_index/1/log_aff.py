import logging
from datetime import datetime

def log_info(level,log_text,enable_print):
	# Obtenir l'heure actuelle
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	# Créer le message de log
	logtext = f"{current_time} > {level} > {log_text}"
	
	if enable_print:
		# Afficher le message dans la console
		print(f"{logtext}")
		
	# Enregistrer le message dans le log
	if level == "INFO" :
		logging.info(f"{log_text}")
	elif level == "WARNING" :
		logging.warning(f"{log_text}")
	elif level == "ERROR" :
		logging.error(f"{log_text}")
		

def log_enreg(log_text):
	print(f"{log_text}")
	logging.info(f"{log_text}")
	

def log_base(level,log_text):
	# Calcul de l'heure actuelle
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	# Crée le message de log
	logtext = f"{current_time} > {level} > {log_text}"
	
	# Affiche le message dans la console
	print(f"{logtext}")
	
	# Enregistre le message dans le log
	if level == "INFO" :
		logging.info(f"{log_text}")
	elif level == "WARNING" :
		logging.warning(f"{log_text}")
	elif level == "ERROR" :
		logging.error(f"{log_text}")