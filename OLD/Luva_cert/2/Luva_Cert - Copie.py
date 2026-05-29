import os
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import re
import time
import logging
import logging.handlers
import configparser
from datetime import datetime, timedelta, timezone
import win32evtlogutil
import win32evtlog
import win32api
import win32con
import argparse
import subprocess
import shutil
import sys
from pathlib import Path
import jks
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12, Encoding, PrivateFormat, NoEncryption, BestAvailableEncryption
from cryptography.hazmat.backends import default_backend

# Pour les erreurs dans les evenements
service_base = "Luva_cert"

# Pour le traitement des services (vérification du nom services dans le programme)

programme = os.path.splitext(os.path.basename(sys.argv[0]))[0]
path = Path(sys.executable).resolve() if getattr(__import__("sys"), "frozen", False) else Path(__file__).resolve()
exe_filename = f"{programme}.exe"
terme_service = "service"
contient_service = terme_service.lower() in exe_filename.lower()

if contient_service :
	traitement_type = "service"
else:
	traitement_type = "exe"

log_event_level = "ERROR"
log_folder_level = "ERROR"
log_console_level = "INFO"

time_sleep=0

log_levels = {
	"DEBUG": logging.DEBUG,
	"INFO": logging.INFO,
	"WARNING": logging.WARNING,
	"ERROR": logging.ERROR
}

### affiche les logs dans les Evenements windows ###
def log_service(level,log_text):
	if level == "DEBUG" and log_event_level == "DEBUG" :
		logger_service.debug(f"{log_text}")
	if level == "INFO" and (log_event_level == "DEBUG" or log_event_level == "INFO") :
		logger_service.info(f"{log_text}")
	elif level == "WARNING" and (log_event_level == "DEBUG" or log_event_level == "INFO" or log_event_level == "WARNING"):
		logger_service.warning(f"{log_text}")
	elif level == "ERROR" :
		logger_service.error(f"{log_text}")

### affiche les logs dans la console ###
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
	
### affiche les logs de façon securisé avant l'initialisations des paramètres (event et console) ###
def log_secure(type,level,log_text):
	if type == "0" :
		log_service(level,log_text)
	log_console(level,log_text)
	if traitement_type == "exe" and level == "ERROR" :
		input("Appuyez sur une touche pour quitter...")

### création d'une source d'événements si elle n'existe pas pour le mode service ###
def create_event_source(source_name):
	try:
		win32evtlogutil.ReportEvent(source_name, 1, eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE, strings=[source_name])
	except Exception as e:
		print("error")
		win32api.RegCreateKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}')
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'EventMessageFile', win32con.REG_SZ, os.path.abspath(__file__))
		win32api.RegSetValue(win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, f'SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application\\{source_name}'), 'TypesSupported', win32con.REG_DWORD, 7)

### enregistre les logs dans un fichier ###
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
		
### traitement des logs en fonction du type ###
### 2 > pour la console ###
### 1 > pour log dans un fichier et la console ###
### 0 > pour les event win, log dans un fichier et la console ###
def log_event(type,level,log_text):
	if type == "0" :
		if enable_logging :
			log_enreg(level,log_text)
		log_service(level,log_text)
		log_console(level,log_text)
	elif type == "1" :
		if enable_logging :
			log_enreg(level,log_text)
		log_console(level,log_text)
	elif type == "2" :
		log_console(level,log_text)

# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
		
### lecture du fichier INI et traitement de toutes les entrées ###
config = configparser.ConfigParser()
logger_service = logging.getLogger(service_base)
logger_service.setLevel(logging.WARNING)
event_handler = logging.handlers.NTEventLogHandler(service_base)
logger_service.addHandler(event_handler)
create_event_source(f"{service_base}")

### Recupéaration des du nom du programme ###
programme = os.path.splitext(os.path.basename(sys.argv[0]))[0]
path = Path(sys.executable).resolve() if getattr(__import__("sys"), "frozen", False) else Path(__file__).resolve()

ini_filename = f"{programme}.ini"

### Sécurisation du nom luva dans le nom du programme ###
terme = "luva"
contient_luva = terme.lower() in exe_filename.lower()

# Erreur si il n'y a pas LUVA
if not contient_luva:
	log_secure("0","ERROR",f"Probleme de nom de programme.")
	input()
	sys.exit(1)  # ferme lapp

### Sécurisation des variables de logs ###
try:
	
	if not os.path.exists(ini_filename):
		log_secure("0","INFO",f"Pas de fichier ini '{ini_filename}'")
		log_validation = False
	else :
		log_secure("0","INFO",f"Fichier ini '{ini_filename}' est présent")
		log_validation = True
		config.read(f'{ini_filename}')
		if not config.sections():  # Vérifie si le fichier ini est vide
			raise FileNotFoundError(f"Le fichier de configuration '{ini_filename}' est vide.")
except Exception as e:
	log_secure("0","ERROR",f"Probleme de traitement du fichier '{ini_filename}': {e}")
	sys.exit(1)  # ferme lapp

try:
	if log_validation :
		enable_logging = config.getboolean('logging', 'enable_logging')
	else :
		enable_logging = False
except Exception as e:
	enable_logging = False

if enable_logging :
	try:
		log_folder = config['logging']['log_folder']
	except Exception as e:
		log_secure("0","ERROR",f"L'option 'log_folder' est manquante dans le fichier 'config.ini': {e}")
		sys.exit(1)  # Quitte l'application avec un code d'erreur
	try:
		log_folder_level = config['logging']['log_folder_level']
	except Exception as e:
		log_folder_level = "ERROR"

try:
	if log_validation :
		log_console_level = config['logging']['log_console_level']
	else :
		log_console_level = "INFO"
except Exception as e:
	log_console_level = "INFO"

try:	
	if enable_logging:
		os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log
except Exception as e:
	log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}")
	sys.exit(1)  # Quitte l'application avec un code d'erreur

try:	
	# Configure le log si activé
	if enable_logging:
		log_level = log_levels.get(log_folder_level, logging.ERROR)
		log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
		logger_folder = logging.getLogger('folderloger')
		logger_folder.setLevel(log_level)
		file_handler = logging.FileHandler(log_filename)
		file_handler.setLevel(log_level)
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		file_handler.setFormatter(formatter)
		logger_folder.addHandler(file_handler)
	else:
		logging.disable(logging.CRITICAL)  # Désactiver le logging si non activé
except Exception as e:
	log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}")
	sys.exit(1)  # Quitte l'application avec un code d'erreur	

try:
	log_event_level = config['logging']['log_event_level']
	log_console("DEBUG",f"L'option 'log_event_level' est de niveau '{log_event_level}'")
except Exception as e:
	log_event_level = "ERROR"
verif = False

### Validation du type de processus via le nom de l'application ###
terme_creation = "creation"
contient_creation = terme_creation.lower() in exe_filename.lower()

terme_extraction = "extraction"
contient_extraction = terme_extraction.lower() in exe_filename.lower()

terme_keystore = "keystore"
contient_keystore = terme_keystore.lower() in exe_filename.lower()

terme_cacert = "cacerts"
contient_cacert = terme_cacert.lower() in exe_filename.lower()

terme_auto = "auto"
contient_auto = terme_auto.lower() in exe_filename.lower()

# permet de tester l'application en developpement
DEV = True
# DEV = False
# Permet de définir le périmètre de test

if DEV:
	PROCESSUS = "AUTO" # a desactivé pour le test

try:
	if not DEV:
		if not contient_creation and not contient_extraction and not contient_keystore and not contient_cacert and not contient_auto:
			log_secure("0","ERROR",f"Le nom du programme doit contenir 'creation' ou 'extraction'")
			sys.exit(1)  # Quitte l'application avec un code d'erreur	
	if contient_creation:
		PROCESSUS = "CREATION"
	if contient_extraction:
		PROCESSUS = "EXTRACTION"
	if contient_keystore:
		PROCESSUS = "KEYSTORE"
	if contient_cacert:
		PROCESSUS = "CACERTS"
	if contient_cacert:
		PROCESSUS = "AUTO"
except Exception as e:
	log_secure("0","ERROR",f"Le nom du programme doit contenir 'creation' ou 'extraction'")
	sys.exit(1)  # Quitte l'application avec un code d'erreur






If PROCESSUS != "AUTO" :
	# Recuperation du COMMON_NAME
	try:
		COMMON_NAME = config['certif']['COMMON_NAME']
	except Exception as e:
		if PROCESSUS == "CREATION":
			log_secure("0","ERROR",f"L'option 'COMMON_NAME' est manquante dans le fichier 'config.ini': {e}")
			sys.exit(1)  # Quitte l'application avec un code d'erreur
		else:
			COMMON_NAME = programme

	# Recuperation des info du certificat
	try:
		COUNTRY_NAME = config['certif']['COUNTRY_NAME']
	except Exception as e:
		COUNTRY_NAME = "FR"
	try:
		STATE_OR_PROVINCE_NAME = config['certif']['STATE_OR_PROVINCE_NAME']
	except Exception as e:
		STATE_OR_PROVINCE_NAME = "FRANCE"
	try:
		LOCALITY_NAME = config['certif']['LOCALITY_NAME']
	except Exception as e:
		LOCALITY_NAME = "DARDILLY"
	try:
		ORGANIZATION_NAME = config['certif']['ORGANIZATION_NAME']
	except Exception as e:
		ORGANIZATION_NAME = "LUVA"
	try:
		ORGANIZATIONAL_UNIT_NAME = config['certif']['ORGANIZATIONAL_UNIT_NAME']
	except Exception as e:
		ORGANIZATIONAL_UNIT_NAME = "LUVA"
	try:
		PFX_PASSWORD = config['certif']['PFX_PASSWORD']
		log_console("DEBUG",f"'PFX_PASSWORD' = '{PFX_PASSWORD}'")
	except Exception as e:
		PFX_PASSWORD = ""
	try:
		PFX_GEN = config.getboolean('certif', 'PFX_GEN')
	except Exception as e:
		PFX_GEN = False

	# Initialisation de certaines variables
	OUT_KEY = Path(f"{COMMON_NAME}.key")
	OUT_CSR = Path(f"{COMMON_NAME}.csr")
	OUT_CRT = Path(f"{COMMON_NAME}.crt")
	OUT_PFX = Path(f"{COMMON_NAME}.pfx")
	OUT_KEYSTORE = Path(f"localhost.keystore")
	OUT_CACERTS = Path(f"cacerts")

	try:
		NB_BITS = config['certif']['NB_BITS']
		log_console("DEBUG",f"'NB_BITS' = '{NB_BITS}'")
		KEY_BITS = int(NB_BITS)
	except Exception as e:
		if PROCESSUS == "CREATION":
			log_secure("0","ERROR",f"L'option 'NB_BITS' est manquante dans le fichier 'config.ini': {e}")
			sys.exit(1)  # Quitte l'application avec un code d'erreur

	try:
		JOURS = config['certif']['JOURS']
		log_console("DEBUG",f"'DAYS' = '{JOURS}'")
		DAYS = int(JOURS) 
	except Exception as e:
		if PROCESSUS == "CREATION":
			log_secure("0","ERROR",f"L'option 'JOURS' est manquante dans le fichier 'config.ini': {e}")
			sys.exit(1)  # Quitte l'application avec un code d'erreur

	if PROCESSUS == "EXTRACTION":
		try:
			pfx_path = Path(path).parent / f"{COMMON_NAME}.pfx"
			if not os.path.exists(pfx_path):
				raise FileNotFoundError(f"Le fichier '{pfx_path}' est absent.")
				sys.exit(1)  # Quitte l'application avec un code d'erreur
		except Exception as e:
			if PROCESSUS == "EXTRACTION":
				log_secure("0","ERROR",f"{e}")
				sys.exit(1)  # Quitte l'application avec un code d'erreur

log_level2 = log_levels.get(log_event_level, logging.ERROR)
logger_service.setLevel(log_level2)

# Traitement de la création
def traitementcreation():
	
	# Build subject
	name_attrs = []
	name_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, COUNTRY_NAME))
	name_attrs.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, STATE_OR_PROVINCE_NAME))
	name_attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, LOCALITY_NAME))
	name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORGANIZATION_NAME))
	name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ORGANIZATIONAL_UNIT_NAME))
	name_attrs.append(x509.NameAttribute(NameOID.COMMON_NAME, COMMON_NAME))
	subject = issuer = x509.Name(name_attrs)
	log_event("0","DEBUG",f"Recuperation des datas > OK.")
	# Generate key
	key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_BITS)
	with open(OUT_KEY, "wb") as f:
		f.write(key.private_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PrivateFormat.TraditionalOpenSSL,
			encryption_algorithm=serialization.NoEncryption()
		))
	log_event("0","INFO",f"Generation du fichier KEY > OK.")
	# Build SANs
	dns_raw = config.get('certif', 'DNS', fallback='')
	dns_list = [ip.strip() for ip in dns_raw.split(',') if ip.strip()]
	ip_raw = config.get('certif', 'IP', fallback='')
	ip_list = [ip.strip() for ip in ip_raw.split(',') if ip.strip()]
		
	san_list = []
	for v in dns_list:
		try:
			san_list.append(x509.DNSName(v))
		except Exception:
			# ignore invalid DNS names
			pass
	for v in ip_list:
		try:
			san_list.append(x509.DNSName(v))
		except Exception:
			# ignore invalid DNS names
			pass
	log_event("0","DEBUG",f"Recuperation des SAN > OK.")
	# Create CSR
	csr_builder = x509.CertificateSigningRequestBuilder().subject_name(subject)
	if san_list:
		csr_builder = csr_builder.add_extension(x509.SubjectAlternativeName(san_list), critical=False)
	csr = csr_builder.sign(key, hashes.SHA256())
	with open(OUT_CSR, "wb") as f:
		f.write(csr.public_bytes(serialization.Encoding.PEM))
	log_event("0","INFO",f"Creation du fichier CSR > OK.")
	
	# Self-sign certificate
	builder = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer)
	builder = builder.public_key(key.public_key())
	builder = builder.serial_number(x509.random_serial_number())
	builder = builder.not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
	builder = builder.not_valid_after(datetime.now(timezone.utc) + timedelta(days=DAYS))
	if san_list:
		builder = builder.add_extension(x509.SubjectAlternativeName(san_list), critical=False)
	builder = builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
	cert = builder.sign(private_key=key, algorithm=hashes.SHA256())
	with open(OUT_CRT, "wb") as f:
		f.write(cert.public_bytes(serialization.Encoding.PEM))
	log_event("0","INFO",f"Creation du fichier CRT > OK.")
	
	if PFX_GEN :
		pfx_bytes = None
		if PFX_PASSWORD == "":
			pfx_bytes = pkcs12.serialize_key_and_certificates(
				name=bytes(config['certif'].get('COMMON_NAME', ''), 'utf-8') or None,
				key=key,
				cert=cert,
				cas=None,
				encryption_algorithm=NoEncryption()
			)
		else:
			pfx_bytes = pkcs12.serialize_key_and_certificates(
				name=bytes(config['certif'].get('COMMON_NAME', ''), 'utf-8') or None,
				key=key,
				cert=cert,
				cas=None,
				encryption_algorithm=BestAvailableEncryption(PFX_PASSWORD.encode())
			)

		with open(OUT_PFX, "wb") as f:
			f.write(pfx_bytes)
		log_event("0","INFO",f"Creation du fichier PFX > OK.")

# Traitement de l'extraction
def traitementextraction(exe_filename):

	pfx_path = OUT_PFX
	pfx_password = PFX_PASSWORD.encode()
	
	with open(pfx_path, "rb") as f:
		pfx_data = f.read()

	# Charger le pfx
	private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(pfx_data, pfx_password)

	if certificate is None:
		raise SystemExit("Aucun certificat trouvé dans le PFX.")

	# Exporter le certificat en PEM
	crt_pem = certificate.public_bytes(Encoding.PEM)
	with open(OUT_CRT, "wb") as f:
		f.write(crt_pem)
	log_event("0","INFO",f"Extraction du fichier CRT > OK.")
	# Exporter la clé privée en PEM (non chiffrée) — pour clé chiffrée, utiliser BestAvailableEncryption(b"pass")
	key_pem = private_key.private_bytes(
		Encoding.PEM,
		PrivateFormat.TraditionalOpenSSL,
		NoEncryption()
	)
	with open(OUT_KEY, "wb") as f:
		f.write(key_pem)
	log_event("0","INFO",f"Extraction du fichier KEY > OK.")

def resource_path(relative_path):
	
	base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
	return os.path.join(base_path, relative_path)

def copy_resource_to(target_dir, relative_resource_path, target_name=None):
	
	src = resource_path(relative_resource_path)
	if not os.path.exists(src):
		raise FileNotFoundError(f"Source introuvable: {src}")
	os.makedirs(target_dir, exist_ok=True)
	dst = os.path.join(target_dir, target_name or os.path.basename(relative_resource_path))
	shutil.copy2(src, dst)  # conserve métadonnées
	return dst
	
# Traitement de cacerts
def traitementcacerts(exe_filename):
	
	# --- Configuration
	jks_path_interne = Path(path).parent / f"cacert"
	jks_path = Path(path).parent / f"cacert" / f"cacerts.base"
	bak = Path(path).parent / f"cacert" / f"cacerts.temp"
	out_path = Path(path).parent / f"cacert" / f"cacerts"
	password = PFX_PASSWORD
	if DEV:
		if not jks_path.exists():
			log_secure("0","ERROR",f"Keystore de base introuvable: {jks_path}")
			sys.exit(1)
	
	if not DEV:
		# sauvegarde sûre
		target_folder = os.path.expanduser(jks_path_interne)  # modifier destination si besoin
		# chemin relatif dans votre bundle, par ex "data/config.yaml"
		copied = copy_resource_to(target_folder, os.path.join("cacertsbase", "cacerts.base"))
		
	shutil.copy2(jks_path, bak)
	if not DEV:
		jks_path.unlink()
	
	fic_type = "CRT"
	### lire tout les crt du dossier 
	cert_doss = Path(path).parent / f"cacert"
	for file in os.listdir(cert_doss):
		if file.endswith(fic_type.lower()) or file.endswith(fic_type):
			fic_name = file
			print(fic_name)
			cert_path = Path(path).parent / f"cacert" / f"{fic_name}"
			print(cert_path)
			alias = fic_name.lower().replace(".crt", "")
			print(alias)
			ks = jks.KeyStore.load(str(bak), password)
	
			with cert_path.open("rb") as f:
				pem = f.read()
			cert = x509.load_pem_x509_certificate(pem)
			cert_der = cert.public_bytes(encoding=serialization.Encoding.DER)
			entries = dict(ks.entries)
			entries[alias] = jks.TrustedCertEntry.new(alias, cert_der)
			new_ks = jks.KeyStore(ks.store_type, entries)
			with open(bak, "wb") as f:
				new_ks.save(str(bak), password)
			shutil.copy2(bak, out_path)
	
	bak.unlink()
	
	print("Fini — sauvegarde:", out_path)
	log_event("0","INFO",f"Creation du fichier cacerts > OK.")
	
# Traitement de keystore
def traitementkeystore(exe_filename):
	log_event("0","INFO",f"Creation du fichier localhost.keystore > OK.")
	
# Main
if __name__ == "__main__":
	
	log_event("0","INFO",f"Debut du traitement")
	if PROCESSUS == "CREATION":
		traitementcreation(exe_filename)
	
	if PROCESSUS == "EXTRACTION":
		traitementextraction(exe_filename)
		
	if PROCESSUS == "CACERTS":
		traitementcacerts(exe_filename)
		
	if PROCESSUS == "KEYSTORE":
		traitementkeystore(exe_filename)
		
	if PROCESSUS == "AUTO":
		traitement_dossier = Path(path).parent
		fintype_ini = "INI"
		for file in os.listdir(traitement_dossier):
			if file.endswith(fintype_ini.lower()) or file.endswith(fintype_ini):
				
	
	log_event("0","INFO",f"Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()