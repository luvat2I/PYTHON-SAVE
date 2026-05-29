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

sys.path.append('class')  # ou sys.path.append('./class')
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
    
    log_file.info(f"Début du traitement de correction des X1")
    log_console.info(f"Début du traitement de correction des X1")
    
    db_query_data = f"select [framework_security_business_data].objectType,[framework_security_business_data_expression].dataValue,[framework_security_business_data_expression].id, *  from [{db_database}].dbo.[framework_security_business_data_expression] left join [framework_security_business_data] on [framework_security_business_data_expression].businessDataId = [framework_security_business_data].id"
    
    DB_RETURN_DATA = DB_CONNEXION.execute_query(db_query_data)
    
    from collections import Counter
    
    # for row in DB_RETURN_DATA["return"]:
        # print(f"{row.dataValue} {row.objectType} {row.id}")
    
    seen_combinations = Counter()
    for row in DB_RETURN_DATA["return"]:
        key = (row.dataValue, row.objectType)
        seen_combinations[key] += 1

    # Afficher uniquement les combinaisons uniques
    for row in DB_RETURN_DATA["return"]:
        key = (row.dataValue, row.objectType)
        if seen_combinations[key] == 1:
            if row.objectType == "Document" :
                query_ECM_PARAM = f"UPDATE [{db_database}].dbo.ecm_param set [ecm_param].br_id_document = '{row.businessDataRuleId}' where param_id = '{row.dataValue}' and param_type = '{row.dataCode}'"
            if row.objectType == "Folder" :
                query_ECM_PARAM = f"UPDATE [{db_database}].dbo.ecm_param set [ecm_param].br_id_folder = '{row.businessDataRuleId}' where param_id = '{row.dataValue}' and param_type = '{row.dataCode}'"
            message = f"QUERY > {query_ECM_PARAM}"
            log_console.debug(f"{message}")
            message = f"Ajout de la règle {row.businessDataRuleId} sur {row.dataValue} et {row.dataCode}"
            log_console.info(f"{message}")
            log_file.info(f"{message}")
            DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
            if DB_RETURN["error"] :
                log_console.error(DB_RETURN["return"])
                log_file.error(DB_RETURN["return"])
                MESSAGE_EVENT = f"Erreur d'enregistrement de la règle {row.businessDataRuleId} sur la règle X1 de {row.dataValue} et {row.dataCode}"
                complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"X1",MESSAGE_EVENT)
            else :
                log_file.info(f"{DB_RETURN["return"]}")
                MESSAGE_EVENT = f"Enregistrement de la règle {row.businessDataRuleId} sur la règle X1 de {row.dataValue} et {row.dataCode}"
                complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"X1",MESSAGE_EVENT)
    
    
    log_file.info(f"Fin du traitement de correction des X1")
    log_console.info(f"Fin du traitement de correction des X1")
    
    log_file.info(f"-------")
    log_console.info(f"-------")
    
    log_file.info(f"Début du traitement de correction des mots clef UNIQUE dans ECM_PARAM")
    log_console.info(f"Début du traitement des corrections des mots clef UNIQUE dans ECM_PARAM")
    
    if db_type == 'DB2':
        query_ECM_PARAM = f"""update {sgbd_database}.ECM_PARAM set PARAM_DATA = replace(param_data , ',"unique":true' , ',"unique":false') where param_type = 'DATATYPE' and PARAM_DATA like '%"unique":true%' """
    else :
        query_ECM_PARAM = f"""update [{db_database}].dbo.ecm_param set param_data = replace(param_data , ',"unique":true' , ',"unique":false') where param_type = 'DATATYPE' and param_data like '%"unique":true%' """
        
    message = f"QUERY > {query_ECM_PARAM}"
    log_console.debug(f"{message}")
    message = f"Enregistrement "
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    
    DB_RETURN = DB_CONNEXION.execute_query_save(query_ECM_PARAM)
    if DB_RETURN["error"] :
        log_console.error(DB_RETURN["return"])
        log_file.error(DB_RETURN["return"])
        MESSAGE_EVENT = f"Erreur d'enregistrement des corrections des mots clef UNIQUE dans ECM_PARAM"
        complement.solr_event_echoue(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Unique",MESSAGE_EVENT)
    else :
        log_file.info(f"{DB_RETURN["return"]}")
        MESSAGE_EVENT = f"Enregistrement des corrections des mots clef UNIQUE dans ECM_PARAM"
        complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Unique",MESSAGE_EVENT)
    
    log_file.info(f"Fin du traitement suppression des UNIQUE.")
    log_console.info(f"Fin du traitement suppression des UNIQUE.")
    
    DB_RETURN = DB_CONNEXION.close() # Ferme le co SGBD
    
    message = "Fin du service Sans erreurs"
    log_console.info(f"{message}")
    log_file.info(f"{message}")
    
    complement.solr_event_traite(SOLR_LOG,log_sorl,log_console,log_file,CATEGORIE_EVENT,CODE_EVENT,"Init",f"{message}")
    
    if not contrainte_is_service : 
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
        