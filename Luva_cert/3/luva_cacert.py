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
def creation_cacert_ini(filename_ini,DOSSIER_EXPORT_BASE,debug):
	error = False
	
	ID_APP = "CAC"
	
	if debug: print(f"filename_ini : {filename_ini}")
	if debug: print(f"DOSSIER_EXPORT_BASE : {DOSSIER_EXPORT_BASE}")
	
	# lecture du fichier INI
	if not error :
		try:
			config_cacerts = configparser.ConfigParser()
			config_cacerts.read(f'{filename_ini}')
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# lecture PFX_PASSWORD
	if not error :
		try:
			PFX_PASSWORD = config_cacerts['certif']['PFX_PASSWORD']
		except Exception as e:
			PFX_PASSWORD = ""
	
		# lecture DOSSIER_EXPORT
		
		try:
			DOSSIER_EXPORT = config_cacerts['param']['DOSSIER_EXPORT']
			if debug: print(f"DOSSIER_EXPORT : {DOSSIER_EXPORT}")
		except Exception as e:
			DOSSIER_EXPORT = DOSSIER_EXPORT_BASE
			if debug: print(f"erreur DOSSIER_EXPORT : {DOSSIER_EXPORT}")
		
		if debug : print(f"DOSSIER_EXPORT = {DOSSIER_EXPORT}")
		
		try:
			DOSSIER_CRT = config_cacerts['param']['DOSSIER_CRT']
		except Exception as e:
			DOSSIER_CRT = DOSSIER_EXPORT_BASE
		
		if debug : print(f"DOSSIER_CRT = {DOSSIER_CRT}")
	
	# --- Configuration
	if not error :
		try:
			jks_path_interne = Path(f"{DOSSIER_EXPORT}")
			bak = Path(f"{DOSSIER_EXPORT}\cacerts.temp")
			out_path = Path(f"{DOSSIER_EXPORT}\cacerts")
			jks_path = Path(f"{DOSSIER_EXPORT}\cacerts.base")
			jks_path_base = Path(f"{DOSSIER_EXPORT}cacerts.dev")
			cert_doss = Path(f"{DOSSIER_CRT}")
			
			jks_path_interne = rf"{DOSSIER_EXPORT}\\"
			password = PFX_PASSWORD
			
		except Exception as e:
			if debug: print(e)
			return {
				"code": ID_APP,
				"result": "",
				"error": "002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	### création du cacert base 
	if not error :
		try:
			# sauvegarde sûre
			target_folder = os.path.expanduser(jks_path_interne)  # modifier destination si besoin
			# chemin relatif dans votre bundle, par ex "data/config.yaml"
			copied = copy_resource_to(target_folder, os.path.join("cacertsbase", "cacerts.base"))
		except Exception as e:
			if not jks_path_base.exists():
				if debug: print(e)
			shutil.copy2(jks_path_base,jks_path)
		
	if not error :
		try:
			shutil.copy2(jks_path, bak)
		except Exception as e:
			if debug: print(e)
			return {
				"code": ID_APP,
				"result": "",
				"error": "003",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	if not error :
		try:
			jks_path.unlink()
			
		except Exception as e:
			if debug: print(e)
			return {
				"code": ID_APP,
				"result": "",
				"error": "004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	fic_type = "CRT"
	if not error :
		try:
			### lire tout les crt du dossier 
			for file in os.listdir(cert_doss):
				if file.endswith(fic_type.lower()) or file.endswith(fic_type):
					fic_name = file
					cert_path = Path(cert_doss) / f"{fic_name}"
					alias = fic_name.lower().replace(".crt", "")
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
		except Exception as e:
			if debug: print(e)
			return {
				"code": ID_APP,
				"result": "",
				"error": "005",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	if not error :
		try:	
			bak.unlink()
		except Exception as e:
			if debug: print(e)
			return {
				"code": ID_APP,
				"result": "",
				"error": "006",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	return {
			"code": ID_APP,
			"result": f"Fin du traitement sans erreur",
			"error": "",
			"message": f"Fin du traitement sans erreur",
			"message2": ""
		}