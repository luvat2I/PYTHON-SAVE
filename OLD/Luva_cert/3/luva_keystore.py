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
def creation_keystore(filename_ini,COMMON_NAME_BASE,PEM_PATH_BASE,DOSSIER_EXPORT_BASE,debug):
	error = False
	ID_APP = "KEYSTORE"
	
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
	
	if not error :
		try:
			
			KEYSTORE_PASSWORD = config_extraction['certif']['KEYSTORE_PASSWORD']
			
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
			DOSSIER_EXPORT = config_extraction['param']['DOSSIER_EXPORT']
			if debug: print(f"DOSSIER_EXPORT : {DOSSIER_EXPORT}")
		except Exception as e:
			DOSSIER_EXPORT = DOSSIER_EXPORT_BASE
			if debug: print(f"erreur DOSSIER_EXPORT : {DOSSIER_EXPORT}")
		
		if debug : print(f"DOSSIER_EXPORT = {DOSSIER_EXPORT}")
	
	COMMON_NAME = COMMON_NAME_BASE
	
	if debug : print(f"COMMON_NAME = {COMMON_NAME}")
	
	PEM_PATH = r"D:\PYTHON\Luva_cert\3\CERTIFICAT.crt"
	
	data = Path(PEM_PATH).read_bytes()
    certs = []
    for cert in x509.load_pem_x509_certificates(data, default_backend()):
        certs.append(cert)
    if not certs:
        #raise ValueError("Aucun certificat trouvé dans " + PEM_PATH)
		print("Aucun certificat trouvé dans " + PEM_PATH)
	