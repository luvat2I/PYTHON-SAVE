# Exemple de fichier ini pour la création d'un CRT
# [logging]
# log_console_level=DEBUG

# [param]
# PROCESSUS=CREATION
# DOSSIER_EXPORT=D:\PYTHON\Luva_cert\TEST\CREATION\

# [certif]
# COMMON_NAME=TEST
# NB_BITS=2048
# JOURS=365
# DNS=TEST1,TEST2,TEST3,localhost
# IP=000.000.000.000
# PFX_GEN=TRUE
# PFX_PASSWORD=changeit



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

# Traitement de la création
def creation_crt_ini(filename_ini,DOSSIER_EXPORT_BASE,debug):
	error = False
	ID_APP = "CRT"
	
	# lecture du fichier INI
	if not error :
		try:
			config_creation = configparser.ConfigParser()
			config_creation.read(f'{filename_ini}')
		except Exception as e:
			if debug: print(e)
			return {
				"code": ID_APP,
				"result": "",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	if debug: print(filename_ini)
	# Recuperation du COMMON_NAME
	if not error :
		try:
			COMMON_NAME = config_creation['certif']['COMMON_NAME']
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
	
	# Recuperation du COMMON_NAME
	if not error :
		try:
			COMMON_NAME = config_creation['certif']['COMMON_NAME']
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "003",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	# Recuperation des info du certificat
	if not error :
		try:
			COUNTRY_NAME = config_creation['certif']['COUNTRY_NAME']
		except Exception as e:
			COUNTRY_NAME = "FR"
		try:
			STATE_OR_PROVINCE_NAME = config_creation['certif']['STATE_OR_PROVINCE_NAME']
		except Exception as e:
			STATE_OR_PROVINCE_NAME = "FRANCE"
		try:
			LOCALITY_NAME = config_creation['certif']['LOCALITY_NAME']
		except Exception as e:
			LOCALITY_NAME = "DARDILLY"
		try:
			ORGANIZATION_NAME = config_creation['certif']['ORGANIZATION_NAME']
		except Exception as e:
			ORGANIZATION_NAME = "LUVA"
		try:
			ORGANIZATIONAL_UNIT_NAME = config_creation['certif']['ORGANIZATIONAL_UNIT_NAME']
		except Exception as e:
			ORGANIZATIONAL_UNIT_NAME = "LUVA"
		try:
			PFX_PASSWORD = config_creation['certif']['PFX_PASSWORD']
		except Exception as e:
			PFX_PASSWORD = ""
		try:
			PFX_GEN = config_creation.getboolean('certif', 'PFX_GEN')
		except Exception as e:
			PFX_GEN = False
	
	
	# Recuperation du DOSSIER_EXPORT
	if not error :
		try:
			DOSSIER_EXPORT = config_creation['param']['DOSSIER_EXPORT']
		except Exception as e:
			DOSSIER_EXPORT = DOSSIER_EXPORT_BASE
	
	# Initialisation de certaines variables
	if not error :
		try:
			OUT_KEY = Path(f"{DOSSIER_EXPORT}\{COMMON_NAME}.key")
			OUT_CSR = Path(f"{DOSSIER_EXPORT}\{COMMON_NAME}.csr")
			OUT_CRT = Path(f"{DOSSIER_EXPORT}\{COMMON_NAME}.crt")
			OUT_PFX = Path(f"{DOSSIER_EXPORT}\{COMMON_NAME}.pfx")
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# recupération NB_BITS
	if not error :
		try:
			NB_BITS = config_creation['certif']['NB_BITS']
		except Exception as e:
			NB_BITS = "2048"
	
	# recupération KEY_BITS
	if not error :
		try:
			KEY_BITS = int(NB_BITS)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "005",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# recupération JOURS
	if not error :
		try:
			JOURS = config_creation['certif']['JOURS']
		except Exception as e:
			JOURS = "365"
	
	# recupération DAYS
	if not error :
		try:
			DAYS = int(JOURS) 
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "006",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# Build subject
	if not error :
		try:
			name_attrs = []
			name_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, COUNTRY_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, STATE_OR_PROVINCE_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, LOCALITY_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORGANIZATION_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ORGANIZATIONAL_UNIT_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.COMMON_NAME, COMMON_NAME))
			subject = issuer = x509.Name(name_attrs)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "007",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# Création du subject
	if not error :
		try:
			name_attrs = []
			name_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, COUNTRY_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, STATE_OR_PROVINCE_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, LOCALITY_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORGANIZATION_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ORGANIZATIONAL_UNIT_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.COMMON_NAME, COMMON_NAME))
			subject = issuer = x509.Name(name_attrs)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "008",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	
	# Génération du .key
	if not error :
		try:
			key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_BITS)
			with open(OUT_KEY, "wb") as f:
				f.write(key.private_bytes(
					encoding=serialization.Encoding.PEM,
					format=serialization.PrivateFormat.TraditionalOpenSSL,
					encryption_algorithm=serialization.NoEncryption()
				))
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "009",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# Création des SANs
	if not error :
		try:
			dns_raw = config_creation.get('certif', 'DNS', fallback='')
			dns_list = [ip.strip() for ip in dns_raw.split(',') if ip.strip()]
			ip_raw = config_creation.get('certif', 'IP', fallback='')
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
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "010",
				"message": f"{e}",
				"message2": ""
			}
			error = True

	# Création du CSR
	if not error :
		try:
			csr_builder = x509.CertificateSigningRequestBuilder().subject_name(subject)
			if san_list:
				csr_builder = csr_builder.add_extension(x509.SubjectAlternativeName(san_list), critical=False)
			csr = csr_builder.sign(key, hashes.SHA256())
			with open(OUT_CSR, "wb") as f:
				f.write(csr.public_bytes(serialization.Encoding.PEM))
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "011",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# Création du crt
	if not error :
		try:
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
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "012",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	# Si création du PFX à faire
	if PFX_GEN :
		if not error :
			try:
				pfx_bytes = None
				if PFX_PASSWORD == "":
					pfx_bytes = pkcs12.serialize_key_and_certificates(
						name=bytes(config_creation['certif'].get('COMMON_NAME', ''), 'utf-8') or None,
						key=key,
						cert=cert,
						cas=None,
						encryption_algorithm=NoEncryption()
					)
				else:
					pfx_bytes = pkcs12.serialize_key_and_certificates(
						name=bytes(config_creation['certif'].get('COMMON_NAME', ''), 'utf-8') or None,
						key=key,
						cert=cert,
						cas=None,
						encryption_algorithm=BestAvailableEncryption(PFX_PASSWORD.encode())
					)

				with open(OUT_PFX, "wb") as f:
					f.write(pfx_bytes)
			except Exception as e:
				return {
					"code": ID_APP,
					"result": "",
					"error": "013",
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

# Traitement de la création
def creation_crt_info(COMMON_NAME,
					  COUNTRY_NAME,STATE_OR_PROVINCE_NAME,LOCALITY_NAME,ORGANIZATION_NAME,ORGANIZATIONAL_UNIT_NAME,
					  NB_BITS,
					  JOURS,
					  dns_raw,
					  ip_raw,
					  PFX_GEN,PFX_PASSWORD,
					  DOSSIER_EXPORT,
					  debug):
	
	error = False
	ID_APP = "CRI"
	
	if not error :
		try:
			if not COUNTRY_NAME:
				COUNTRY_NAME = "FR"
			if not STATE_OR_PROVINCE_NAME:
				STATE_OR_PROVINCE_NAME = "FRANCE"
			if not LOCALITY_NAME:
				LOCALITY_NAME = "DARDILLY"
			if not ORGANIZATION_NAME:
				ORGANIZATION_NAME = "LUVA"
			if not ORGANIZATIONAL_UNIT_NAME:
				ORGANIZATIONAL_UNIT_NAME = "LUVA"
			if not PFX_PASSWORD:
				PFX_PASSWORD = ""
			if not PFX_GEN:
				PFX_GEN = False
			if not NB_BITS:
				NB_BITS = "2048"
			if not JOURS:
				JOURS="365"
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
			OUT_KEY = Path(f"{DOSSIER_EXPORT}{COMMON_NAME}.key")
			OUT_CSR = Path(f"{DOSSIER_EXPORT}{COMMON_NAME}.csr")
			OUT_CRT = Path(f"{DOSSIER_EXPORT}{COMMON_NAME}.crt")
			OUT_PFX = Path(f"{DOSSIER_EXPORT}{COMMON_NAME}.pfx")
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
			KEY_BITS = int(NB_BITS)
			DAYS = int(JOURS) 
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "003",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# Build subject
	if not error :
		try:
			name_attrs = []
			name_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, COUNTRY_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, STATE_OR_PROVINCE_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, LOCALITY_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, ORGANIZATION_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ORGANIZATIONAL_UNIT_NAME))
			name_attrs.append(x509.NameAttribute(NameOID.COMMON_NAME, COMMON_NAME))
			subject = issuer = x509.Name(name_attrs)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	
	
	
	# Génération du .key
	if not error :
		try:
			key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_BITS)
			with open(OUT_KEY, "wb") as f:
				f.write(key.private_bytes(
					encoding=serialization.Encoding.PEM,
					format=serialization.PrivateFormat.TraditionalOpenSSL,
					encryption_algorithm=serialization.NoEncryption()
				))
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "005",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# Création des SANs
	if not error :
		try:
			
			dns_list = [ip.strip() for ip in dns_raw.split(',') if ip.strip()]
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
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "006",
				"message": f"{e}",
				"message2": ""
			}
			error = True

	# Création du CSR
	if not error :
		try:
			csr_builder = x509.CertificateSigningRequestBuilder().subject_name(subject)
			if san_list:
				csr_builder = csr_builder.add_extension(x509.SubjectAlternativeName(san_list), critical=False)
			csr = csr_builder.sign(key, hashes.SHA256())
			with open(OUT_CSR, "wb") as f:
				f.write(csr.public_bytes(serialization.Encoding.PEM))
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "007",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	# Création du crt
	if not error :
		try:
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
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "008",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	# Si création du PFX à faire
	if PFX_GEN :
		if not error :
			try:
				pfx_bytes = None
				if PFX_PASSWORD == "":
					pfx_bytes = pkcs12.serialize_key_and_certificates(
						name=bytes(COMMON_NAME, 'utf-8') or None,
						key=key,
						cert=cert,
						cas=None,
						encryption_algorithm=NoEncryption()
					)
				else:
					pfx_bytes = pkcs12.serialize_key_and_certificates(
						name=bytes(COMMON_NAME, 'utf-8') or None,
						key=key,
						cert=cert,
						cas=None,
						encryption_algorithm=BestAvailableEncryption(PFX_PASSWORD.encode())
					)

				with open(OUT_PFX, "wb") as f:
					f.write(pfx_bytes)
			except Exception as e:
				return {
					"code": ID_APP,
					"result": "",
					"error": "009",
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