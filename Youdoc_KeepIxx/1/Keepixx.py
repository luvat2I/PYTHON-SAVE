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
from datetime import date
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
import threading
from multiprocessing import Process, Queue

import getpass

from openpyxl import load_workbook

import luva_lic
import luva_code
import db_class
import solr_class

import Youdoc_Youdoc_VerifIndex_complement

# Pour les erreurs dans les evenements
service_base = "Youdoc_keepixx"
licence_base = "9736234122426398669" # sur l'année 2026

contrainte_active_ini = True #doit faire la vérification du fichier .ini
contrainte_contient_luva = False # Doit faire la vérification du nom du programme : True / False
contrainte_active_lic = False # Doit faire la vérification de la license : True / False
event_active_log = False # Doit activer les logs des events : True / False
MODE_DEV = False

if contrainte_active_lic and not MODE_DEV : contrainte_active_ini = True #secu pour le mode dev

### Génération du nom du fichier ini
ini_filename = luva_code.get_ini_path()
if MODE_DEV : print(f"> DEV > ini_filename : {ini_filename}")

### Récupération du nom du programme
nom_programme = luva_code.get_nom_programme()
if MODE_DEV : print(f"> DEV > nom_programme : {nom_programme}")

### Vérification de contient service
contient_service = luva_code.nom_programme_contient(nom_programme,"SERVICE")
if contient_service :
    traitement_type = "service"
else:
    traitement_type = "exe"
traitement_type = "service"
### Vérification de contient LUVA
contient_luva = luva_code.nom_programme_contient(nom_programme,"LUVA")
if contrainte_contient_luva and not contient_luva :
    print(f"ERROR : Nom du programme non conforme")
    input()
    sys.exit(1)

### Variables complémentaires
log_event_level = "ERROR"
log_folder_level = "ERROR"
log_console_level = "WARNING"

time_sleep=0

log_levels = {"DEBUG": logging.DEBUG,"INFO": logging.INFO,"WARNING": logging.WARNING,"ERROR": logging.ERROR}

# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

### lecture du fichier INI pour le traitement de toutes les entrées
config = configparser.ConfigParser()

## creation des loggers
logger_service = logging.getLogger(service_base)
logger_service.setLevel(logging.WARNING)
event_handler = logging.handlers.NTEventLogHandler(service_base)
logger_service.addHandler(event_handler)

if event_active_log : luva_code.create_event_source(f"{service_base}")

### Lecture du fichier INI et gestion des logs ###
try:
    if not os.path.exists(ini_filename):
        luva_code.log_secure("0","INFO",f"Pas de fichier ini '{ini_filename}'",log_event_level,logger_service,log_console_level,traitement_type)
        log_validation = False
    else :
        luva_code.log_secure("0","INFO",f"Fichier ini '{ini_filename}' est présent",log_event_level,logger_service,log_console_level,traitement_type)
        log_validation = True
        config.read(f'{ini_filename}')
        if not config.sections():  # Vérifie si le fichier ini est vide
            if contrainte_active_ini : 
                luva_code.log_secure("0","ERROR",f"Le fichier de configuration '{ini_filename}' est vide.",log_event_level,logger_service,log_console_level,traitement_type)
                sys.exit(1)  # ferme lapp
            else :
                luva_code.log_secure("0","INFO",f"Le fichier de configuration '{ini_filename}' est vide.",log_event_level,logger_service,log_console_level,traitement_type)
except Exception as e:
    luva_code.log_secure("0","ERROR",f"Probleme de traitement du fichier '{ini_filename}': {e}",log_event_level,logger_service,log_console_level,traitement_type)
    sys.exit(1)  # ferme lapp
enable_logging = False
### Valide l'activation des logs
if log_validation : enable_logging = luva_code.get_enable_logging(log_validation,config)

if enable_logging :
    try:
        log_folder = config['logging']['log_folder']
    except Exception as e: enable_logging = False
    
    try: 
        log_folder_level = config['logging']['log_folder_level']
    except Exception as e: log_folder_level = "ERROR"

try:
    if log_validation : log_console_level = config['logging']['log_console_level']
    else : log_console_level = "INFO"
except Exception as e: log_console_level = "INFO"

try:    
    if enable_logging: os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log
except Exception as e:
    luva_code.log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}",log_event_level,logger_service,log_console_level,traitement_type)
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
    luva_code.log_secure("0","ERROR",f"creation du dossier {log_folder} impossible : {e}",log_event_level,logger_service,log_console_level,traitement_type)
    sys.exit(1)  # Quitte l'application avec un code d'erreur    

try:
    log_event_level = config['logging']['log_event_level']
    luva_code.log_console("DEBUG",f"L'option 'log_event_level' est de niveau '{log_event_level}'",log_console_level,traitement_type)
except Exception as e:
    log_event_level = "ERROR"
verif = False

log_level2 = log_levels.get(log_event_level, logging.ERROR)
logger_service.setLevel(log_level2)

if contrainte_active_ini :
    licence_valide = False
    
    
    licence = luva_code.get_licence(config)
    if licence_base and licence == "ERROR" :
        licence = licence_base
    
    if MODE_DEV : print(f"> DEV > licence > {licence}")
    
    LUVA_VERIF_LICENCE = luva_code.get_param(config,'LUVA','LICENCE')
    if not LUVA_VERIF_LICENCE["error"] :
        licence = LUVA_VERIF_LICENCE["return"]
    
    try:
        licence_valide = luva_lic.valide_licence(licence,MODE_DEV)
    except Exception as e:
        licence_valide = False
        
    if not licence_valide :
        luva_code.log_secure("0","ERROR",f"ERREUR INCONNU 00",log_event_level,logger_service,log_console_level,traitement_type)
        sys.exit(1)  # Quitte l'application avec un code d'erreur
    elif MODE_DEV :
        print(f"> DEV > licence > VALIDE")

### fin traitement des logs

# Main
if __name__ == "__main__":

    DEBUG = True
    IS_DEBUG = False
    
    TYPE_DOC = "IXX"
    ECM_IXX_INPUT = r"D:\PYTHON\Youdoc_KeepIxx\ixx\input"
    ECM_IXX_ERROR = r"D:\PYTHON\Youdoc_KeepIxx\ixx\error"
    ECM_IXX_OUTPUT = r"D:\PYTHON\Youdoc_KeepIxx\ixx\output"
    ECM_IXX_WORKING = r"D:\PYTHON\Youdoc_KeepIxx\ixx\working"
    IS_ARCHIVE = True
    ECM_IXX_ARCHIVE = r"D:\PYTHON\Youdoc_KeepIxx\ixx\archive"
    
    PARAM_TIME = 5
    
    
    
    
    
    global fichiers_INPUT
    fichiers_INPUT = set()
    source_INPUT = Queue()
    
    global fichiers_ERROR
    fichiers_ERROR = set()
    source_ERROR = Queue()
    
    global fichiers_OUTPUT
    fichiers_OUTPUT = set()
    source_OUTPUT = Queue()
    
    global fichiers_WORKING
    fichiers_WORKING = set()
    source_WORKING = Queue()
    
    while True :
        
        if DEBUG : print("boucle")
        
        for file in os.listdir(ECM_IXX_ERROR) :
            if file not in fichiers_ERROR:
                print(file)
                source_ERROR.put(file)
                fichiers_ERROR.add(file)
        
        for file in os.listdir(ECM_IXX_INPUT) :
            if file not in fichiers_INPUT:
                print(file)
                source_INPUT.put(file)
                fichiers_INPUT.add(file)
        
        for file in os.listdir(ECM_IXX_OUTPUT) :
            if file not in fichiers_OUTPUT:
                print(file)
                source_OUTPUT.put(file)
                fichiers_OUTPUT.add(file)
        
        for file in os.listdir(ECM_IXX_WORKING) :
            if file not in fichiers_WORKING:
                print(file)
                source_WORKING.put(file)
                fichiers_WORKING.add(file)
        
        
        
        time.sleep(PARAM_TIME)
        


    fichiers_traites.remove(file)        
    
    for file in os.listdir(ECM_IXX_INPUT) :
        print(file)
        source_queue.put(file)
    
    while not source_queue.empty():
        item = source_queue.get()
        print(item)
        
        
    
    