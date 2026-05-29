import os
import urllib3
import configparser
import ast
from datetime import datetime, timedelta
import threading
from multiprocessing import Process, Queue
import re
import sys
import uuid
import time
import json
import requests
from typing import Dict, Any, Optional
from requests.auth import HTTPBasicAuth

import xml.etree.ElementTree as ET

#----------- IMPORT LIB EXTERNE
import luva_lic         #--licence
import luva_code        #--luva
import keycloak_suite   #--Keycloak
import group_gestion    #--Youdoc Gestion
import complement       #--complements
import luva_file        #--luva_file
import luva_console     #--luva_console
import solr_event       #--solr_event
import db_class         #--db_class

#----------- LICENCES
licence_base = "9736234122426398669" # 2026

#----------- Config
contrainte_active_ini = True        # Doit faire la vérification du fichier .ini        : True / False
contrainte_contient_luva = False    # Doit faire la vérification du nom du programme    : True / False
contrainte_active_lic = False        # Doit faire la vérification de la license         : True / False
contrainte_is_service = False        # Doit être un service                             : True / False 
possible_confi_ini = True           # Doit être un service                              : True / False 

#----------- Active le MOD-DEV 
MODEDEV = False
if contrainte_active_lic and not MODEDEV : contrainte_active_ini = True # Secu recup ini pour la licence


#----------- Init du log
dossier_courant = os.getcwd()
dossier_log = os.path.join(dossier_courant, "logs")
if not os.path.exists(dossier_log): os.makedirs(dossier_log)

nom_programme = luva_code.get_nom_programme()

log_file = luva_file.GestionnaireLogFile(
        nom_dossier=dossier_log,
        nom_fichier=f"{nom_programme}.log",
        niveau="INFO",
        max_bytes=2*1024*1024,  # 2 Mo
        backup_count=5
    )
    
log_file.info("------------------------------------------------")  
log_file.info("SERVICE démarré")

if MODEDEV : 
    log_console = luva_console.Logger(luva_console.LogLevel.DEBUG)
elif contrainte_is_service :
    log_console = luva_console.Logger(luva_console.LogLevel.DISABLED)
else :
    log_console = luva_console.Logger(luva_console.LogLevel.INFO)

log_console.debug(f"MODEDEV = {MODEDEV}")
log_console.info(f"SERVICE démarré")

#----------- Gestion du INI
ini_filename = luva_code.get_ini_path()
log_console.info(f"ini_filename : {ini_filename}")
log_file.info(f"ini_filename : {ini_filename}")



contient_service = luva_code.nom_programme_contient(nom_programme,"SERVICE")
if contient_service :
    traitement_type = "SERVICE"
else:
    traitement_type = "EXE"
    
log_console.debug(f"traitement_type : {traitement_type}")

#----------- Gestion de contient luva
contient_luva = luva_code.nom_programme_contient(nom_programme,"LUVA")
if contrainte_contient_luva and not contient_luva :
    log_console.error(f"Nom du programme non conforme")
    log_file.error(f"Nom du programme non conforme")
    if not contrainte_is_service : input()
    sys.exit(1)

#----------- Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#----------- Lecture du fichier ini
if contrainte_active_ini :
    ini_filename_error = True
    config = configparser.ConfigParser()
    try:
        if not os.path.exists(ini_filename):
            ini_filename_error = True
            log_console.debug(f"fichier ini : inaccessible donc ini_filename_error = True")
        else :
            ini_filename_error = False
            log_console.info(f"fichier ini : accessible")
            log_file.info(f"fichier ini : accessible")
            config.read(f'{ini_filename}')
            if not config.sections():  # Vérifie si le fichier ini est vide
                log_console.error(f"Le fichier de configuration '{ini_filename}' est vide.")
                log_file.error(f"Le fichier de configuration '{ini_filename}' est vide.")
                if not contrainte_is_service :
                    print("Appuyer sur entrer pour fermer")
                    input()
                sys.exit(1)  # ferme lapp
    except Exception as e:
        log_console.error(f"erreur de traitement du fichier .ini : '{e}'")
        log_file.error(f"erreur de traitement du fichier .ini : '{e}'")
        if not contrainte_is_service :
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)  # ferme lapp
    
    CONFIG_INI_PARAM = luva_code.get_param(config,'INI','CONFIG_INI')
    if CONFIG_INI_PARAM["error"] :
        CONFIG_INI = ""
    else :
        CONFIG_INI = CONFIG_INI_PARAM["return"]
        CONFIG_INI = os.path.join(dossier_courant, CONFIG_INI)
    
    try:
        if CONFIG_INI != "" :
            log_console.info(f"redirection ini_filename : {CONFIG_INI}")
            log_file.info(f"redirection ini_filename : {CONFIG_INI}")
            if not os.path.exists(CONFIG_INI):
                log_console.error(f"fichier ini : inaccessible")
                log_file.error(f"fichier ini : inaccessible")
                if not contrainte_is_service :
                    print("Appuyer sur entrer pour fermer")
                    input()
                sys.exit(1)  # ferme lapp
            else :
                log_console.info(f"fichier ini : accessible")
                log_file.info(f"fichier ini : accessible")
                config.read(f'{CONFIG_INI}')
                if not config.sections():  # Vérifie si le fichier ini est vide
                    log_console.error(f"Le fichier de configuration '{CONFIG_INI}' est vide.")
                    log_file.error(f"Le fichier de configuration '{CONFIG_INI}' est vide.")
                    if not contrainte_is_service :
                        print("Appuyer sur entrer pour fermer")
                        input()
                    sys.exit(1)  # ferme lapp
    except Exception as e:
        log_console.error(f"erreur de traitement du fichier .ini : '{e}'")
        log_file.error(f"erreur de traitement du fichier .ini : '{e}'")
        if not contrainte_is_service :
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)  # ferme lapp
    
    if ini_filename_error and possible_confi_ini:
        CONFIG_INI = "config.ini"
        CONFIG_INI = os.path.join(dossier_courant, CONFIG_INI)
        if not os.path.exists(CONFIG_INI):
            log_console.error(f"fichier ini : {CONFIG_INI} innaccessible")
            if not contrainte_is_service :
                print("Appuyer sur entrer pour fermer")
                input()
            sys.exit(1)  # ferme lapp
        else :
            log_console.info(f"fichier ini : accessible")
            log_file.info(f"fichier ini : accessible")
            config.read(f'{CONFIG_INI}')
            if not config.sections():  # Vérifie si le fichier ini est vide
                log_console.error(f"Le fichier de configuration '{CONFIG_INI}' est vide.")
                log_file.error(f"Le fichier de configuration '{CONFIG_INI}' est vide.")
                if not contrainte_is_service :
                    print("Appuyer sur entrer pour fermer")
                    input()
                sys.exit(1)  # ferme lapp
    else :
        log_console.error(f"erreur de traitement du fichier .ini")
        log_file.error(f"erreur de traitement du fichier .ini")
        if not contrainte_is_service :
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)  # ferme lapp
        
#----------- Gestion de la licence
if contrainte_active_lic :
    licence_valide = False
    
    licence = luva_code.get_licence(config)
    if licence_base and licence == "ERROR" :
        licence = licence_base
        
    log_console.debug(f"LICENCE = {licence}")
    
    LUVA_VERIF_LICENCE = luva_code.get_param(config,'LUVA','LICENCE')
    if not LUVA_VERIF_LICENCE["error"] : licence = LUVA_VERIF_LICENCE["return"]
    
    try: licence_valide = luva_lic.valide_licence(licence,MODEDEV)
    except Exception as e: licence_valide = False
        
    if not licence_valide :
        log_console.error(f"Erreur python inconnu il faut faire la vérification de la licence")
        log_file.error(f"Erreur python inconnu il faut faire la vérification de la licence")
        if not contrainte_is_service : input()
        sys.exit(1)
    elif MODEDEV :
        log_console.debug(f"Modedev donc valide la licenece")
        
#--------------------------------------------------------------------- 
#- MAIN
#---------------------------------------------------------------------        

if __name__ == "__main__":

    log_console.info(f"------------------------------------------------")
    log_file.info(f"------------------------------------------------")
    log_console.info(f"Récuperation des paramètres du fichier INI")
    log_file.info(f"Récuperation des paramètres du fichier INI")
    
    #--------------------------------------------------------------------- 
    #- SERVICE
    #---------------------------------------------------------------------
    
    db_type = luva_code.recup_param_exit(config,'SGBD','db_type',contrainte_is_service,log_console,log_file)
    db_driver = luva_code.recup_param_exit(config,'SGBD','db_driver',contrainte_is_service,log_console,log_file)
    db_server = luva_code.recup_param_exit(config,'SGBD','db_server',contrainte_is_service,log_console,log_file)
    db_port = luva_code.recup_param_exit(config,'SGBD','db_port',contrainte_is_service,log_console,log_file)
    db_username = luva_code.recup_param_exit(config,'SGBD','db_username',contrainte_is_service,log_console,log_file)
    db_password = luva_code.recup_param_exit(config,'SGBD','db_password',contrainte_is_service,log_console,log_file)
    db_database = luva_code.recup_param_exit(config,'SGBD','db_database',contrainte_is_service,log_console,log_file)
    
    #--------------------------------------------------------------------- 
    #- PARAM LUVA
    #---------------------------------------------------------------------
    
    DEBUG = luva_code.recup_bool_param_valeur(config,'SGBD','DEBUG',contrainte_is_service,log_console,log_file,False)
    is_debug = luva_code.recup_bool_param_valeur(config,'SGBD','IS_DEBUG',contrainte_is_service,log_console,log_file,False)
    
    #--------------------------------------------------------------------- 
    #- SOLR
    #---------------------------------------------------------------------
    
    SOLR_URL = luva_code.recup_param_exit(config,'SOLR','SOLR_URL',contrainte_is_service,log_console,log_file)
    SOLR_LOGIN = luva_code.recup_param_valeur(config,'SOLR','SOLR_LOGIN',contrainte_is_service,log_console,log_file,"default-svc-usr")
    SOLR_PASSWORD = luva_code.recup_param_valeur(config,'SOLR','SOLR_PASSWORD',contrainte_is_service,log_console,log_file,"zYDdjrIZ2M1jbgv")
    SOLR_LOG = luva_code.recup_bool_param_valeur(config,'SOLR','SOLR_LOG',contrainte_is_service,log_console,log_file,True)
    SOLR_TIMEOUT_TIME = luva_code.recup_param_valeur(config,'SOLR','SOLR_TIMEOUT_TIME',contrainte_is_service,log_console,log_file,10)
    SOLR_VERIF_SSL = luva_code.recup_bool_param_valeur(config,'SOLR','SOLR_VERIF_SSL',contrainte_is_service,log_console,log_file,False)
    SOLR_TENANT=db_database[-3:]
    #--------------------------------------------------------------------- 
    #- PAC
    #---------------------------------------------------------------------
    
    parameter_file = luva_code.recup_param_exit(config,'PAC','parameter_file',contrainte_is_service,log_console,log_file)
    
    #--------------------------------------------------------------------- 
    #- LOG
    #---------------------------------------------------------------------
    
    if is_debug :
        log_console.debug(f"----------------------------------------------------")
        log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
        
    log_file.debug(f"----------------------------------------------------")
    log_file.info(f"Recupération des param DB > OK")
    
    #--------------------------------------------------------------------- 
    #- PARAM
    #---------------------------------------------------------------------
    
    CODE_EVENT = "S"
    TENANT_EVENT = SOLR_TENANT
    USER_EVENT = SOLR_LOGIN
    
    FRAMEWORK_EVENT = "PAC"
    
    LOGICIEL_EVENT = "PAC"
    SOFTWARE_EVENT = "PAC"
    
    CATEGORIE_EVENT = "Programme"
    
    #--------------------------------------------------------------------- 
    #- DEBUT
    #---------------------------------------------------------------------
    
    log_console.info(f"----------------------------------------------------")
    log_file.info(f"----------------------------------------------------")
    
    log_console.info(f"Debut du traitement")
    log_file.info(f"Debut du traitement")
    
    #--------------------------------------------------------------------- 
    #- SOLR LOG
    #---------------------------------------------------------------------
    
    if SOLR_LOG :
        log_sorl = solr_event.SolrEventPublisher(f"{SOLR_URL}",TENANT_EVENT,SOLR_LOGIN,SOLR_PASSWORD,SOLR_VERIF_SSL,SOLR_TIMEOUT_TIME)
        RESULT_SOLR = log_sorl.test_connection()
        luva_code.erreur_exit(RESULT_SOLR,log_console,log_file,contrainte_is_service,f"connexion SOLR valide")

        
        RESULT_SOLR = log_sorl.init_event_info(TENANT_EVENT,USER_EVENT,FRAMEWORK_EVENT,LOGICIEL_EVENT,SOFTWARE_EVENT,CODE_EVENT)
        luva_code.erreur_exit(RESULT_SOLR,log_console,log_file,contrainte_is_service,f"init_event_info SOLR ok")
        
        complement.solr_event_cours(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,"Init",CODE_EVENT)

    #--------------------------------------------------------------------- 
    #- Connexion BDD
    #---------------------------------------------------------------------
    
    
    
    log_file.info(f"-------")
    log_console.info(f"-------")
    
    log_file.info(f"Test connexion BDD")
    log_console.info(f"Test connexion BDD")
    
    DB_CONNEXION = db_class.DatabaseConnection(db_type, db_driver, db_server,db_port, db_database, db_username, db_password, is_debug)
    
    DB_RETURN = DB_CONNEXION.connect()
    luva_code.erreur_exit_debug(DB_RETURN,log_console,log_file,contrainte_is_service,f"Creation DB = OK")
    
    DB_RETURN = DB_CONNEXION.validate_connection()
    luva_code.erreur_exit(DB_RETURN,log_console,log_file,contrainte_is_service,f"{DB_RETURN["return"]}")
    
    
    #--------------------------------------------------------------------- 
    #- Connexion BDD
    #---------------------------------------------------------------------
    
    log_file.info(f"-------")
    log_console.info(f"-------")
    
    log_file.info(f"Liste des DATABASE")
    log_console.info(f"Liste des DATABASE")
    
    caractere_special1 = '{'
    caractere_special2 = '}'
    caractere_special3 = '"'
    
    if db_type == 'DB2':
        db_query_pacref = f"SELECT DISTINCT BASEID, PACDESC FROM {db_database}.ECM_PACREF"
    else :
        db_query_pacref = f"SELECT DISTINCT baseid, pacDesc FROM [{db_database}].dbo.ecm_pacref"
        
    message = f"QUERY > {db_query_pacref}"
    log_console.debug(f"{message}")
    log_file.debug(f"{message}")
    
    DB_RETURN_PACREF = DB_CONNEXION.execute_query(db_query_pacref)
    
    message = f"Début du traitement de création des databases"
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    
    for row in DB_RETURN_PACREF["return"]:
        
        if db_type == 'DB2':
            PARAM_ID = row.BASEID
        else :
            PARAM_ID = row.baseid
            
        log_console.info(f"traitement de la BDD {PARAM_ID}")
        log_file.info(f"traitement de la BDD {PARAM_ID}")
        
        if db_type == 'DB2':
            FORMATTED_JSON = f"{caractere_special3}databaseDescription_fr{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3},{caractere_special3}databaseDescription_de{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3},{caractere_special3}databaseDescription_it{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3},{caractere_special3}databaseDescription_en{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3}"
            PARAM_DATA_FIN = f"{caractere_special3}language{caractere_special3}:{caractere_special3}fr{caractere_special3},{caractere_special3}value{caractere_special3}:{caractere_special3}{row.PACDESC}{caractere_special3}"
        else :
            FORMATTED_JSON = f"{caractere_special3}databaseDescription_fr{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_de{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_it{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_en{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
            PARAM_DATA_FIN = f"{caractere_special3}language{caractere_special3}:{caractere_special3}fr{caractere_special3},{caractere_special3}value{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
            
        if db_type == 'DB2':
            db_query_ARAMREP = f"SELECT * FROM {db_database}.ARAMREP WHERE ARAMREP.AMAWCD = '{row.BASEID}'"
        else :
            db_query_ARAMREP = f"SELECT * FROM [{db_database}].dbo.ARAMREP WHERE ARAMREP.AMAWCD = '{row.baseid}'"
            
        message = f"QUERY > {db_query_ARAMREP}"
        log_console.debug(f"{message}")
        DB_RETURN_ARAMREP = DB_CONNEXION.execute_query(db_query_ARAMREP)
        if db_type == 'DB2':
            db_query_ARGGREP = f"SELECT * FROM {db_database}.ARGGREP WHERE ARGGREP.GGAWCD = '{row.BASEID}'"
        else :
            db_query_ARGGREP = f"SELECT * FROM [{db_database}].dbo.ARGGREP WHERE ARGGREP.GGAWCD = '{row.baseid}'"
        message = f"QUERY > {db_query_ARGGREP}"
        log_console.debug(f"{message}")
        DB_RETURN_ARGGREP = DB_CONNEXION.execute_query(db_query_ARGGREP)
        
        if db_type == 'DB2':
            db_query_FLDTYP = f"SELECT DISTINCT TYPENME FROM {db_database}.ECM_FLDTYP WHERE ECM_FLDTYP.BASE = '{row.BASEID}'"
        else :
            db_query_FLDTYP = f"SELECT DISTINCT typeNme FROM [{db_database}].dbo.ECM_FLDTYP WHERE ECM_FLDTYP.BASE = '{row.baseid}'"
        message = f"QUERY > {db_query_FLDTYP}"
        log_console.debug(f"{message}")
        DB_RETURN_FLDTYP = DB_CONNEXION.execute_query(db_query_FLDTYP)
        
        PARAM_TYPE = f"DATABASE"
        PARAM_DATA = ""
        dataTypeLink = ""
        folderLinkTypes = ""
        folderTypes = ""
        
        for index, row in enumerate(DB_RETURN_ARAMREP["return"]):
            print(row.AMATCD)
            if index == len(DB_RETURN_ARAMREP["return"]) - 1: 
                dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2}"""
            else :
                dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2},"""
        
        for index, row in enumerate(DB_RETURN_ARGGREP["return"]):
        
            if index == len(DB_RETURN_ARGGREP["return"]) - 1: 
                folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2}"""
            else :
                folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2},"""
        
        for index, row in enumerate(DB_RETURN_FLDTYP["return"]):
            if db_type == 'DB2':
                if index == len(DB_RETURN_FLDTYP["return"]) - 1: 
                    folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.TYPENME}","autoIncrement":false{caractere_special2}"""
                else :
                    folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.TYPENME}","autoIncrement":false{caractere_special2},"""
            else :
                if index == len(DB_RETURN_FLDTYP["return"]) - 1: 
                    folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.typeNme}","autoIncrement":false{caractere_special2}"""
                else :
                    folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.typeNme}","autoIncrement":false{caractere_special2},"""
        
        PARAM_DATA = f"{caractere_special1}{caractere_special3}dataTypeLink{caractere_special3}:" + dataTypeLink + f","
        PARAM_DATA = PARAM_DATA + f"{caractere_special3}folderLinkTypes{caractere_special3}:[" + folderLinkTypes + f"],"
        PARAM_DATA = PARAM_DATA + f"{caractere_special3}folderTypes{caractere_special3}:[" + folderTypes + f"],"
        PARAM_DATA = PARAM_DATA + f"{caractere_special3}isPacMode{caractere_special3}:false,{caractere_special3}descriptions{caractere_special3}:[" + "{"
        PARAM_DATA = PARAM_DATA + PARAM_DATA_FIN
        PARAM_DATA = PARAM_DATA + "}]}"
        
        RADIATED = "0"
        CREATION_USER = "NULL"
        MODIFICATION_USER = "NULL"
        CREATION_DATE = "NULL"
        MODIFICATION_DATE = "NULL"
        BR_ID_DOCUMENT = "NULL"
        BR_ID_FOLDER = "NULL"
        
        if db_type == 'DB2':
            query_save = f"INSERT INTO {db_database}.ECM_PARAM (PARAM_ID, PARAM_TYPE,PARAM_DATA,RADIATED,CREATION_USER,MODIFICATION_USER,CREATION_DATE,MODIFICATION_DATE,FORMATTED_JSON,BR_ID_DOCUMENT,BR_ID_FOLDER)"
            query_save = query_save + f" select '{PARAM_ID}','{PARAM_TYPE}','{PARAM_DATA}','0',NULL,NULL,NULL,NULL,'{FORMATTED_JSON}',NULL,NULL"
            query_save = query_save + f" WHERE NOT EXISTS (SELECT 1 FROM {db_database}.ECM_PARAM WHERE param_id = '{PARAM_ID}');"
        else :
            query_save = f"INSERT INTO [{db_database}].dbo.ecm_param (param_id, param_type,param_data,radiated,creation_user,modification_user,creation_date,modification_date,formatted_json,br_id_document,br_id_folder)"
            query_save = query_save + f" select '{PARAM_ID}','{PARAM_TYPE}','{PARAM_DATA}','0',NULL,NULL,NULL,NULL,'{FORMATTED_JSON}',NULL,NULL"
            query_save = query_save + f" WHERE NOT EXISTS (SELECT 1 FROM [{db_database}].dbo.ecm_param WHERE param_id = '{PARAM_ID}');"
        
        message = f"QUERY > {query_save}"
        log_console.debug(f"{message}")
        
        #DB_RETURN_ARAMREP = DB_CONNEXION.execute_query_save(db_query_ARAMREP)
        DB_RETURN = DB_CONNEXION.execute_query_save(query_save)
        if DB_RETURN["error"] :
            log_console.error(DB_RETURN["return"])
            log_file.error(DB_RETURN["return"])
            MESSAGE_EVENT = f"Erreur de création de la DATABASE {PARAM_ID} dans ECM_PARAM"
            complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"DATABASE",MESSAGE_EVENT)
        else :
            MESSAGE_EVENT = f"Création de la DATABASE {PARAM_ID} dans ECM_PARAM"
            log_file.info(f"{MESSAGE_EVENT}")
            complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"DATABASE",MESSAGE_EVENT)

    message = f" Fin du traitement ajout des DATABASES." 
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    
    message = f"-----------------------------------------------------" 
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    
    message = f"Début du traitement ajout des MULTI." 
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    
    # Charger le fichier XML
    try :
        tree = ET.parse(f"{parameter_file}")
        root = tree.getroot()
        
        message = f"Début du traitement du fichier {parameter_file}" 
        log_console.info(f"{message}")
        log_file.info(f"{message}")
        
        for Environment in root.findall('Environment'):
            for Base in Environment.findall('Base'):
                for L_FLD in Base.findall('L_FLD'):
                    for E_FLD in L_FLD.findall('E_FLD'):
                        for L_TYP in E_FLD.findall('L_TYP'):
                            for E_TYP in L_TYP.findall('E_TYP'):
                                
                                E_TYPname = E_TYP.get('nme')
                                E_TYPmul = E_TYP.get('mul')
                                if E_TYPmul == "2" :
                                    if db_type == 'DB2':
                                        
                                        query_ECM_PARAM = f"update {db_database}.ECM_KITYDO set FLDIDXTYP = 'MULTI' where KINDID = '{E_TYPname}' "
                                        message = f"QUERY > {query_ECM_PARAM}"
                                        log_console.debug(f"{message}")
                                        message = f"Multi dossier sur Nature {E_TYPname}"
                                        log_console.info(f"{message}")
                                        log_file.info(f"{message}")
                                        
                                        DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
                                        if DB_RETURN["error"] :
                                            log_console.error(DB_RETURN["return"])
                                            log_file.error(DB_RETURN["return"])
                                            MESSAGE_EVENT = f"Erreur d'enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                            complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                        else :
                                            log_file.info(f"{DB_RETURN["return"]}")
                                            MESSAGE_EVENT = f"Enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                            complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                    else :
                                        
                                        query_ECM_PARAM = f"update [{db_database}].dbo.ECM_KITYDO set fldIdxTyp = 'MULTI' where kindid = '{E_TYPname}' "
                                        
                                        message = f"QUERY > {query_ECM_PARAM}"
                                        log_console.debug(f"{message}")
                                        message = f"Multi dossier sur Nature {E_TYPname}"
                                        log_console.info(f"{message}")
                                        log_file.info(f"{message}")
                                        
                                        DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
                                        if DB_RETURN["error"] :
                                            log_console.error(DB_RETURN["return"])
                                            log_file.error(DB_RETURN["return"])
                                            MESSAGE_EVENT = f"Erreur d'enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                            complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                        else :
                                            log_file.info(f"{DB_RETURN["return"]}")
                                            MESSAGE_EVENT = f"Enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                            complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                            
        for Environment in root.findall('Environment'):
            for Base in Environment.findall('Base'):
                for L_FLD in Base.findall('L_FLD'):
                    for E_FLD in L_FLD.findall('E_FLD'):
                        for E_SUB in E_FLD.findall('E_SUB'):
                            for L_TYP in E_SUB.findall('L_TYP'):
                                for E_TYP in L_TYP.findall('E_TYP'):
                                    E_TYPname = E_TYP.get('nme')
                                    E_TYPmul = E_TYP.get('mul')
                                    if E_TYPmul == "2" :
                                        if db_type == 'DB2':
                                            
                                            query_ECM_PARAM = f"update {db_database}.ECM_KITYDO set FLDIDXTYP = 'MULTI' where KINDID = '{E_TYPname}' "
                                            message = f"QUERY > {query_ECM_PARAM}"
                                            log_console.debug(f"{message}")
                                            message = f"Multi dossier sur Nature {E_TYPname}"
                                            log_console.info(f"{message}")
                                            log_file.info(f"{message}")
                                            
                                            DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
                                            if DB_RETURN["error"] :
                                                log_console.error(DB_RETURN["return"])
                                                log_file.error(DB_RETURN["return"])
                                                MESSAGE_EVENT = f"Erreur d'enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                            else :
                                                log_file.info(f"{DB_RETURN["return"]}")
                                                MESSAGE_EVENT = f"Enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                        else :
                                            
                                            query_ECM_PARAM = f"update [{db_database}].dbo.ECM_KITYDO set fldIdxTyp = 'MULTI' where kindid = '{E_TYPname}' "
                                            
                                            message = f"QUERY > {query_ECM_PARAM}"
                                            log_console.debug(f"{message}")
                                            message = f"Multi dossier sur Nature {E_TYPname}"
                                            log_console.info(f"{message}")
                                            log_file.info(f"{message}")
                                            
                                            DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
                                            if DB_RETURN["error"] :
                                                log_console.error(DB_RETURN["return"])
                                                log_file.error(DB_RETURN["return"])
                                                MESSAGE_EVENT = f"Erreur d'enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                            else :
                                                log_file.info(f"{DB_RETURN["return"]}")
                                                MESSAGE_EVENT = f"Enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
        for Environment in root.findall('Environment'):
            for Base in Environment.findall('Base'):
                for L_FLD in Base.findall('L_FLD'):
                    for E_FLD in L_FLD.findall('E_FLD'):
                        for L_SUB in E_FLD.findall('L_SUB'):
                            for E_SUB in L_SUB.findall('E_SUB'):
                                for L_TYP in E_SUB.findall('L_TYP'):
                                    for E_TYP in L_TYP.findall('E_TYP'):
                                        E_TYPname = E_TYP.get('nme')
                                        E_TYPmul = E_TYP.get('mul')
                                        if E_TYPmul == "2" :
                                            if db_type == 'DB2':
                                                
                                                query_ECM_PARAM = f"update {db_database}.ECM_KITYDO set FLDIDXTYP = 'MULTI' where KINDID = '{E_TYPname}' "
                                                message = f"QUERY > {query_ECM_PARAM}"
                                                log_console.debug(f"{message}")
                                                message = f"Multi dossier sur Nature {E_TYPname}"
                                                log_console.info(f"{message}")
                                                log_file.info(f"{message}")
                                                
                                                DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
                                                if DB_RETURN["error"] :
                                                    log_console.error(DB_RETURN["return"])
                                                    log_file.error(DB_RETURN["return"])
                                                    MESSAGE_EVENT = f"Erreur d'enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                    complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                                else :
                                                    log_file.info(f"{DB_RETURN["return"]}")
                                                    MESSAGE_EVENT = f"Enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                    complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                            else :
                                                
                                                query_ECM_PARAM = f"update [{db_database}].dbo.ECM_KITYDO set fldIdxTyp = 'MULTI' where kindid = '{E_TYPname}' "
                                                
                                                message = f"QUERY > {query_ECM_PARAM}"
                                                log_console.debug(f"{message}")
                                                message = f"Multi dossier sur Nature {E_TYPname}"
                                                log_console.info(f"{message}")
                                                log_file.info(f"{message}")
                                                
                                                DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
                                                if DB_RETURN["error"] :
                                                    log_console.error(DB_RETURN["return"])
                                                    log_file.error(DB_RETURN["return"])
                                                    MESSAGE_EVENT = f"Erreur d'enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                    complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
                                                else :
                                                    log_file.info(f"{DB_RETURN["return"]}")
                                                    MESSAGE_EVENT = f"Enregistrement du Multi dossier sur la Nature {E_TYPname}"
                                                    complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
    except Exception as e:
        print(f"ERROR > {e}")
        message = f"ERROR > {e}"
        log_console.info(f"{message}")
        log_file.info(f"{message}")
        MESSAGE_EVENT = f"Erreur de traitement du fichier XML parameter"
        complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Multi",MESSAGE_EVENT)
        
    DB_RETURN = DB_CONNEXION.close() # Ferme le co SGBD
    
    message = "Fin du service Sans erreurs"
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    
    complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Init",f"{message}")
    
    if not contrainte_is_service : 
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
        