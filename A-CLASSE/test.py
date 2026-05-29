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

#----------- IMPORT LIB EXTERNE
import luva_lic         #--licence
import luva_code        #--luva
import keycloak_suite   #--Keycloak
import group_gestion    #--Youdoc Gestion
import complement       #--complements
import solr_event       #--creation des event solr

import luva_file        #--luva_file
import luva_console     #--luva_file

#----------- LICENCES
licence_base = "9736234122426398669" # 2026

#----------- Config
contrainte_active_ini = True        # Doit faire la vérification du fichier .ini        : True / False
contrainte_contient_luva = False    # Doit faire la vérification du nom du programme    : True / False
contrainte_active_lic = False        # Doit faire la vérification de la license          : True / False
contrainte_is_service = True        # Doit être un service                              : True / False 

#----------- Active le MOD-DEV 
MODEDEV = False
if contrainte_active_lic and not MODEDEV : contrainte_active_ini = True # Secu recup ini pour la licence

if MODEDEV :
    print(f"> LUVA > MODEDEV > is active")

#----------- Gestion du INI
ini_filename = luva_code.get_ini_path()
if MODEDEV : print(f"> LUVA > MODEDEV > ini_filename : {ini_filename}")

nom_programme = luva_code.get_nom_programme()
if MODEDEV : print(f"> LUVA > MODEDEV > nom_programme : {nom_programme}")

contient_service = luva_code.nom_programme_contient(nom_programme,"SERVICE")
if contient_service :
    traitement_type = "SERVICE"
else:
    traitement_type = "EXE"
if MODEDEV : print(f"> LUVA > MODEDEV > traitement_type : {traitement_type}")

#----------- Gestion de contient luva
contient_luva = luva_code.nom_programme_contient(nom_programme,"LUVA")
if contrainte_contient_luva and not contient_luva :
    if not contrainte_is_service :
        print(f"ERROR : Nom du programme non conforme")
        input()
    sys.exit(1)

#----------- Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#----------- Lecture du fichier ini
if contrainte_active_ini :
    config = configparser.ConfigParser()
    try:
        if not os.path.exists(ini_filename):
            if not contrainte_is_service :
                if MODEDEV : print(f"> LUVA > MODEDEV > ini_filename : excessible")
            sys.exit(1)  # ferme lapp
        else :
            if not contrainte_is_service :
                if MODEDEV : print(f"> LUVA > MODEDEV > ini_filename : not excessible")
            config.read(f'{ini_filename}')
            if not config.sections():  # Vérifie si le fichier ini est vide
                if not contrainte_is_service :
                    print(f"Le fichier de configuration '{ini_filename}' est vide.")
                sys.exit(1)  # ferme lapp
    except Exception as e:
        if not contrainte_is_service :
            print(f"erreur de traitement du fichier .ini : '{e}'")
        sys.exit(1)  # ferme lapp

#----------- Gestion de la licence
if contrainte_active_lic :
    licence_valide = False
    
    licence = luva_code.get_licence(config)
    if licence_base and licence == "ERROR" :
        licence = licence_base
    
    if MODEDEV : print(f"> LUVA > MODEDEV > {licence}")
    
    LUVA_VERIF_LICENCE = luva_code.get_param(config,'LUVA','LICENCE')
    if not LUVA_VERIF_LICENCE["error"] :
        licence = LUVA_VERIF_LICENCE["return"]
    
    try:
        licence_valide = luva_lic.valide_licence(licence,MODEDEV)
    except Exception as e:
        licence_valide = False
        
    if not licence_valide :
        if not contrainte_is_service :
            print(f"ERREUR PYTHON INCONNU")
            input()
        sys.exit(1)  # Quitte l'EXCEL_APPLICATION avec un code d'erreur
    elif MODEDEV :
        print(f"> LUVA > MODEDEV > VALIDE")
        
def split_prefix_and_uuid(data: str):
    """
    doit verifié si il s'agit d'un '<group>_<uuid>'.
    """
    if len(data) < 38:  # au minimum "a_XXXXXXXX-...." (1 + '_' + 36)
        return {
            "error": True,
            "groupe": None,
            "uuid": None
        }
    
    if '_' not in data:
        return {
            "error": True,
            "groupe": None,
            "uuid": None
        }
    prefix, sep, candidate = data.rpartition('_')
    
    if not prefix or len(candidate) != 36:
        return {
            "error": True,
            "groupe": None,
            "uuid": None
        }
    
    try:
        parsed = uuid.UUID(candidate)
    except (ValueError, AttributeError):
        return {
            "error": True,
            "groupe": None,
            "uuid": None
        }
    if str(parsed) != candidate.lower():
        return {
            "error": True,
            "groupe": None,
            "uuid": None
        }

    return {
        "error": False,
        "groupe": prefix,
        "uuid": candidate
    }
        
#-------------------------------------------------------
#-----------                traitement
#-------------------------------------------------------

def timer():
    
    if MODEDEV : print(f"> 1 > debut du traitement timer")
    
    global thread_traitement_nb
    threads = []
    thread_traitement_nb = 0
    thread_traitement = 0
    
    valide = complement.valideTIMER(SERVICE_HEURE,SERVICE_MINUTE)
    minute_time_before = 0
    hour_time_before = 0
    
    while True :
        service_valide = False
        
        if not contrainte_is_service : print(f"INFO {service_valide} {thread_traitement_nb}")
        minute_time = datetime.now().minute
        hour_time = datetime.now().hour
        
        if minute_time != minute_time_before or hour_time != hour_time_before :
            service_valide = valide.getvalide(hour_time,minute_time)
        
        if not contrainte_is_service : print(f"service_valide = {service_valide} / {hour_time}:{minute_time} / {SERVICE_HEURE} et {SERVICE_MINUTE}")
        
        if thread_traitement_nb < 1 and service_valide :
            if not contrainte_is_service : print("lance")
            thread = threading.Thread(target=traitement, args=(), name =f"thread_traitement_{thread_traitement}")
            threads.append(thread)
            thread.start()
            thread_traitement += 1
            thread_traitement_nb += 1
        
        minute_time_before = minute_time
        hour_time_before = hour_time
        time.sleep(60)
    if not contrainte_is_service : print(f"> 1 > fin du traitement timer")

def traitement():
    
    global thread_traitement_nb
    if not contrainte_is_service : print(f"> 1 > debut du traitement par thread")
        
    name_thread_actuel = ""
    
    try:
        thread_actuel = threading.current_thread()
        name_thread_actuel = f"th > {thread_actuel} > "
    except Exception as e:
        name_thread_actuel = ""
        
    if not contrainte_is_service : print(f"> 1 >  {name_thread_actuel}")
        
    try:
        if not contrainte_is_service : print(f"> 1 >  {name_thread_actuel} > verif token expire")
        YOUDOC_TOKEN_EXPIRE = YOUDOC_CONNEXION.token_valide()
        if YOUDOC_TOKEN_EXPIRE["error"] :
            if not contrainte_is_service : print(YOUDOC_TOKEN_EXPIRE["return"])
            YOUDOC_TOKEN_EXPIRE_token = YOUDOC_TOKEN_EXPIRE["return"]
        else :
            YOUDOC_TOKEN_EXPIRE_token = YOUDOC_TOKEN_EXPIRE["return"]
            
        if not contrainte_is_service : print(f"> 1 >  {name_thread_actuel} > YOUDOC_TOKEN_EXPIRE_token = {YOUDOC_TOKEN_EXPIRE_token}")
        
        if YOUDOC_TOKEN_EXPIRE_token :
            if not contrainte_is_service : print(f"> 1 >  {name_thread_actuel} > Recup new token")
            YOUDOC_TOKEN = YOUDOC_CONNEXION.recup_barear()
            if YOUDOC_TOKEN["error"] :
                if not contrainte_is_service :
                    print(YOUDOC_TOKEN["return"])
                    print("Appuyer sur entrer pour fermer")
                    input()
                sys.exit(1)
            else :
                if DEBUG :
                    if not contrainte_is_service :
                        print(f"> 1 > Token : {YOUDOC_TOKEN["return"]}")
            if not contrainte_is_service :
                print(f"> 1 >  {name_thread_actuel} > TOKEN YD renouvellé ")
        
        YOUDOC_VERIF_group = YOUDOC_CONNEXION.list_group()
        
        
        
        # TENANT_EVENT = "001"
        # minute_time = datetime.now().minute
        # hour_time = datetime.now().hour
        # minute_time = datetime.now().second
        # micro_time = datetime.now().microsecond // 1000
        
        # ID_EVENT = "S115801"
        # USER_EVENT = "YOUDOC"
        # YEAR_EVENT = "2026"
        # MONTH_EVENT = "5"
        # DAY_EVENT = "21"
        # HOUR_EVENT = "13"
        # MINUTE_EVENT = "23"
        # SECONDE_EVENT = "10"
        
        # SERVEUR = "2026"
        # FRAMEWORK_EVENT = "YOUDOC-SYNCHRO"
        # LOGICIEL_EVENT = "YOUDOC SYNCHRO"
        # SOFTWARE_EVENT = "YOUDOC-SYNCHRO"
        # CATEGORIE_EVENT = "SERVICE"
        
        # TYPE_EVENT = "MAJ"
        # objectTypeDescription_EVENT = "MAJ"
        
        # SUB_EVENT = "Creation"
        # STATUS_EVENT = "Réussi"
        # MESSAGE_EVENT = "Création d'un groupe"
        
        
        
        
        
        
        
        
        
        
        
        
        if YOUDOC_VERIF_group["error"] :
            if not contrainte_is_service :
                print(f"> 1 >  {name_thread_actuel} > recupération des groupes = KO ")
        else :
            if not contrainte_is_service :
                print(f"> 1 >  {name_thread_actuel} > recupération des groupes = OK ")
                #print(f"> 1 >  {name_thread_actuel} > recupération des groupes = {YOUDOC_VERIF_group} ")
            YOUDOC_VERIF_group = YOUDOC_VERIF_group["return"]
            lst = ast.literal_eval(YOUDOC_VERIF_group)
            
            for item in lst:
                
                if not contrainte_is_service : print(f"> 1 >  {name_thread_actuel} > {item.get("name")} / {item.get("displayName")}  ")
                verif = split_prefix_and_uuid(item.get("displayName"))
                if not verif["error"] :
                    groupe = verif["groupe"]
                    role = f"ydg_{YOUDOC_TENANT}_{verif["groupe"]}"
                    
                    uuid = verif["uuid"]
                    
                    if not contrainte_is_service :
                        print(f"doit créer le role '{role}' ")
                        print(f"doit créer le mapper '{groupe}' avec le uuid '{uuid}' pour le role '{role}'")
                        
                    KEYCLOAK_TOKEN_EXPIRE = KEYCLOAK_CONNECT.token_valide()
                    if KEYCLOAK_TOKEN_EXPIRE["error"] :
                        if not contrainte_is_service : print(KEYCLOAK_TOKEN_EXPIRE["return"])
                        KEYCLOAK_TOKEN_EXPIRE_token = KEYCLOAK_TOKEN_EXPIRE["return"]
                    else :
                        KEYCLOAK_TOKEN_EXPIRE_token = KEYCLOAK_TOKEN_EXPIRE["return"]
                    if DEBUG : print(f"> 4 > Token KC : {KEYCLOAK_TOKEN_EXPIRE}")
                    if KEYCLOAK_TOKEN_EXPIRE_token :
                        if not contrainte_is_service : print(f"> 4 >             > TOKEN KC expiré ")
                        KEYCLOAK_TOKEN = KEYCLOAK_CONNECT.recup_barear()
                        if KEYCLOAK_TOKEN["error"] :
                            if not contrainte_is_service :
                                print(KEYCLOAK_TOKEN["return"])
                                print("Appuyer sur entrer pour fermer")
                                input()
                            sys.exit(1)
                        else :
                            if DEBUG :
                                print(f"> 4 > Token : {KEYCLOAK_TOKEN["return"]}")
                        if not contrainte_is_service : print(f"> 4 >             > TOKEN KC renouvellé ")
                        
                        
                        
                    KEYCLOAK_VERIF_ROLE = KEYCLOAK_CONNECT.id_role(role)
                    if KEYCLOAK_VERIF_ROLE["error"] :
                        role_exist = False
                    else :
                        role_exist = True
                    
                    if not role_exist :
                        KEYCLOAK_ADMIN_ROLE = KEYCLOAK_CONNECT.admin_role(role,ACTION)
                        if KEYCLOAK_ADMIN_ROLE["error"] :
                            if not contrainte_is_service :
                                print(f"> 4 > {role} > {KEYCLOAK_ADMIN_ROLE["return"]}")
                                print("Appuyer sur entrer pour continuer")
                                input()
                        else :
                            if not contrainte_is_service : 
                                print(f"> 4 > {role} > {KEYCLOAK_ADMIN_ROLE["return"]}")
                            
                            
                    KEYCLOAK_VERIF_MAPPER = KEYCLOAK_CONNECT.id_mapper(IDP_ALIAS,groupe)
                    if KEYCLOAK_VERIF_MAPPER["error"] :
                        mapper_exist = False
                    else :
                        mapper_exist = True
                    
                    if not mapper_exist :
                        KEYCLOAK_ADMIN_MAPPER = KEYCLOAK_CONNECT.admin_mapper(IDP_ALIAS,CALCUL_CLIENT,groupe,role,uuid,"",ACTION)
                        if KEYCLOAK_ADMIN_MAPPER["error"] :
                            if not contrainte_is_service : print(KEYCLOAK_ADMIN_MAPPER["return"])
                        else :
                            if not contrainte_is_service : 
                                if DEBUG : print(f"{KEYCLOAK_ADMIN_MAPPER["return"]}")
                                print(f"> 4 > {groupe} > {KEYCLOAK_ADMIN_MAPPER["return"]}")
                    
    except Exception as e:
        if not contrainte_is_service : print(f"ERROR: {e}")
        thread_traitement_nb = thread_traitement_nb - 1
        
    if not contrainte_is_service : print(f"> 1 > Fin du traitement par thread")
    thread_traitement_nb = thread_traitement_nb - 1

#-------------------------------------------------------
#-----------                MAIN
#-------------------------------------------------------

if __name__ == "__main__":
    
    #----------- LOG FILE
    
    log_file = luva_file.GestionnaireLogFile(
        nom_dossier=r"D:\PYTHON\classe\logfile",
        nom_fichier="mon_app.log",
        niveau="INFO",
        max_bytes=2*1024*1024,  # 2 Mo
        backup_count=5
    )
    
    log_file.info("Mon application")
    log_file.error("Erreur détectée")
    
    
    log_console = luva_console.Logger(luva_console.LogLevel.DEBUG)

    log_console.debug("Ceci ne s'affichera pas")
    log_console.info("Application démarrée")
    log_console.warning("Attention : mémoire faible")
    log_console.error("Erreur lors de la connexion")
    log_console.critical("Système en panne !")
    
    
    
    
    SOLR_hostname="YDGLUVA24Q:8984"
    SOLR_username="default-svc-usr"
    SOLR_password="zYDdjrIZ2M1jbgv"
    SOLR_tenant="001"
    VERIF_SSL=False
    
    
    
    CODE_EVENT = "S"
    TENANT_EVENT = "001"
    USER_EVENT = "default-svc-usr"
    
    FRAMEWORK_EVENT = "YOUDOC-SYNCHRO"
    
    LOGICIEL_EVENT = "KEYCLOAK"
    SOFTWARE_EVENT = "KEYCLOAK"
    
    CATEGORIE_EVENT = "SYNCHRO"
    
    TYPE_EVENT = "ROLE"
    objectTypeDescription_EVENT = "ROLE"
    
    SUB_EVENT = "ROLE"  # "ROLE" / "MAPPER"

    MESSAGE_EVENT = "Création du groupe test avec id 48"
    
    
    
    log_sorl = solr_event.SolrEventPublisher(
        f"https://{SOLR_hostname}",
        SOLR_tenant,
        SOLR_username,
        SOLR_password,
        VERIF_SSL
    )
    
    result_connexion = log_sorl.test_connection()
    log_console.debug(result_connexion)
    
    result_connexion = log_sorl.init_event_info(TENANT_EVENT,USER_EVENT,FRAMEWORK_EVENT,LOGICIEL_EVENT,SOFTWARE_EVENT,CODE_EVENT)
    log_console.debug(result_connexion)
    
    result_connexion = log_sorl.en_cours(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
    log_console.debug(result_connexion)
    
    result_connexion = log_sorl.traite(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
    log_console.debug(result_connexion)
    
    result_connexion = log_sorl.echoue(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
    log_console.debug(result_connexion)