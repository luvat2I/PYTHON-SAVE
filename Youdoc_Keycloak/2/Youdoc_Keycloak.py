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
    if not contrainte_is_service :
        print(f"> 1 > -----------------------------------------------------------------------")
        print(f"> 1 > = Récuperation des paramètres du fichier {ini_filename}")
    
    CLIENT_PARAM = complement.get_param(config,'ENVIRONNEMENT','CLIENT')
    if CLIENT_PARAM["error"] :
        if not contrainte_is_service :
            print(CLIENT_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        CLIENT = CLIENT_PARAM["return"]
    
    ENVIRONNEMENT_PARAM = complement.get_param(config,'ENVIRONNEMENT','ENVIRONNEMENT')
    if ENVIRONNEMENT_PARAM["error"] :
        if not contrainte_is_service :
            print(ENVIRONNEMENT_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        ENVIRONNEMENT = ENVIRONNEMENT_PARAM["return"]
        
    KEYCLOAK_URL_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_URL')
    if KEYCLOAK_URL_PARAM["error"] :
        if not contrainte_is_service :
            print(KEYCLOAK_URL_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_URL = KEYCLOAK_URL_PARAM["return"]
    
    KEYCLOAK_LOGIN_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_LOGIN')
    if KEYCLOAK_LOGIN_PARAM["error"] :
        if not contrainte_is_service :
            print(KEYCLOAK_LOGIN_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_LOGIN = KEYCLOAK_LOGIN_PARAM["return"]
    
    KEYCLOAK_PASSWORD_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_PASSWORD')
    if KEYCLOAK_PASSWORD_PARAM["error"] :
        if not contrainte_is_service :
            print(KEYCLOAK_PASSWORD_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_PASSWORD = KEYCLOAK_PASSWORD_PARAM["return"]
    
    KEYCLOAK_CLIENTSECRET_PARAM = complement.get_param(config,'KEYCLOAK','KEYCLOAK_CLIENTSECRET')
    if KEYCLOAK_CLIENTSECRET_PARAM["error"] :
        if not contrainte_is_service :
            print(KEYCLOAK_CLIENTSECRET_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        KEYCLOAK_CLIENTSECRET = KEYCLOAK_CLIENTSECRET_PARAM["return"]
    
    # ++++++++++++++++++++++++++++++
    # Recup variables KEYCLOAK_PARAM
    # ++++++++++++++++++++++++++++++
    
    KEYCLOAK_TIMEOUT_TIME_PARAM = complement.get_param(config,'KEYCLOAK_PARAM','KEYCLOAK_TIMEOUT_TIME')
    if KEYCLOAK_TIMEOUT_TIME_PARAM["error"] :
        KEYCLOAK_TIMEOUT_TIME = 10
    else :
        KEYCLOAK_TIMEOUT_TIME = int(KEYCLOAK_TIMEOUT_TIME_PARAM["return"])
    
    KEYCLOAK_VERIF_SSL_PARAM = complement.get_bool_param(config,'KEYCLOAK_PARAM','KEYCLOAK_VERIF_SSL')
    if KEYCLOAK_VERIF_SSL_PARAM["error"] :
        KEYCLOAK_VERIF_SSL = False
    else :
        KEYCLOAK_VERIF_SSL = KEYCLOAK_VERIF_SSL_PARAM["return"]
    
    KEYCLOAK_CREATE_ROLE_PARAM = complement.get_bool_param(config,'KEYCLOAK_PARAM','KEYCLOAK_CREATE_ROLE')
    if KEYCLOAK_CREATE_ROLE_PARAM["error"] :
        KEYCLOAK_CREATE_ROLE = False
    else :
        KEYCLOAK_CREATE_ROLE = KEYCLOAK_CREATE_ROLE_PARAM["return"]
    
    
    GENERATION_RAPPORT_ROLE_PARAM = complement.get_bool_param(config,'KEYCLOAK_PARAM','GENERATION_RAPPORT')
    if GENERATION_RAPPORT_ROLE_PARAM["error"] :
        GENERATION_RAPPORT_ROLE = False
    else :
        GENERATION_RAPPORT_ROLE = GENERATION_RAPPORT_ROLE_PARAM["return"]

    # ++++++++++++++++++++++++++++++
    # Init des variables KEYCLOAK
    # ++++++++++++++++++++++++++++++
    
    KEYCLOAK_REALM = "master"
    CALCUL_CLIENT_ID = "admin-cli"
    KEYCLOAK_GRANT_TYPE = "password"
    
    # ++++++++++++++++++++++++++++++
    # Recup variables YOUDOC
    # ++++++++++++++++++++++++++++++
    
    YOUDOC_URL_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_URL')
    if YOUDOC_URL_PARAM["error"] :
        if not contrainte_is_service :
            print(YOUDOC_URL_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_URL = YOUDOC_URL_PARAM["return"]
    
    
    YOUDOC_TENANT_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_TENANT')
    if YOUDOC_TENANT_PARAM["error"] :
        if not contrainte_is_service :
            print(YOUDOC_TENANT_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_TENANT = YOUDOC_TENANT_PARAM["return"]
    
    
    YOUDOC_LOGIN_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_LOGIN')
    if YOUDOC_LOGIN_PARAM["error"] :
        if not contrainte_is_service :
            print(YOUDOC_LOGIN_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_LOGIN = YOUDOC_LOGIN_PARAM["return"]
    
    YOUDOC_PASSWORD_PARAM = complement.get_param(config,'YOUDOC','YOUDOC_PASSWORD')
    if YOUDOC_PASSWORD_PARAM["error"] :
        if not contrainte_is_service :
            print(YOUDOC_PASSWORD_PARAM["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        YOUDOC_PASSWORD = YOUDOC_PASSWORD_PARAM["return"]
     
    # ++++++++++++++++++++++++++++++
    # Recup variables YOUDOC_PARAM
    # ++++++++++++++++++++++++++++++
    
    YOUDOC_TIMEOUT_TIME_PARAM = complement.get_param(config,'KEYCLOAK_PARAM','YOUDOC_TIMEOUT_TIME')
    if YOUDOC_TIMEOUT_TIME_PARAM["error"] :
        YOUDOC_TIMEOUT_TIME = 10
    else :
        YOUDOC_TIMEOUT_TIME = int(YOUDOC_TIMEOUT_TIME_PARAM["return"])
    
    YOUDOC_VERIF_SSL_PARAM = complement.get_bool_param(config,'KEYCLOAK_PARAM','YOUDOC_VERIF_SSL')
    if YOUDOC_VERIF_SSL_PARAM["error"] :
        YOUDOC_VERIF_SSL = False
    else :
        YOUDOC_VERIF_SSL = YOUDOC_VERIF_SSL_PARAM["return"]
    
    YOUDOC_CREATE_GROUPE_PARAM = complement.get_bool_param(config,'YOUDOC_PARAM','YOUDOC_CREATE_GROUPE')
    if YOUDOC_CREATE_GROUPE_PARAM["error"] :
        YOUDOC_CREATE_GROUPE = False
    else :
        YOUDOC_CREATE_GROUPE = YOUDOC_CREATE_GROUPE_PARAM["return"]
    
    GENERATION_RAPPORT_GROUPE_PARAM = complement.get_bool_param(config,'YOUDOC_PARAM','GENERATION_RAPPORT')
    if GENERATION_RAPPORT_GROUPE_PARAM["error"] :
        GENERATION_RAPPORT_GROUPE = False
    else :
        GENERATION_RAPPORT_GROUPE = GENERATION_RAPPORT_GROUPE_PARAM["return"]
        
    # ++++++++++++++++++++++++++++++
    # Recup des variables IDP
    # ++++++++++++++++++++++++++++++
    
    CREATE_MAPPER_PARAM = complement.get_bool_param(config,'IDP','CREATE_MAPPER')
    if CREATE_MAPPER_PARAM["error"] :
        CREATE_MAPPER = False
    else :
        CREATE_MAPPER = CREATE_MAPPER_PARAM["return"]
    
    GENERATION_RAPPORT_MAPPER_PARAM = complement.get_bool_param(config,'IDP','GENERATION_RAPPORT')
    if GENERATION_RAPPORT_MAPPER_PARAM["error"] :
        GENERATION_RAPPORT_MAPPER = False
    else :
        GENERATION_RAPPORT_MAPPER = GENERATION_RAPPORT_MAPPER_PARAM["return"]
    
    # ++++++++++++++++++++++++++++++
    # Recup des variables SERVICES
    # ++++++++++++++++++++++++++++++
    
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
    
    # ++++++++++++++++++++++++++++++
    # Init des variables LUVA
    # ++++++++++++++++++++++++++++++
    
    
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
    
    if not contrainte_is_service :
        if is_debug :
            print(f"> 1 > ----------------------------------------------------")
            print(f"> 1 > ++ IS_DEBUG = {is_debug}")
            print(f"> 1 > ++ CLIENT_REALM = {CALCUL_CLIENT_REALM}")
            print(f"> 1 > ++ CLIENT = {CALCUL_CLIENT}")
        
        print(f"> 1 > -----------------------------------------------------------------------")
        print(f"> 1 > | KEYCLOAK |")
        print(f"> 1 > + URL Keycloak = {KEYCLOAK_URL}")
        print(f"> 1 > + REALM = {CALCUL_CLIENT_REALM}")
        print(f"> 1 > + CLIENT ID = {CALCUL_CLIENT}")
        print(f"> 1 > + CLIENT SECRET = {KEYCLOAK_CLIENTSECRET}")
        print(f"> 1 > + LOGIN Keycloak = {KEYCLOAK_LOGIN}")
        print(f"> 1 > + PASSWORD Keycloak ={KEYCLOAK_PASSWORD}")
        print(f"> 1 > + TIMEOUT Keycloak ={KEYCLOAK_TIMEOUT_TIME}")
        print(f"> 1 > + SSL Keycloak = {KEYCLOAK_VERIF_SSL}")

        
        print(f"> 1 > -----------------------------------------------------------------------")
        print(f"> 1 > | YOUDOC |")
        print(f"> 1 > + URL Youdoc = {YOUDOC_URL}")
        print(f"> 1 > + TENANT Youdoc = {YOUDOC_TENANT}")
        print(f"> 1 > + LOGIN Youdoc = {YOUDOC_LOGIN}")
        print(f"> 1 > + PASSWORD Youdoc ={YOUDOC_PASSWORD}")
        print(f"> 1 > + TIMEOUT Youdoc ={YOUDOC_TIMEOUT_TIME}")
        print(f"> 1 > + SSL Youdoc = {YOUDOC_VERIF_SSL}")
        
        print(f"> 1 > -----------------------------------------------------------------------")
        print(f"> 1 > | IDP |")
        if CREATE_MAPPER :
            print(f"> 1 > + ALIAS IDP = {IDP_ALIAS}")
        else :
            print(f"> 1 > + PAS DE CREATION DE MAPPER")
        print(f"> 1 > -----------------------------------------------------------------------")
        print(f"> 1 > = FIN > Récuperation des paramètres")
        print(f"> 1 > -----------------------------------------------------------------------")
        print("")
        
        print(f"> 2 > -----------------------------------------------------------------------")
        print(f"> 2 > = Connexions Keycloak et Youdoc")
        print(f"> 2 > -----------------------------------------------------------------------")
        
        print(f"> 2 > -----------------------------------------------------------------------")
        print(f"> 2 > | Connexion KEYCLOAK |")
    
    YOUDOC_CONNEXION = group_gestion.YdgGroupClass(YOUDOC_URL, YOUDOC_TENANT, YOUDOC_LOGIN, YOUDOC_PASSWORD, YOUDOC_TIMEOUT_TIME, YOUDOC_VERIF_SSL,
    KEYCLOAK_URL, CALCUL_CLIENT_ID, KEYCLOAK_CLIENTSECRET, CALCUL_CLIENT_REALM,KEYCLOAK_TIMEOUT_TIME, KEYCLOAK_VERIF_SSL, is_debug)
    
    YOUDOC_TOKEN = YOUDOC_CONNEXION.recup_barear()
    if YOUDOC_TOKEN["error"] :
        if not contrainte_is_service :
            print(YOUDOC_TOKEN["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        if not contrainte_is_service :
            print(f"> 2 > + Récupération du token et connexion > Connexion OK")
            print(f"> 2 > + Récupération du token et connexion > Token OK")
            if DEBUG : 
                print(f"")
                print(f"> 2 > Token :")
                print(f"{YOUDOC_TOKEN["return"]}")
                print(f"")
    if not contrainte_is_service :
        print(f"> 2 > + Récupération du token et connexion > FIN")
        print("")
    
    
    if not contrainte_is_service :
        print(f"> 2 > -----------------------------------------------------------------------")
        print(f"> 2 > | Connexion YOUDOC |")
    KEYCLOAK_CONNECT = keycloak_suite.Keycloak_youdoc(KEYCLOAK_URL, KEYCLOAK_REALM,CALCUL_CLIENT_REALM, CALCUL_CLIENT_ID, KEYCLOAK_GRANT_TYPE, KEYCLOAK_LOGIN, KEYCLOAK_PASSWORD ,KEYCLOAK_TIMEOUT_TIME , KEYCLOAK_VERIF_SSL, is_debug)
    
    KEYCLOAK_TOKEN = KEYCLOAK_CONNECT.recup_token_barear()
    if KEYCLOAK_TOKEN["error"] :
        if not contrainte_is_service :
            print(KEYCLOAK_TOKEN["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        if not contrainte_is_service :
            print(f"> 2 > Récupération du token et connexion > Connexion OK")
            print(f"> 2 > Récupération du token et connexion > Token OK")
            if DEBUG : 
                print(f"")
                print(f"> 2 > Token :")
                print(f"{KEYCLOAK_TOKEN["return"]}")
                print(f"")
    if not contrainte_is_service :
        print(f"> 2 > Récupération du token et connexion > FIN")
    
    KEYCLOAK_ID_CLIENT = KEYCLOAK_CONNECT.recup_client_id(CALCUL_CLIENT)
    if KEYCLOAK_ID_CLIENT["error"] :
        if not contrainte_is_service :
            print(KEYCLOAK_ID_CLIENT["return"])
            print("Appuyer sur entrer pour fermer")
            input()
        sys.exit(1)
    else :
        if not contrainte_is_service :
            print(f"> 3 > Le client {CALCUL_CLIENT} existe")
            if DEBUG : 
                print(f"> 3 > ID client :")
                print(KEYCLOAK_ID_CLIENT["return"])
    if not contrainte_is_service :
        print(f"> 3 > Connexion au client {CALCUL_CLIENT} > FINI")
    
    IDP_VALIDE = False
    KEYCLOAK_ID_PROVIDER = KEYCLOAK_CONNECT.recup_identity_provider(IDP_ALIAS)
    if KEYCLOAK_ID_PROVIDER["error"] :
        print(KEYCLOAK_ID_PROVIDER["return"])
        print("Appuyer sur entrer pour fermer")
        input()
        sys.exit(1)
    else :
        if not contrainte_is_service : print(f"> 3 > L'IDP {IDP_ALIAS} existe")
        if DEBUG : 
            print(f"> 3 > IDP :")
            print(KEYCLOAK_ID_PROVIDER["return"])
        IDP_VALIDE = True
        if not contrainte_is_service : print(f"> 3 > Connexion à l'IDP {IDP_ALIAS} > FINI")
    
    if not contrainte_is_service :
        print(f"> 2 > -----------------------------------------------------------------------")
        print(f"> 2 > = FIN > Connexions Keycloak et Youdoc")
        print(f"> 2 > -----------------------------------------------------------------------")
        print("")
    
        print(f"> 5 > = Generation du rapport des GROUPES") 
    timer()
    if not contrainte_is_service : print("FIN")
    
    

