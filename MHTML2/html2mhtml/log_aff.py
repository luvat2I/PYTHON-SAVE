
from datetime import datetime

def log_info(level,log_text):
	# Obtenir l'heure actuelle
	current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	print(f"{current_time} > {log_text}")
