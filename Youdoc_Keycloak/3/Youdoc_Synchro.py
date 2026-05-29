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
import luva_file        #--luva_file
import luva_console     #--luva_console
import solr_event       #--creation des event solr

#----------- LICENCES
licence_base = "9736234122426398669" # 2026

#----------- Config
contrainte_active_ini = True        # Doit faire la vérification du fichier .ini        : True / False
contrainte_contient_luva = False    # Doit faire la vérification du nom du programme    : True / False
contrainte_active_lic = False        # Doit faire la vérification de la license         : True / False
contrainte_is_service = True        # Doit être un service                              : True / False 

#----------- Active le MOD-DEV 
MODEDEV = True
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
    config = configparser.ConfigParser()
    try:
        if not os.path.exists(ini_filename):
            log_console.error(f"fichier ini : inaccessible")
            log_file.error(f"fichier ini : inaccessible")
            if not contrainte_is_service : input()
            sys.exit(1)  # ferme lapp
        else :
            log_console.info(f"fichier ini : accessible")
            log_file.info(f"fichier ini : accessible")
            config.read(f'{ini_filename}')
            if not config.sections():  # Vérifie si le fichier ini est vide
                log_console.error(f"Le fichier de configuration '{ini_filename}' est vide.")
                log_file.error(f"Le fichier de configuration '{ini_filename}' est vide.")
                if not contrainte_is_service : input()
                sys.exit(1)  # ferme lapp
    except Exception as e:
        log_console.error(f"erreur de traitement du fichier .ini : '{e}'")
        log_file.error(f"erreur de traitement du fichier .ini : '{e}'")
        if not contrainte_is_service : input()
    
    
    print("print(CONFIG_INI)")
    
    CONFIG_INI_PARAM = complement.get_param(config,'INI','CONFIG_INI')
    if CONFIG_INI_PARAM["error"] :
        CONFIG_INI = ""
    else :
        CONFIG_INI = CONFIG_INI_PARAM["return"]
        CONFIG_INI = os.path.join(dossier_courant, CONFIG_INI)
    
    try:
        if CONFIG_INI != "" :
            if not os.path.exists(CONFIG_INI):
                log_console.error(f"fichier ini : inaccessible")
                log_file.error(f"fichier ini : inaccessible")
                if not contrainte_is_service : input()
                sys.exit(1)  # ferme lapp
            else :
                log_console.info(f"fichier ini : accessible")
                log_file.info(f"fichier ini : accessible")
                config.read(f'{CONFIG_INI}')
                if not config.sections():  # Vérifie si le fichier ini est vide
                    log_console.error(f"Le fichier de configuration '{CONFIG_INI}' est vide.")
                    log_file.error(f"Le fichier de configuration '{CONFIG_INI}' est vide.")
                    if not contrainte_is_service : input()
                    sys.exit(1)  # ferme lapp
    except Exception as e:
        log_console.error(f"erreur de traitement du fichier .ini : '{e}'")
        log_file.error(f"erreur de traitement du fichier .ini : '{e}'")
        if not contrainte_is_service : input()

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
    log_console.debug(f" > debut du traitement timer")
    
    global thread_traitement_nb
    threads = []
    thread_traitement_nb = 0
    thread_traitement = 0
    
    valide = complement.valideTIMER(SERVICE_HEURE,SERVICE_MINUTE)
    minute_time_before = 0
    hour_time_before = 0
    
    while True :
        service_valide = False

        minute_time = datetime.now().minute
        hour_time = datetime.now().hour
        
        if minute_time != minute_time_before or hour_time != hour_time_before :
            service_valide = valide.getvalide(hour_time,minute_time)
            log_console.debug(f"service_valide = {service_valide} / {hour_time}:{minute_time} / {SERVICE_HEURE} et {SERVICE_MINUTE}")
            
        if thread_traitement_nb < 1 and service_valide :
            TYPE_EVENT = "Service"
            objectTypeDescription_EVENT = "Service"
            SUB_EVENT = "Service"  # "Service" / "Service"
            MESSAGE_EVENT = "Lancement de la synchronisation des groupes"
            log_console.info(f"{MESSAGE_EVENT}")
            log_file.info(f"{MESSAGE_EVENT}")
            RESULT_SOLR = log_sorl.en_cours(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
            if RESULT_SOLR["error"] :
                log_file.error(f"Enregistrement event solr - {RESULT_SOLR["return"]}")
            
            thread = threading.Thread(target=traitement, args=(), name =f"thread_traitement_{thread_traitement}")
            threads.append(thread)
            thread.start()
            thread_traitement += 1
            thread_traitement_nb += 1
            
        minute_time_before = minute_time
        hour_time_before = hour_time
        message = f"Wait for 60"
        log_console.debug(f"{message}")
        time.sleep(60)
        
    log_console.debug(f" > Fin du traitement timer")

def traitement():
    
    log_console.debug(f" > debut du traitement des ajouts")
    global KEYCLOAK_ID_CLIENT_VALIDE
    global KEYCLOAK_ID_PROVIDER_VALIDE
    global thread_traitement_nb
    name_thread_actuel = " > th > thread >"
    
    try:
        thread_actuel = threading.current_thread()
        name_thread_actuel = f" > th > {thread_actuel} >"
    except Exception as e:
        name_thread_actuel = " > th > thread >"
    
    
    log_console.debug(f"{name_thread_actuel}")
    
    message = f"{name_thread_actuel} verif token KC"
    log_console.debug(f" > {name_thread_actuel} > {message}")
    
    KEYCLOAK_TOKEN_EXPIRE = KEYCLOAK_CONNECT.token_valide()
    if KEYCLOAK_TOKEN_EXPIRE["error"] :
        KEYCLOAK_TOKEN_EXPIRE_token = True
        message = f"{name_thread_actuel} {KEYCLOAK_TOKEN_EXPIRE["return"]}"
        log_console.error(f"{message}")
        log_file.error(f"{message}")
    else :
        KEYCLOAK_TOKEN_EXPIRE_token = KEYCLOAK_TOKEN_EXPIRE["return"]
        
    message = f"{name_thread_actuel} Token KC : {KEYCLOAK_TOKEN_EXPIRE}"
    log_console.debug(f"{message}")
    
    if KEYCLOAK_TOKEN_EXPIRE_token :
        message = f"{name_thread_actuel} TOKEN KC expiré"
        log_console.info(f"{message}")
        log_file.info(f"{message}")
        KEYCLOAK_TOKEN = KEYCLOAK_CONNECT.recup_token_barear()
        if KEYCLOAK_TOKEN["error"] :
            message = f"{name_thread_actuel} {KEYCLOAK_TOKEN["return"]}"
            log_console.error(f"{message}")
            log_file.error(f"{message}")
        else :
            message = f"{name_thread_actuel} {KEYCLOAK_TOKEN["return"]}"
            log_console.debug(f"{message}")
            
            message = f"{name_thread_actuel} TOKEN KC renouvellé"
            log_console.info(f"{message}")
            log_file.info(f"{message}")
    
    
    
    if not KEYCLOAK_ID_CLIENT_VALIDE :
        try :
            KEYCLOAK_ID_CLIENT = KEYCLOAK_CONNECT.recup_client_id(CALCUL_CLIENT)
            if KEYCLOAK_ID_CLIENT["error"] :
                message = f"{name_thread_actuel} {KEYCLOAK_ID_CLIENT["return"]}"
                log_console.error(f"{message}")
                log_file.error(f"{message}")
                KEYCLOAK_ID_CLIENT_VALIDE = False
            else :
                message = f"{name_thread_actuel} Connexion ID CLIENT = OK"
                log_console.info(f"{message}")
                log_file.info(f"{message}")
                KEYCLOAK_ID_CLIENT_VALIDE = True
                if is_debug :
                    log_console.debug(f"----------------------------------------------------")
                    log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
                    log_console.debug(f" > ++ ID CLIENT = {KEYCLOAK_ID_CLIENT["return"]}")
        except Exception as e:
            message = f"{name_thread_actuel} {e}"
            log_console.error(f"{message}")
            log_file.error(f"{message}")
            KEYCLOAK_ID_CLIENT_VALIDE = False
            
    if not KEYCLOAK_ID_PROVIDER_VALIDE :
        try :
            KEYCLOAK_ID_PROVIDER = KEYCLOAK_CONNECT.recup_identity_provider(IDP_ALIAS)
            if KEYCLOAK_ID_PROVIDER["error"] :
                message = f"{name_thread_actuel} {KEYCLOAK_ID_PROVIDER["return"]}"
                log_console.error(f"{message}")
                log_file.error(f"{message}")
                KEYCLOAK_ID_PROVIDER_VALIDE = False
            else :
                message = f"{name_thread_actuel} Connexion ID PROVIDER = OK"
                log_console.info(f"{message}")
                log_file.info(f"{message}")
                KEYCLOAK_ID_PROVIDER_VALIDE = True
                if is_debug :
                    log_console.debug(f"----------------------------------------------------")
                    log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
                    log_console.debug(f" > ++ ID PROVIDER = {KEYCLOAK_ID_PROVIDER["return"]}") 
        
        except Exception as e:
            message = f"{name_thread_actuel} {e}"
            log_console.error(f"{message}")
            log_file.error(f"{message}")
            KEYCLOAK_ID_PROVIDER_VALIDE = False
        
    try:
        message = f"{name_thread_actuel} verif token YD"
        log_console.debug(f"{message}")
        
        YOUDOC_TOKEN_EXPIRE = YOUDOC_CONNEXION.token_valide()
        if YOUDOC_TOKEN_EXPIRE["error"] :
            message = f"{name_thread_actuel} Token YOUDOC expiré"
            log_console.error(f"{message}")
            log_file.error(f"{message}")
            YOUDOC_TOKEN_EXPIRE_token = YOUDOC_TOKEN_EXPIRE["return"]
            TOKEN_valide = False
        else :
            YOUDOC_TOKEN_EXPIRE_token = YOUDOC_TOKEN_EXPIRE["return"]
            TOKEN_valide = True
            
        log_console.info(f"{name_thread_actuel} YOUDOC_TOKEN_EXPIRE_token = {YOUDOC_TOKEN_EXPIRE_token}")
        
        if YOUDOC_TOKEN_EXPIRE_token :
            message = f"{name_thread_actuel} Renouvellement du token YOUDOC"
            log_console.error(f"{message}")
            log_file.error(f"{message}")
            YOUDOC_TOKEN = YOUDOC_CONNEXION.recup_barear()
            if YOUDOC_TOKEN["error"] :
                message = f"{name_thread_actuel} Renouvellement du token YOUDOC impossible : {YOUDOC_TOKEN["return"]}"
                log_console.error(f"{message}")
                log_file.error(f"{message}")
                TOKEN_valide = False
            else :
                TOKEN_valide = True
                message = f"{name_thread_actuel} Renouvellement du token YOUDOC ok"
                log_console.info(f"{message}")
                log_file.info(f"{message}")
                if DEBUG :
                    log_console.debug(f"{name_thread_actuel} Token : {YOUDOC_TOKEN["return"]}")
        
        
        # ici
        
        if KEYCLOAK_ID_PROVIDER_VALIDE and KEYCLOAK_ID_CLIENT_VALIDE :
        
            YOUDOC_VERIF_group = YOUDOC_CONNEXION.list_group()
            if YOUDOC_VERIF_group["error"] :
                message = f"{name_thread_actuel} recupération des groupes = KO : {YOUDOC_VERIF_group["error"]}"
                log_console.error(f"{message}")
                log_file.error(f"{message}")
                TYPE_EVENT = "Service"
                objectTypeDescription_EVENT = "Service"
                SUB_EVENT = "Groupe utilisateur"  # "Service" / "Service"
                MESSAGE_EVENT = f"recupération des groupes YOUDOC KO"
                
                RESULT_SOLR = log_sorl.echoue(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
                if RESULT_SOLR["error"] :
                    message = f"{name_thread_actuel} Enregistrement event solr - {RESULT_SOLR["return"]}"
                    log_console.error(f"{message}")
                    log_file.error(f"{message}")
                print("fini")   
            else :
                message = f"{name_thread_actuel} recupération des groupes = OK"
                log_console.error(f"{message}")
                log_file.error(f"{message}")
                
                TYPE_EVENT = "Service"
                objectTypeDescription_EVENT = "Service"
                SUB_EVENT = "Groupe utilisateur"  # "Service" / "Service"
                MESSAGE_EVENT = f"Recupération des groupes YOUDOC OK"
                
                RESULT_SOLR = log_sorl.traite(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
                if RESULT_SOLR["error"] :
                    message = f"{name_thread_actuel} Enregistrement event solr - {RESULT_SOLR["return"]}"
                    log_console.error(f"{message}")
                    log_file.error(f"{message}")
                    
                YOUDOC_VERIF_group = YOUDOC_VERIF_group["return"]
                lst = ast.literal_eval(YOUDOC_VERIF_group)
                
                for item in lst:
                    
                    message = f"{name_thread_actuel} {item.get("name")} / {item.get("displayName")}"
                    log_console.debug(f"{message}")
                    
                    verif = split_prefix_and_uuid(item.get("displayName"))
                    if not verif["error"] :
                        groupe = verif["groupe"]
                        role = f"ydg_{YOUDOC_TENANT}_{verif["groupe"]}"
                        
                        uuid = verif["uuid"]
                        
                        message = f"{name_thread_actuel} Vérification du role '{role}'"
                        log_console.debug(f"{message}")
                        
                        message = f"{name_thread_actuel} Vérification du mapper '{groupe}' avec le uuid '{uuid}' pour le role '{role}'"
                        log_console.debug(f"{message}")
                            
                        KEYCLOAK_TOKEN_EXPIRE = KEYCLOAK_CONNECT.token_valide()
                        if KEYCLOAK_TOKEN_EXPIRE["error"] :
                            message = f"{name_thread_actuel} {KEYCLOAK_TOKEN_EXPIRE["return"]}"
                            log_console.error(f"{message}")
                            log_file.error(f"{message}")
                        else :
                            KEYCLOAK_TOKEN_EXPIRE_token = KEYCLOAK_TOKEN_EXPIRE["return"]
                            
                        message = f"{name_thread_actuel} Token KC : {KEYCLOAK_TOKEN_EXPIRE}"
                        log_console.debug(f"{message}")
                        
                        if KEYCLOAK_TOKEN_EXPIRE_token :
                            message = f"{name_thread_actuel} TOKEN KC expiré"
                            log_console.info(f"{message}")
                            log_file.info(f"{message}")
                            KEYCLOAK_TOKEN = KEYCLOAK_CONNECT.recup_barear()
                            if KEYCLOAK_TOKEN["error"] :
                                message = f"{name_thread_actuel} {KEYCLOAK_TOKEN["return"]}"
                                log_console.error(f"{message}")
                                log_file.error(f"{message}")
                            else :
                                message = f"{name_thread_actuel} {KEYCLOAK_TOKEN["return"]}"
                                log_console.debug(f"{message}")
                                
                                message = f"{name_thread_actuel} TOKEN KC renouvellé"
                                log_console.info(f"{message}")
                                log_file.info(f"{message}")
                        
                        KEYCLOAK_VERIF_ROLE = KEYCLOAK_CONNECT.id_role(role)
                        if KEYCLOAK_VERIF_ROLE["error"] :
                            role_exist = False
                        else :
                            role_exist = True
                        
                        if not role_exist :
                            
                            message = f"{name_thread_actuel} Création du role {role}"
                            log_console.debug(f"{message}")
                                                       
                            KEYCLOAK_ADMIN_ROLE = KEYCLOAK_CONNECT.admin_role(role,ACTION)
                            if KEYCLOAK_ADMIN_ROLE["error"] :
                                message = f"{name_thread_actuel} Erreur lors de la création du role {role} : {KEYCLOAK_ADMIN_ROLE["return"]} "
                                log_console.error(f"{message}")
                                log_file.error(f"{message}")
                                
                                TYPE_EVENT = "Service"
                                objectTypeDescription_EVENT = "Service"
                                SUB_EVENT = "Role Utilisateur"  # "Service" / "Service"
                                MESSAGE_EVENT = f"Erreur lors de la création du role {role} Voir les logs du service"
                                
                                RESULT_SOLR = log_sorl.echoue(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
                                if RESULT_SOLR["error"] :
                                    message = f"{name_thread_actuel} Enregistrement event solr - {RESULT_SOLR["return"]}"
                                    log_console.error(f"{message}")
                                    log_file.error(f"{message}")
                                
                            else :
                                message = f"{name_thread_actuel} Création du role {role} : {KEYCLOAK_ADMIN_ROLE["return"]}"
                                log_console.info(f"{message}")
                                log_file.info(f"{message}")
                                
                                TYPE_EVENT = "Service"
                                objectTypeDescription_EVENT = "Service"
                                SUB_EVENT = "Role Utilisateur"  # "Service" / "Service"
                                MESSAGE_EVENT = f"Création du role {role}"
                                
                                RESULT_SOLR = log_sorl.traite(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
                                if RESULT_SOLR["error"] :
                                    message = f"{name_thread_actuel} Enregistrement event solr - {RESULT_SOLR["return"]}"
                                    log_console.error(f"{message}")
                                    log_file.error(f"{message}")
                                
                                
                        KEYCLOAK_VERIF_MAPPER = KEYCLOAK_CONNECT.id_mapper(IDP_ALIAS,groupe)
                        if KEYCLOAK_VERIF_MAPPER["error"] :
                            mapper_exist = False
                        else :
                            mapper_exist = True
                        
                        if not mapper_exist :
                            message = f"{name_thread_actuel} Création du mapper {groupe} pour le role {role} avec {uuid}"
                            log_console.debug(f"{message}")
                            
                            
                            
                            
                            KEYCLOAK_ADMIN_MAPPER = KEYCLOAK_CONNECT.admin_mapper(IDP_ALIAS,CALCUL_CLIENT,groupe,role,uuid,"",ACTION)
                            if KEYCLOAK_ADMIN_MAPPER["error"] :
                                message = f"{name_thread_actuel} Erreur lors de la création du mapper {groupe} pour le role {role} avec {uuid} : {KEYCLOAK_ADMIN_MAPPER["return"]} "
                                log_console.error(f"{message}")
                                log_file.error(f"{message}")
                                
                                TYPE_EVENT = "Service"
                                objectTypeDescription_EVENT = "Service"
                                SUB_EVENT = "Mapper Utilisateur"  # "Service" / "Service"
                                MESSAGE_EVENT = f"Erreur lors de la création du mapper {groupe} pour le role {role} avec {uuid} Voir les logs du service"
                                
                                RESULT_SOLR = log_sorl.echoue(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
                                if RESULT_SOLR["error"] :
                                    message = f"{name_thread_actuel} Enregistrement event solr - {RESULT_SOLR["return"]}"
                                    log_console.error(f"{message}")
                                    log_file.error(f"{message}")
                            else :
                                message = f"{name_thread_actuel} Création du mapper {groupe} pour le role {role} avec {uuid} : {KEYCLOAK_ADMIN_MAPPER["return"]} "
                                log_console.error(f"{message}")
                                log_file.error(f"{message}")
                                
                                TYPE_EVENT = "Service"
                                objectTypeDescription_EVENT = "Service"
                                SUB_EVENT = "Mapper Utilisateur"  # "Service" / "Service"
                                MESSAGE_EVENT = f"Création du mapper {groupe} pour le role {role} avec {uuid}"
                                
                                RESULT_SOLR = log_sorl.traite(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
                                if RESULT_SOLR["error"] :
                                    message = f"{name_thread_actuel} Enregistrement event solr - {RESULT_SOLR["return"]}"
                                    log_console.error(f"{message}")
                                    log_file.error(f"{message}")
                                if not contrainte_is_service : 
                                    if DEBUG : print(f"{KEYCLOAK_ADMIN_MAPPER["return"]}")
                                    print(f"> 4 > {groupe} > {KEYCLOAK_ADMIN_MAPPER["return"]}")
                    
        else :
            message = f"{name_thread_actuel} Pas de traitement car soucis de validation de l'IDP {IDP_ALIAS} ou du client {CALCUL_CLIENT}"
            log_console.error(f"{message}")
            log_file.error(f"{message}")
            
            TYPE_EVENT = "Service"
            objectTypeDescription_EVENT = "Service"
            SUB_EVENT = "Service"  # "Service" / "Service"
            MESSAGE_EVENT = f"Pas de traitement car soucis de validation de l'IDP {IDP_ALIAS} ou du client {CALCUL_CLIENT} voir les logs du service"
            
            RESULT_SOLR = log_sorl.echoue(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
            if RESULT_SOLR["error"] :
                log_file.error(f"Enregistrement event solr - {RESULT_SOLR["return"]}")
                log_console.error(f" > Thread > Enregistrement event solr - {RESULT_SOLR["return"]}")
            
    except Exception as e:
        message = f"{name_thread_actuel} max ERROR: {e}"
        log_console.error(f"{message}")
        log_file.error(f"{message}")
        
        TYPE_EVENT = "Service"
        objectTypeDescription_EVENT = "Service"
        SUB_EVENT = "Service"  # "Service" / "Service"
        MESSAGE_EVENT = f"Erreur inconnu Voir les logs du service"
        
        RESULT_SOLR = log_sorl.echoue(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
        if RESULT_SOLR["error"] :
            log_file.error(f"Enregistrement event solr - {RESULT_SOLR["return"]}")
            log_console.error(f" > Thread > Enregistrement event solr - {RESULT_SOLR["return"]}")
        
        thread_traitement_nb = thread_traitement_nb - 1
        if thread_traitement_nb < 0 :
            thread_traitement_nb = 0
        
    thread_traitement_nb = thread_traitement_nb - 1
    if thread_traitement_nb < 0 :
        thread_traitement_nb = 0
        
    log_console.debug(f" > Fin du traitement des ajouts")

#-------------------------------------------------------
#-----------                MAIN
#-------------------------------------------------------

if __name__ == "__main__":
    
    log_console.info(f"------------------------------------------------")
    log_file.info(f"------------------------------------------------")
    log_console.info(f"Récuperation des paramètres du fichier INI")
    log_file.info(f"Récuperation des paramètres du fichier INI")
    
    
    #--------------------------------------------------------------------- 
    #- SERVICE
    #---------------------------------------------------------------------
    
    SERVICE_HEURE_PARAM = complement.get_param(config,'SERVICE','SERVICE_HEURE')
    if SERVICE_HEURE_PARAM["error"] :
        SERVICE_HEURE = "*/8"
    else :
        SERVICE_HEURE = SERVICE_HEURE_PARAM["return"]
    
    SERVICE_MINUTE_PARAM = complement.get_param(config,'SERVICE','SERVICE_MINUTE')
    if SERVICE_MINUTE_PARAM["error"] :
        SERVICE_MINUTE = "*/60"
    else :
        SERVICE_MINUTE = SERVICE_MINUTE_PARAM["return"] 
    
    
    #--------------------------------------------------------------------- 
    #- ENVIRONNEMENT
    #---------------------------------------------------------------------
    
    CLIENT_PARAM = complement.get_param(config,'ENVIRONNEMENT','CLIENT')
    if CLIENT_PARAM["error"] :
        log_console.error(CLIENT_PARAM["return"])
        log_file.error(CLIENT_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        CLIENT = CLIENT_PARAM["return"]
        
    ENVIRONNEMENT_PARAM = complement.get_param(config,'ENVIRONNEMENT','ENVIRONNEMENT')
    if ENVIRONNEMENT_PARAM["error"] :
        log_console.error(ENVIRONNEMENT_PARAM["return"])
        log_file.error(ENVIRONNEMENT_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        ENVIRONNEMENT = ENVIRONNEMENT_PARAM["return"]
    
    
    #--------------------------------------------------------------------- 
    #- KEYCLOAK
    #---------------------------------------------------------------------
    
    KEYCLOAK_URL_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_URL')
    if KEYCLOAK_URL_PARAM["error"] :
        log_console.error(KEYCLOAK_URL_PARAM["return"])
        log_file.error(KEYCLOAK_URL_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_URL = KEYCLOAK_URL_PARAM["return"]
    
    KEYCLOAK_LOGIN_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_LOGIN')
    if KEYCLOAK_LOGIN_PARAM["error"] :
        log_console.error(KEYCLOAK_LOGIN_PARAM["return"])
        log_file.error(KEYCLOAK_LOGIN_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_LOGIN = KEYCLOAK_LOGIN_PARAM["return"]
    
    KEYCLOAK_PASSWORD_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_PASSWORD')
    if KEYCLOAK_PASSWORD_PARAM["error"] :
        log_console.error(KEYCLOAK_PASSWORD_PARAM["return"])
        log_file.error(KEYCLOAK_PASSWORD_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_PASSWORD = KEYCLOAK_PASSWORD_PARAM["return"]
    
    KEYCLOAK_CLIENTSECRET_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_CLIENTSECRET')
    if KEYCLOAK_CLIENTSECRET_PARAM["error"] :
        log_console.error(KEYCLOAK_CLIENTSECRET_PARAM["return"])
        log_file.error(KEYCLOAK_CLIENTSECRET_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_CLIENTSECRET = KEYCLOAK_CLIENTSECRET_PARAM["return"]
    
    
    #--------------------------------------------------------------------- 
    #- YOUDOC
    #---------------------------------------------------------------------
    
    YOUDOC_URL_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_URL')
    if YOUDOC_URL_PARAM["error"] :
        log_console.error(YOUDOC_URL_PARAM["return"])
        log_file.error(YOUDOC_URL_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_URL = YOUDOC_URL_PARAM["return"]
    
    
    YOUDOC_TENANT_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_TENANT')
    if YOUDOC_TENANT_PARAM["error"] :
        log_console.error(YOUDOC_TENANT_PARAM["return"])
        log_file.error(YOUDOC_TENANT_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_TENANT = YOUDOC_TENANT_PARAM["return"]
    
    
    YOUDOC_LOGIN_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_LOGIN')
    if YOUDOC_LOGIN_PARAM["error"] :
        log_console.error(YOUDOC_LOGIN_PARAM["return"])
        log_file.error(YOUDOC_LOGIN_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_LOGIN = YOUDOC_LOGIN_PARAM["return"]
    
    YOUDOC_PASSWORD_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_PASSWORD')
    if YOUDOC_PASSWORD_PARAM["error"] :
        log_console.error(YOUDOC_PASSWORD_PARAM["return"])
        log_file.error(YOUDOC_PASSWORD_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_PASSWORD = YOUDOC_PASSWORD_PARAM["return"]
    
    
    
    #--------------------------------------------------------------------- 
    #- SOLR
    #---------------------------------------------------------------------
    
    SOLR_URL_PARAM = complement.get_param(config,'SOLR','SOLR_URL')
    if SOLR_URL_PARAM["error"] :
        log_console.error(SOLR_URL_PARAM["return"])
        log_file.error(SOLR_URL_PARAM["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        SOLR_URL = SOLR_URL_PARAM["return"]
    
    
    SOLR_LOGIN_PARAM = complement.get_param(config,'SOLR','SOLR_LOGIN')
    if SOLR_LOGIN_PARAM["error"] :
        log_console.error(SOLR_LOGIN_PARAM["return"])
        log_file.error(SOLR_LOGIN_PARAM["return"])
        SOLR_LOGIN="default-svc-usr"
    else :
        SOLR_LOGIN = SOLR_LOGIN_PARAM["return"]
    
    SOLR_PASSWORD_PARAM = complement.get_param(config,'SOLR','SOLR_PASSWORD')
    if SOLR_PASSWORD_PARAM["error"] :
        log_console.error(SOLR_PASSWORD_PARAM["return"])
        log_file.error(SOLR_PASSWORD_PARAM["return"])
        SOLR_PASSWORD="zYDdjrIZ2M1jbgv"
    else :
        SOLR_PASSWORD = SOLR_PASSWORD_PARAM["return"]
    
    
    SOLR_LOG_PARAM = complement.get_bool_param(config,'SOLR','SOLR_LOG')
    if SOLR_LOG_PARAM["error"] :
        log_console.error(SOLR_LOG_PARAM["return"])
        log_file.error(SOLR_LOG_PARAM["return"])
        SOLR_LOG = True
    else :
        SOLR_LOG = SOLR_PASSWORD_PARAM["return"]
    
    #--------------------------------------------------------------------- 
    #- PARAM
    #---------------------------------------------------------------------
    
    KEYCLOAK_TIMEOUT_TIME_PARAM = complement.get_param(config,'PARAM','KEYCLOAK_TIMEOUT_TIME')
    if KEYCLOAK_TIMEOUT_TIME_PARAM["error"] :
        KEYCLOAK_TIMEOUT_TIME = 10
    else :
        KEYCLOAK_TIMEOUT_TIME = int(KEYCLOAK_TIMEOUT_TIME_PARAM["return"])
    
    KEYCLOAK_VERIF_SSL_PARAM = complement.get_bool_param(config,'PARAM','KEYCLOAK_VERIF_SSL')
    if KEYCLOAK_VERIF_SSL_PARAM["error"] :
        KEYCLOAK_VERIF_SSL = False
    else :
        KEYCLOAK_VERIF_SSL = KEYCLOAK_VERIF_SSL_PARAM["return"]
    
    
    YOUDOC_TIMEOUT_TIME_PARAM = complement.get_param(config,'PARAM','YOUDOC_TIMEOUT_TIME')
    if YOUDOC_TIMEOUT_TIME_PARAM["error"] :
        YOUDOC_TIMEOUT_TIME = 10
    else :
        YOUDOC_TIMEOUT_TIME = int(YOUDOC_TIMEOUT_TIME_PARAM["return"])
    
    YOUDOC_VERIF_SSL_PARAM = complement.get_bool_param(config,'PARAM','YOUDOC_VERIF_SSL')
    if YOUDOC_VERIF_SSL_PARAM["error"] :
        YOUDOC_VERIF_SSL = False
    else :
        YOUDOC_VERIF_SSL = YOUDOC_VERIF_SSL_PARAM["return"]
    
    SOLR_TIMEOUT_TIME_PARAM = complement.get_param(config,'PARAM','SOLR_TIMEOUT_TIME')
    if SOLR_TIMEOUT_TIME_PARAM["error"] :
        SOLR_TIMEOUT_TIME = 10
    else :
        SOLR_TIMEOUT_TIME = int(SOLR_TIMEOUT_TIME_PARAM["return"])
    
    SOLR_VERIF_SSL_PARAM = complement.get_bool_param(config,'PARAM','SOLR_VERIF_SSL')
    if SOLR_VERIF_SSL_PARAM["error"] :
        SOLR_VERIF_SSL = False
    else :
        SOLR_VERIF_SSL = SOLR_VERIF_SSL_PARAM["return"]
        
    
    
    
    #--------------------------------------------------------------------- 
    #- PARAM
    #---------------------------------------------------------------------
    
    KEYCLOAK_REALM = "master"
    CALCUL_CLIENT_ID = "admin-cli"
    KEYCLOAK_GRANT_TYPE = "password"
    
    CODE_EVENT = "S"
    TENANT_EVENT = YOUDOC_TENANT
    USER_EVENT = SOLR_LOGIN
    
    FRAMEWORK_EVENT = "YOUDOC-SYNCHRO"
    
    LOGICIEL_EVENT = "Keycloak Synchro"
    SOFTWARE_EVENT = "Keycloak Synchro"
    
    CATEGORIE_EVENT = "BATCH"
    
    #--------------------------------------------------------------------- 
    #- PARAM LUVA
    #---------------------------------------------------------------------
    
    
    KEYCLOAK_VERIF_DEBUG_PARAM = complement.get_bool_param(config,'LUVA','DEBUG')
    if KEYCLOAK_VERIF_DEBUG_PARAM["error"] :
        DEBUG = False
    else :
        DEBUG = KEYCLOAK_VERIF_DEBUG_PARAM["return"]
    
    KEYCLOAK_VERIF_DEBUG_PARAM = complement.get_bool_param(config,'LUVA','IS_DEBUG')
    if KEYCLOAK_VERIF_DEBUG_PARAM["error"] :
        is_debug = False
    else :
        is_debug = KEYCLOAK_VERIF_DEBUG_PARAM["return"]
    
    CALCUL_CLIENT_REALM_PARAM = complement.get_param(config,'LUVA','CALCUL_CLIENT_REALM')
    if CALCUL_CLIENT_REALM_PARAM["error"] :
        CALCUL_CLIENT_REALM = f"YD-{CLIENT}-{ENVIRONNEMENT}"
    else :
        CALCUL_CLIENT_REALM = CALCUL_CLIENT_REALM_PARAM["return"]
    
    CALCUL_CLIENT_PARAM = complement.get_param(config,'LUVA','CALCUL_CLIENT')
    if CALCUL_CLIENT_PARAM["error"] :
        CALCUL_CLIENT = f"YDG-{CLIENT}-{ENVIRONNEMENT}"
    else :
        CALCUL_CLIENT = CALCUL_CLIENT_PARAM["return"]
    
    ACTION = "CREATION"
    
    IDP_ALIAS_PARAM = complement.get_param(config,'LUVA','IDP_ALIAS')
    if IDP_ALIAS_PARAM["error"] :
        IDP_ALIAS = f"YD-{CLIENT}-{ENVIRONNEMENT}"
    else :
        IDP_ALIAS = IDP_ALIAS_PARAM["return"]
        
    KEYCLOAK_REALM = CALCUL_CLIENT_REALM
    
    
    #--------------------------------------------------------------------- 
    #- LOG
    #---------------------------------------------------------------------
    
    if is_debug :
        log_console.debug(f"----------------------------------------------------")
        log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
        log_console.debug(f" > ++ CLIENT_REALM = {CALCUL_CLIENT_REALM}")
        log_console.debug(f" > ++ CLIENT = {CALCUL_CLIENT}")
        
    log_file.debug(f"----------------------------------------------------")
    log_file.info(f"Recupération des param SERVICE > OK")
    log_file.info(f"Recupération des param KEYCLOAK > OK")
    log_file.info(f"Recupération des param YOUDOC > OK")
    log_file.info(f"Recupération des param SOLR > OK")
    log_file.info(f"Recupération des param PARAM > OK")
    
    if SOLR_LOG :
        log_sorl = solr_event.SolrEventPublisher(f"{SOLR_URL}",TENANT_EVENT,SOLR_LOGIN,SOLR_PASSWORD,SOLR_VERIF_SSL,SOLR_TIMEOUT_TIME)
        RESULT_SOLR = log_sorl.test_connection()
        if RESULT_SOLR["error"] :
            log_console.error(RESULT_SOLR["return"])
            log_file.error(RESULT_SOLR["return"])
            if not contrainte_is_service : 
                print("Appuyer sur entrer pour fermer")
                input()
                sys.exit(1)
        else :
            log_console.info(f"connexion SOLR valide")
            log_file.info(f"connexion SOLR valide")
        
    
        RESULT_SOLR = log_sorl.init_event_info(TENANT_EVENT,USER_EVENT,FRAMEWORK_EVENT,LOGICIEL_EVENT,SOFTWARE_EVENT,CODE_EVENT)
        if RESULT_SOLR["error"] :
            log_console.error(RESULT_SOLR["return"])
            log_file.error(RESULT_SOLR["return"])
            if not contrainte_is_service : 
                print("Appuyer sur entrer pour fermer")
                input()
                sys.exit(1)
        else :
            log_console.debug(f"init_event_info SOLR ok")
    
    
        TYPE_EVENT = "Service"
        objectTypeDescription_EVENT = "Service"
        SUB_EVENT = "Service"  # "Service" / "Service"
        MESSAGE_EVENT = "Lancement du service de synchro"
        RESULT_SOLR = log_sorl.en_cours(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
        if RESULT_SOLR["error"] :
            log_console.error(f"Enregistrement event solr - {RESULT_SOLR["return"]}")
            log_file.error(f"Enregistrement event solr - {RESULT_SOLR["return"]}")

    YOUDOC_CONNEXION = group_gestion.YdgGroupClass(YOUDOC_URL, YOUDOC_TENANT, YOUDOC_LOGIN, YOUDOC_PASSWORD, YOUDOC_TIMEOUT_TIME, YOUDOC_VERIF_SSL,
    KEYCLOAK_URL, CALCUL_CLIENT_ID, KEYCLOAK_CLIENTSECRET, CALCUL_CLIENT_REALM,KEYCLOAK_TIMEOUT_TIME, KEYCLOAK_VERIF_SSL, is_debug)
    
    YOUDOC_TOKEN = YOUDOC_CONNEXION.recup_barear()
    if YOUDOC_TOKEN["error"] :
        log_console.error(YOUDOC_TOKEN["return"])
        log_file.error(YOUDOC_TOKEN["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
            sys.exit(1)
    else :
        log_console.info(f"connexion YOUDOC valide")
        log_file.info(f"connexion YOUDOC valide")
        if is_debug :
            log_console.debug(f"----------------------------------------------------")
            log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
            log_console.debug(f" > ++ TOKEN =")
            log_console.debug(f" > ++ {YOUDOC_TOKEN["return"]}")

    
    KEYCLOAK_CONNECT = keycloak_suite.Keycloak_youdoc(KEYCLOAK_URL, KEYCLOAK_REALM,CALCUL_CLIENT_REALM, CALCUL_CLIENT_ID, KEYCLOAK_GRANT_TYPE, KEYCLOAK_LOGIN, KEYCLOAK_PASSWORD ,KEYCLOAK_TIMEOUT_TIME , KEYCLOAK_VERIF_SSL, is_debug)
    
    KEYCLOAK_TOKEN = KEYCLOAK_CONNECT.recup_token_barear()
    if KEYCLOAK_TOKEN["error"] :
        log_console.error(KEYCLOAK_TOKEN["return"])
        log_file.error(KEYCLOAK_TOKEN["return"])
        if not contrainte_is_service : 
            print("Appuyer sur entrer pour fermer")
            input()
            sys.exit(1)
    else :
        log_console.info(f"connexion KEYCLOAK valide")
        log_file.info(f"connexion KEYCLOAK valide")
        if is_debug :
            log_console.debug(f"----------------------------------------------------")
            log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
            log_console.debug(f" > ++ TOKEN =")
            log_console.debug(f" > ++ {KEYCLOAK_TOKEN["return"]}")
    global KEYCLOAK_ID_CLIENT_VALIDE
    global KEYCLOAK_ID_PROVIDER_VALIDE
    try :
        KEYCLOAK_ID_CLIENT = KEYCLOAK_CONNECT.recup_client_id(CALCUL_CLIENT)
        if KEYCLOAK_ID_CLIENT["error"] :
            log_console.error(KEYCLOAK_ID_CLIENT["return"])
            log_file.error(KEYCLOAK_ID_CLIENT["return"])
            KEYCLOAK_ID_CLIENT_VALIDE = False
            if not contrainte_is_service : 
                print("Appuyer sur entrer pour fermer")
                input()
                sys.exit(1)
        else :
            log_console.info(f"connexion ID CLIENT = OK")
            log_file.info(f"connexion ID CLIENT = OK")
            KEYCLOAK_ID_CLIENT_VALIDE = True
            if is_debug :
                log_console.debug(f"----------------------------------------------------")
                log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
                log_console.debug(f" > ++ ID CLIENT = {KEYCLOAK_ID_CLIENT["return"]}")
    except Exception as e:
        log_console.error(f"connexion ID PROVIDER = {e}")
        log_file.error(f"connexion ID PROVIDER = {e}")
        KEYCLOAK_ID_CLIENT_VALIDE = False
        
    try :
        KEYCLOAK_ID_PROVIDER = KEYCLOAK_CONNECT.recup_identity_provider(IDP_ALIAS)
        if KEYCLOAK_ID_PROVIDER["error"] :
            log_console.error(KEYCLOAK_ID_PROVIDER["return"])
            log_file.error(KEYCLOAK_ID_PROVIDER["return"])
            KEYCLOAK_ID_PROVIDER_VALIDE = False
            if not contrainte_is_service : 
                print("Appuyer sur entrer pour fermer")
                input()
                sys.exit(1)
        else :
            log_console.info(f"connexion ID PROVIDER = OK")
            log_file.info(f"connexion ID PROVIDER = OK")
            KEYCLOAK_ID_PROVIDER_VALIDE = True
            if is_debug :
                log_console.debug(f"----------------------------------------------------")
                log_console.debug(f" > ++ IS_DEBUG = {is_debug}")
                log_console.debug(f" > ++ ID PROVIDER = {KEYCLOAK_ID_PROVIDER["return"]}") 
    except Exception as e:
        log_console.error(f"connexion ID PROVIDER = {e}")
        log_file.error(f"connexion ID PROVIDER = {e}")
        KEYCLOAK_ID_PROVIDER_VALIDE = False
        
    timer()
    
    log_console.info(f"Fin")
    log_file.info(f"Fin")
    if not contrainte_is_service : print("FIN")
    
    
    
    
    sys.exit(1)
    TYPE_EVENT = "ROLE"
    objectTypeDescription_EVENT = "ROLE"
    SUB_EVENT = "ROLE"  # "ROLE" / "MAPPER"
    MESSAGE_EVENT = "Création du groupe test avec id 48"
    
    log_console.debug(result_connexion)
    
    result_connexion = log_sorl.en_cours(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
    log_console.debug(result_connexion)
    
    result_connexion = log_sorl.traite(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
    log_console.debug(result_connexion)
    
    result_connexion = log_sorl.echoue(CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT)
    log_console.debug(result_connexion)
    
    
    
    
    
    
    log_file.info(f"-- Connexion YOUDOC")
    log_file.debug(f"-- Connexion YOUDOC")
    
    
   
    
    
    

