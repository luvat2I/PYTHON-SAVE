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

# Traitement de l'extraction
def extraction_pfx_ini(filename_ini,COMMON_NAME_BASE,DOSSIER_EXPORT_BASE,debug):
	error = False
	ID_APP = "PFX"
	
	
	
	if debug: print(f"filename_ini : {filename_ini}")
	if debug: print(f"DOSSIER_EXPORT_BASE : {DOSSIER_EXPORT_BASE}")
	
	# lecture du fichier INI
	if not error :
		try:
			config_extraction = configparser.ConfigParser()
			config_extraction.read(f'{filename_ini}')
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	
	try:
		PFX_PASSWORD = config_extraction['certif']['PFX_PASSWORD']
	except Exception as e:
		PFX_PASSWORD = ""
		
	if not error :
		try:
			DOSSIER_EXPORT = config_extraction['param']['DOSSIER_EXPORT']
			if debug: print(f"DOSSIER_EXPORT : {DOSSIER_EXPORT}")
		except Exception as e:
			DOSSIER_EXPORT = DOSSIER_EXPORT_BASE
			if debug: print(f"erreur DOSSIER_EXPORT : {DOSSIER_EXPORT}")
		
		if debug : print(f"DOSSIER_EXPORT = {DOSSIER_EXPORT}")
	
	if not error :
		try:
			COMMON_NAME = config_extraction['certif']['COMMON_NAME']
			if debug: print(f"COMMON_NAME : {COMMON_NAME}")
		except Exception as e:
			COMMON_NAME = COMMON_NAME_BASE
			if debug: print(f"erreur COMMON_NAME : {COMMON_NAME}")
		
		if debug : print(f"COMMON_NAME = {COMMON_NAME}")
	
	if not error :
		try:
	
			OUT_KEY = f"{DOSSIER_EXPORT}\{COMMON_NAME}.key"
			OUT_CRT = f"{DOSSIER_EXPORT}\{COMMON_NAME}.crt"
			
			OUT_PFX = filename_ini.replace(".INI", ".pfx")
			OUT_PFX = OUT_PFX.replace(".ini", ".pfx")
		
			
			if debug : print(f"OUT_KEY = {OUT_KEY}")
			if debug : print(f"OUT_CRT = {OUT_CRT}")
			if debug : print(f"OUT_PFX = {OUT_PFX}")
			
			pfx_path = OUT_PFX
			pfx_password = PFX_PASSWORD.encode()
			
			if debug : print(f"pfx_path = {pfx_path}")
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	
	if not error :
		try:
			with open(pfx_path, "rb") as f:
				pfx_data = f.read()
			
		except Exception as e:
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
			with open(pfx_path, "rb") as f:
				pfx_data = f.read()
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	if not error :
		try:
			private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(pfx_data, pfx_password)
		except Exception as e:
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
			if certificate is None:
				raise SystemExit("Aucun certificat trouvé dans le PFX.")
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "006",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	if not error :
		try:
			crt_pem = certificate.public_bytes(Encoding.PEM)
			with open(OUT_CRT, "wb") as f:
				f.write(crt_pem)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "007",
				"message": f"{e}",
				"message2": ""
			}
			error = True

	if not error :
		try:
			# Exporter la clé privée en PEM (non chiffrée) — pour clé chiffrée, utiliser BestAvailableEncryption(b"pass")
			key_pem = private_key.private_bytes(
				Encoding.PEM,
				PrivateFormat.TraditionalOpenSSL,
				NoEncryption()
			)
			with open(OUT_KEY, "wb") as f:
				f.write(key_pem)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "008",
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