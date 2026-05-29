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

import getpass

from openpyxl import load_workbook

import luva_lic
import luva_code
import db_class
import solr_class

import Youdoc_Youdoc_VerifIndex_complement

# Pour les erreurs dans les evenements
service_base = "Youdoc_Keycloak_creator"
licence_base = "9736234122426398669" # sur l'année 2026

contrainte_active_ini = True #doit faire la vérification du fichier .ini
contrainte_contient_luva = False # Doit faire la vérification du nom du programme : True / False
contrainte_active_lic = True # Doit faire la vérification de la license : True / False
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
    input()
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
        input()
        sys.exit(1)  # Quitte l'application avec un code d'erreur
    elif MODE_DEV :
        print(f"> DEV > licence > VALIDE")

### fin traitement des logs

# Main
if __name__ == "__main__":
    
    print("")
    print(f">   > Début du traitement du programme de création automatique des Roles Keycloak pour YDG")
    print("")
    print(f"> 1 > Récuperation des paramètres du fichier {ini_filename}")
    
    
    KEYCLOAK_VERIF_DEBUG_PARAM = luva_code.get_bool_param(config,'LUVA','DEBUG')
    if KEYCLOAK_VERIF_DEBUG_PARAM["error"] :
        DEBUG = False
    else :
        DEBUG = KEYCLOAK_VERIF_DEBUG_PARAM["return"]
    
    KEYCLOAK_VERIF_DEBUG_PARAM = luva_code.get_bool_param(config,'LUVA','IS_DEBUG')
    if KEYCLOAK_VERIF_DEBUG_PARAM["error"] :
        is_debug = False
    else :
        is_debug = KEYCLOAK_VERIF_DEBUG_PARAM["return"]
    
    DEBUT = luva_code.get_param(config,'LUVA','DEBUT')
    if DEBUT["error"] :
        DEBUT = 0
    else :
        DEBUT = DEBUT["return"]
    FIN = luva_code.get_param(config,'LUVA','FIN')
    if FIN["error"] :
        FIN = 0
    else :
        FIN = FIN["return"]
    
    SOLR_hostname = luva_code.get_param(config,'SOLR','SOLR_hostname')
    if SOLR_hostname["error"] :
        print(SOLR_hostname["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        SOLR_hostname = SOLR_hostname["return"]
    
    SOLR_username = luva_code.get_param(config,'SOLR','SOLR_username')
    if SOLR_username["error"] :
        print(SOLR_username["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        SOLR_username = SOLR_username["return"]
    
    VERIF_SSL = luva_code.get_bool_param(config,'SOLR','VERIF_SSL')
    if VERIF_SSL["error"] :
        VERIF_SSL = False
    else :
        VERIF_SSL = VERIF_SSL["return"]
    
    SOLR_password = luva_code.get_param(config,'SOLR','SOLR_password')
    if SOLR_password["error"] :
        print(SOLR_password["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        SOLR_password = SOLR_password["return"]
    
    SOLR_tenant = luva_code.get_param(config,'SOLR','SOLR_tenant')
    if SOLR_tenant["error"] :
        print(SOLR_tenant["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        SOLR_tenant = SOLR_tenant["return"]

    SOLR_requete = luva_code.get_param(config,'SOLR','SOLR_requete')
    if SOLR_requete["error"] :
        print(SOLR_requete["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        SOLR_requete = SOLR_requete["return"]
    
    SOLR_lot = luva_code.get_param(config,'SOLR','SOLR_lot')
    if SOLR_lot["error"] :
        print(SOLR_lot["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        SOLR_lot = SOLR_lot["return"] 
    
    if is_debug :
        print(f"")
        print(f"> 1 > IS_DEBUG = {is_debug}")
        print(f"> 1 > LICENCE = {licence}")
        print(f"> 1 > DEBUT = {DEBUT}")
        print(f"")
    
    print(f"> 1 > Connexion SOLR à l'adresse {SOLR_hostname} avec la vérification SSL à {VERIF_SSL}")
    print(f"> 1 > Connexion SOLR avec user {SOLR_username} mdp {SOLR_password}")
    print(f"> 1 > Liste des {SOLR_requete} sur le tenant {SOLR_tenant} par lot de {SOLR_lot}")
    
    DB_type = luva_code.get_param(config,'SGBD','DB_type')
    if DB_type["error"] :
        print(DB_type["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_type = DB_type["return"]
        
    DB_driver = luva_code.get_param(config,'SGBD','DB_driver')
    if DB_driver["error"] :
        print(DB_driver["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_driver = DB_driver["return"]
        
    DB_server = luva_code.get_param(config,'SGBD','DB_server')
    if DB_server["error"] :
        print(DB_server["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_server = DB_server["return"]
        
    DB_port = luva_code.get_param(config,'SGBD','DB_port')
    if DB_port["error"] :
        print(DB_port["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_port = DB_port["return"]
        
    DB_username = luva_code.get_param(config,'SGBD','DB_username')
    if DB_username["error"] :
        print(DB_username["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_username = DB_username["return"]
        
    DB_password = luva_code.get_param(config,'SGBD','DB_password')
    if DB_password["error"] :
        print(DB_password["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_password = DB_password["return"]
        
    DB_database = luva_code.get_param(config,'SGBD','DB_database')
    if DB_database["error"] :
        print(DB_database["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_database = DB_database["return"]
        
    DB_data = luva_code.get_param(config,'SGBD','DB_data')
    if DB_data["error"] :
        print(DB_data["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_data = DB_data["return"]
        
    DB_name = luva_code.get_param(config,'SGBD','DB_name')
    if DB_name["error"] :
        print(DB_name["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        DB_name = DB_name["return"]
        
    print(f"")
    print(f"> 1 > Connexion {DB_type} sur le driver {DB_driver}")
    print(f"> 1 > Serveur {DB_server} port {DB_port}")
    print(f"> 1 > User {DB_username} port {DB_password}")
    print(f"> 1 > Enregistrement dans {DB_database}.dbo.{DB_data} dans {DB_name}")
    print(f"")
    print(f"> 1 > Récuperation des paramètres du fichier {ini_filename} > FINI")
    print(f"")
   
    print(f"> 2 > Connexion SOLR")
    
    SOLR_TOTAL = int(FIN) 
    ClientSolr = solr_class.SolrConnection(SOLR_hostname,SOLR_username,SOLR_password,SOLR_tenant,VERIF_SSL,is_debug)
    rows = 0
    solr_query = f"id:*{SOLR_requete}{SOLR_tenant}*"
    
    if FIN == 0 :
        
        retour = ClientSolr.SolrCount(solr_query, rows)
        
        print(f"> 2 > Connexion SOLR > resultat sur *{SOLR_requete}* = {retour["return"]}")
        SOLR_TOTAL = int(retour["return"])
        
        if int(FIN) == 0 :
            FIN = SOLR_TOTAL
        
    print(f"> 2 > Connexion SOLR > Fini")
    print("")
       
    print(f"> 3 > Connexion SQL ")
    db = db_class.DatabaseConnection(DB_type, DB_driver, DB_server,DB_port, DB_database, DB_username, DB_password)
    return_db = db.connect()
    if return_db["error"] == "" : 
        print(f"> 3 > {return_db["result"]}")
    else :
        print(f"> 3 > connexion {return_db["result"]} {return_db["message"]}")
        db.close()
        input()
        sys.exit(1)
    print(f"> 3 > Connexion SQL > FINI ")
    print("")
    print(f"> 3 > Traitement des id ")
    
    SORL_START = int(DEBUT)
    rows = int(SOLR_lot)
    if int(FIN) > SOLR_TOTAL:
        FIN = SOLR_TOTAL
    while SORL_START < int(FIN):
        try :
            
        
            if int(FIN)-SORL_START < rows :
                temp_rows = int(FIN)-SORL_START
            else :
                temp_rows = rows
            SORL_TEMP = SORL_START + temp_rows
            print(f"> 3 > Traitement de {SORL_START} à {SORL_TEMP} sur {DEBUT} et {FIN}  ")
            retour = ClientSolr.SolrListeID(solr_query, temp_rows, SORL_START)
            SORL_START = SORL_START + temp_rows
            data = retour["return"]
            data.json()
            ids = data.json()["response"]["docs"]
            if not ids:
                break  # Sortir si aucune donnée n'est renvoyée
            # Insérer les ID dans la base de données
            for doc in ids:
                id_value = doc['id'].replace(f"{SOLR_requete}{SOLR_tenant}-","")
                if DEBUG : print(f"> DEBUG > {id_value}")
                db_query = f"INSERT INTO [{DB_database}].[dbo].[{DB_data}] ({DB_name},STATUS) VALUES ('{id_value}','I')"
                if is_debug : print(f"> DEBUG > {db_query}")
                returndb = db.execute_query_save(db_query)
                if returndb == "ERROR" :
                    print(f"> {id_value} > Une erreur d'enregistrement à eu lieu")
                    
                else :
                    if is_debug : print(f"> DEBUG > enreg ok")
        except Exception as e:
            print(f"> ERREUR > Traitement de {SORL_START} à {SORL_TEMP} sur {DEBUT} et {FIN}  ")
            print(f"> ERREUR > {e} ")
            print(f"Entrer pour continuer ")
            input()
    db.close()
    
    print("")
    print(f"> 4 > Fin du traitement")
    print("")
    print("Bon courage pour la suite")
    print("")
    print(r"  (\_/)")
    print(r" =(^.^)=")
    print("  (LUVA)")
    print(" ( )_( )")
    print("")
    print("Appuyer sur entrer pour fermer")
    input()