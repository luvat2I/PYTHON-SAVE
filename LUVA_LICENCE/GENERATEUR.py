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
import getpass
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

import luva_lic

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


log_level2 = log_levels.get(log_event_level, logging.ERROR)
logger_service.setLevel(log_level2)

# Main
if __name__ == "__main__":
    validation_mdp = False
    while True:
        mdp_luva = getpass.getpass("Entrez le mot de passe : ")
        if mdp_luva:
            break
        print("Le mot de passe ne peut pas être vide. Réessayez.")
    
    if mdp_luva == "Ght1qiratir":
        validation_mdp = True
    
    if validation_mdp :
        print("GOOD mot de passe")
        print("-----------------")
        while True:
            type = input("Entrez le type de licence : 'AN' 'MOIS' 'JOURS' 'DUREE' ").strip()
            if type:
                break
                
        mois = None
        jour = None
        duree = None
        DEV = False
        
        while True:
            annee = input("Entrez l'année : ").strip()
            if annee:
                break
                
        if type == "MOIS" or type == "JOURS":
        
            while True:
                mois = input("Entrez le mois :").strip()
                if mois:
                    break
                    
        if type == "JOURS":
            while True:
                jour = input("Entrez le jour :").strip()
                if jour:
                    break
                    
        if type == "DUREE" :
            while True:
                duree = input("Entrez la duree :").strip()
                if duree:
                    break    

        code_lic = luva_lic.luva_lic_calcul(type,annee,mois,jour,duree,DEV)
        # Chemin du fichier licence.lic dans le même dossier que le script
        
        print(code_lic)
        
        licence_valide = luva_lic.valide_licence(code_lic,DEV)
        if licence_valide :
            print("LICENCE GOOD")
        else :
            print("LICENCE BAD")
    else :
        print("BAD mot de passe")
        
    print("Fin")
    input()