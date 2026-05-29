import json
import requests
from typing import Dict, Any, Optional
from requests.auth import HTTPBasicAuth
import urllib3
import socket
from datetime import datetime
# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SolrEventPublisher:
    """
    Classe pour publier des événements XFRAMEWORK vers Solr avec authentification.
    """
    
    def __init__(
        self, 
        solr_url: str, 
        collection_name: str, 
        username: str,
        password: str,
        verify_ssl: bool = False,
        timeout: int = 10
    ):
        """
        Initialise le publisher Solr avec authentification.
        
        Args:
            solr_url: URL de base du serveur Solr (ex: http://localhost:8983)
            collection_name: Nom de la collection Solr cible
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification
            verify_ssl: Vérifier le certificat SSL (défaut: False)
            timeout: Timeout pour les requêtes HTTP en secondes
        """
        self.solr_url = solr_url.rstrip('/')
        self.collection_name = collection_name
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.update_url = f"{self.solr_url}/solr/{collection_name}/update/json"
        self.auth = HTTPBasicAuth(self.username, self.password)
        
        self.TENANT_EVENT = None
        self.USER_EVENT = None

        self.FRAMEWORK_EVENT = None
        self.LOGICIEL_EVENT = None
        self.SOFTWARE_EVENT = None
        self.CODE_EVENT = None
        
        
    def init_event_info(self, TENANT_EVENT,USER_EVENT,FRAMEWORK_EVENT,LOGICIEL_EVENT,SOFTWARE_EVENT,CODE_EVENT):
        """
        Envoie l'événement vers Solr avec authentification.
        """
        try:

            self.TENANT_EVENT = TENANT_EVENT
            self.USER_EVENT = USER_EVENT

            self.FRAMEWORK_EVENT = FRAMEWORK_EVENT
            self.LOGICIEL_EVENT = LOGICIEL_EVENT
            self.SOFTWARE_EVENT = SOFTWARE_EVENT
            
            self.CODE_EVENT = CODE_EVENT
            
            return {
                    "error": False,
                    "return": f"init_event_info > ok"
                }
            
        except Exception as e:
            return {
                    "error": True,
                    "return": f"ERROR : {e}"
                }
        
    
    def en_cours(self,CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT):
        """
        Envoie l'événement vers Solr avec authentification.
        """
        try:
            
            STATUS_EVENT = "2"
            STATUS_DESC = "En cours"
            
            return self._logsend_event(CATEGORIE_EVENT,CODE_EVENT,MESSAGE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,STATUS_EVENT,STATUS_DESC)
            
        except Exception as e:
            return {
                    "error": True,
                    "return": f"ERROR : {e}"
                }
                
    def traite(self,CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT):
        """
        Envoie l'événement vers Solr avec authentification.
        """
        try:
            
            
            STATUS_EVENT = "3"
            STATUS_DESC = "Traité"
            
            return self._logsend_event(CATEGORIE_EVENT,CODE_EVENT,MESSAGE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,STATUS_EVENT,STATUS_DESC)
            
        except Exception as e:
            return {
                    "error": True,
                    "return": f"ERROR : {e}"
                }
                
    def echoue(self,CATEGORIE_EVENT,CODE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,MESSAGE_EVENT):
        """
        Envoie l'événement vers Solr avec authentification.
        """
        try:
            
            STATUS_EVENT = "4"
            STATUS_DESC = "Échoué"
            
            return self._logsend_event(CATEGORIE_EVENT,CODE_EVENT,MESSAGE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,STATUS_EVENT,STATUS_DESC)
            
        except Exception as e:
            return {
                    "error": True,
                    "return": f"ERROR : {e}"
                }
                
    def _logsend_event(self,CATEGORIE_EVENT,CODE_EVENT,MESSAGE_EVENT,SUB_EVENT,TYPE_EVENT,objectTypeDescription_EVENT,STATUS_EVENT,STATUS_DESC):
        """
        Envoie l'événement vers Solr avec authentification.
        """
        try:
            
            TENANT_EVENT = self.TENANT_EVENT
            USER_EVENT = self.USER_EVENT

            FRAMEWORK_EVENT = self.FRAMEWORK_EVENT
            LOGICIEL_EVENT = self.LOGICIEL_EVENT
            SOFTWARE_EVENT = self.SOFTWARE_EVENT
            CODE_EVENT = self.CODE_EVENT
            
            SERVEUR = socket.gethostname()
            
            maintenant = datetime.now()

            YEAR_EVENT = f"{maintenant.year}"
            MONTH_EVENT = f"{maintenant.month}"
            DAY_EVENT = f"{maintenant.day}"
            HOUR_EVENT = f"{maintenant.hour}"
            MINUTE_EVENT = f"{maintenant.minute}"
            SECONDE_EVENT = f"{maintenant.second}"
            
            format_ID = maintenant.strftime("%y%m%d%H%M%S") + f"{maintenant.microsecond // 1000:03d}"
            ID_EVENT = f"{CODE_EVENT}{format_ID}"
            
            event_message = {
              "id":f"XFRAMEWORK-EVENT-BUSINESSOPERATION--{TENANT_EVENT}-{ID_EVENT}",
              "jsonObject":"{\"id\":\"XFRAMEWORK-EVENT-BUSINESSOPERATION--"+TENANT_EVENT+"-"+ID_EVENT+"\",\"objectReference\":{\"objectKind\":{\"softwareCode\":\"XFRAMEWORK-EVENT\",\"objectType\":\"BusinessOperation\",\"objectSubType\":\"\"},\"objectId\":\""+"ID_EVENT"+"\"},\"objectSource\":{\"uri\":\"\",\"objectSourceKind\":{\"type\":\"XFRAMEWORK-EVENT\",\"name\":\""+TENANT_EVENT+"\"}},\"objectDescription\":{\"audit\":{\"creationUser\":\""+USER_EVENT+"\",\"creationDateTime\":{\"year\":"+YEAR_EVENT+",\"month\":"+MONTH_EVENT+",\"dayOfMonth\":"+DAY_EVENT+",\"hourOfDay\":"+HOUR_EVENT+",\"minute\":"+MINUTE_EVENT+",\"second\":"+SECONDE_EVENT+"},\"modificationUser\":\""+USER_EVENT+"\",\"modificationDateTime\":{\"year\":"+YEAR_EVENT+",\"month\":"+MONTH_EVENT+",\"dayOfMonth\":"+DAY_EVENT+",\"hourOfDay\":"+HOUR_EVENT+",\"minute\":"+MINUTE_EVENT+",\"second\":"+SECONDE_EVENT+"}},\"creationUserFullName\":\""+USER_EVENT+"\",\"modificationUserFullName\":\""+USER_EVENT+"\",\"objectFilterDate\":{\"year\":"+YEAR_EVENT+",\"month\":"+MONTH_EVENT+",\"dayOfMonth\":"+DAY_EVENT+",\"hourOfDay\":"+HOUR_EVENT+",\"minute\":"+MINUTE_EVENT+",\"second\":"+SECONDE_EVENT+"}},\"objectKeyValues\":[\"#EVENT_CATEGORY#"+CATEGORIE_EVENT+"\"],\"objectSecurityClasses\":[[],[],[],[],[],[],[],[]],\"objectSecurityBusinessObjects\":[[],[]],\"objectAttributes\":\"{\\\"status\\\":\\\""+STATUS_EVENT+"\\\",\\\"statusDescription_fr\\\":\\\""+STATUS_DESC+"\\\",\\\"statusDescription_de\\\":\\\""+STATUS_DESC+"\\\",\\\"statusDescription_it\\\":\\\""+STATUS_DESC+"\\\",\\\"statusDescription_en\\\":\\\""+STATUS_DESC+"\\\",\\\"server\\\":\\\"{SERVEUR}\\\",\\\"environment\\\":\\\""+TENANT_EVENT+"\\\",\\\"softwareCode\\\":\\\""+SOFTWARE_EVENT+"\\\",\\\"softwareDescription_fr\\\":\\\""+LOGICIEL_EVENT+"\\\",\\\"softwareDescription_de\\\":\\\""+LOGICIEL_EVENT+"\\\",\\\"softwareDescription_it\\\":\\\""+LOGICIEL_EVENT+"\\\",\\\"softwareDescription_en\\\":\\\""+LOGICIEL_EVENT+"\\\",\\\"groupId\\\":\\\"0000000000000000\\\",\\\"objectType\\\":\\\""+objectTypeDescription_EVENT+"\\\",\\\"objectTypeDescription_fr\\\":\\\""+objectTypeDescription_EVENT+"\\\",\\\"objectTypeDescription_de\\\":\\\""+objectTypeDescription_EVENT+"\\\",\\\"objectTypeDescription_it\\\":\\\""+objectTypeDescription_EVENT+"\\\",\\\"objectTypeDescription_en\\\":\\\""+objectTypeDescription_EVENT+"\\\",\\\"objectSubType\\\":\\\""+SUB_EVENT+"\\\",\\\"objectSubTypeDescription_fr\\\":\\\""+SUB_EVENT+"\\\",\\\"objectSubTypeDescription_de\\\":\\\""+SUB_EVENT+"\\\",\\\"objectSubTypeDescription_it\\\":\\\""+SUB_EVENT+"\\\",\\\"objectSubTypeDescription_en\\\":\\\""+SUB_EVENT+"\\\",\\\"type\\\":\\\""+TYPE_EVENT+"\\\",\\\"typeDescription_fr\\\":\\\""+TYPE_EVENT+"\\\",\\\"typeDescription_de\\\":\\\""+TYPE_EVENT+"\\\",\\\"typeDescription_it\\\":\\\""+TYPE_EVENT+"\\\",\\\"typeDescription_en\\\":\\\""+TYPE_EVENT+"\\\",\\\"category\\\":\\\""+CATEGORIE_EVENT+"\\\",\\\"categoryDescription_fr\\\":\\\""+CATEGORIE_EVENT+"\\\",\\\"categoryDescription_de\\\":\\\""+CATEGORIE_EVENT+"\\\",\\\"categoryDescription_it\\\":\\\""+CATEGORIE_EVENT+"\\\",\\\"categoryDescription_en\\\":\\\""+CATEGORIE_EVENT+"\\\",\\\"source\\\":\\\"XECM\\\",\\\"message\\\":\\\""+MESSAGE_EVENT+"\\\",\\\"severity\\\":\\\"0\\\",\\\"severityDescription_fr\\\":\\\"0\\\",\\\"severityDescription_de\\\":\\\"0\\\",\\\"severityDescription_it\\\":\\\"0\\\",\\\"severityDescription_en\\\":\\\"0\\\",\\\"userName\\\":\\\""+USER_EVENT+"\\\",\\\"userFullName\\\":\\\""+USER_EVENT+"\\\",\\\"timestamp\\\":{\\\"year\\\":"+YEAR_EVENT+",\\\"month\\\":"+MONTH_EVENT+",\\\"dayOfMonth\\\":"+DAY_EVENT+",\\\"hourOfDay\\\":"+HOUR_EVENT+",\\\"minute\\\":"+MINUTE_EVENT+",\\\"second\\\":"+SECONDE_EVENT+"},\\\"DateTime\\\":{\\\"year\\\":"+YEAR_EVENT+",\\\"month\\\":"+MONTH_EVENT+",\\\"dayOfMonth\\\":"+DAY_EVENT+",\\\"hourOfDay\\\":"+HOUR_EVENT+",\\\"minute\\\":"+MINUTE_EVENT+",\\\"second\\\":"+SECONDE_EVENT+"},\\\"createDate_ddmmyyyy_dot\\\":\\\""+DAY_EVENT+"."+MONTH_EVENT+"."+YEAR_EVENT+"\\\",\\\"createDate_ddmmyyyy_slash\\\":\\\""+DAY_EVENT+"/"+MONTH_EVENT+"/"+YEAR_EVENT+"\\\",\\\"createDate_ddmmyyyy_dash\\\":\\\""+DAY_EVENT+"-"+MONTH_EVENT+"-"+YEAR_EVENT+"\\\",\\\"createDate_mmddjyyyy_slash\\\":\\\""+MONTH_EVENT+"/"+DAY_EVENT+"/"+YEAR_EVENT+"\\\",\\\"formattedEvent_fr\\\":\\\"\\\\u003cdiv class\\\\u003d\\\\u0027event-message\\\\u0027\\\\u003e"+MESSAGE_EVENT+"\\\\u003cdiv class\\\\u003d\\\\u0027message-content\\\\u0027\\\\u003e"+FRAMEWORK_EVENT+" - "+objectTypeDescription_EVENT+" - "+SUB_EVENT+"\\\\u003c/div\\\\u003e\\\\u003c/div\\\\u003e\\\",\\\"formattedEvent_de\\\":\\\"\\\\u003cdiv class\\\\u003d\\\\u0027event-message\\\\u0027\\\\u003e"+MESSAGE_EVENT+"\\\\u003cdiv class\\\\u003d\\\\u0027message-content\\\\u0027\\\\u003e"+FRAMEWORK_EVENT+" - "+objectTypeDescription_EVENT+" - "+SUB_EVENT+"\\\\u003c/div\\\\u003e\\\\u003c/div\\\\u003e\\\",\\\"formattedEvent_it\\\":\\\"\\\\u003cdiv class\\\\u003d\\\\u0027event-message\\\\u0027\\\\u003e"+MESSAGE_EVENT+"\\\\u003cdiv class\\\\u003d\\\\u0027message-content\\\\u0027\\\\u003e"+FRAMEWORK_EVENT+" - "+objectTypeDescription_EVENT+" - "+SUB_EVENT+"\\\\u003c/div\\\\u003e\\\\u003c/div\\\\u003e\\\",\\\"formattedEvent_en\\\":\\\"\\\\u003cdiv class\\\\u003d\\\\u0027event-message\\\\u0027\\\\u003e"+MESSAGE_EVENT+"\\\\u003cdiv class\\\\u003d\\\\u0027message-content\\\\u0027\\\\u003e"+FRAMEWORK_EVENT+" - "+objectTypeDescription_EVENT+" - "+SUB_EVENT+"\\\\u003c/div\\\\u003e\\\\u003c/div\\\\u003e\\\"}\",\"objectSecurityUserNameList\":[],\"score\":17.3295,\"childrenVisibility\":true}",
              "XFRAMEWORK-EVENT.BusinessOperation.softwareDescription_fr":f"{LOGICIEL_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.objectType":f"{objectTypeDescription_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.objectTypeDescription_fr":f"{objectTypeDescription_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.createDate_ddmmyyyy_slash":f"{DAY_EVENT}/{MONTH_EVENT}/{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.objectTypeDescription_en":f"{objectTypeDescription_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.timestamp.hourOfDay":[f"{HOUR_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.environment":f"{TENANT_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.DateTime.month":[f"{MONTH_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.softwareDescription_en":f"{LOGICIEL_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.softwareDescription_de":f"{LOGICIEL_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.DateTime.minute":[f"{MINUTE_EVENT}"],
              "objectSourceName":f"{TENANT_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.typeDescription_it":f"{TYPE_EVENT}",
              "modificationDate_mmddyyyy_slash":f"{MONTH_EVENT}/{DAY_EVENT}/{YEAR_EVENT}",
              "creationUserFullName":f"{USER_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.userFullName":f"{USER_EVENT}",
              "creationDate_mmddyyyy_slash":f"{MONTH_EVENT}/{DAY_EVENT}/{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.objectTypeDescription_de":f"{objectTypeDescription_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.createDate_mmddjyyyy_slash":f"{MONTH_EVENT}/{DAY_EVENT}/{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.DateTime.year":[f"{YEAR_EVENT}"],
              "objectType":"BusinessOperation",
              "XFRAMEWORK-EVENT.BusinessOperation.DateTime.hourOfDay":[f"{HOUR_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.categoryDescription_de":f"{CATEGORIE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.typeDescription_fr":f"{TYPE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.categoryDescription_en":f"{CATEGORIE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.objectSubTypeDescription_de":f"{SUB_EVENT}",
              "objectFilterDate":f"{YEAR_EVENT}-{MONTH_EVENT}-{DAY_EVENT}T{HOUR_EVENT}:{MINUTE_EVENT}:{SECONDE_EVENT}Z",
              "XFRAMEWORK-EVENT.BusinessOperation.userName":f"{USER_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.objectTypeDescription_it":f"{objectTypeDescription_EVENT}",
              "creationTime":[f"{HOUR_EVENT}{MINUTE_EVENT}{SECONDE_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.objectSubTypeDescription_fr":f"{SUB_EVENT}",
              "modificationUserName":f"{USER_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.typeDescription_en":f"{TYPE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.createDate_ddmmyyyy_dash":f"{DAY_EVENT}-{MONTH_EVENT}-{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.typeDescription_de":f"{TYPE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.DateTime.second":[f"{SECONDE_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.objectSubTypeDescription_en":f"{SUB_EVENT}",
              "objectKeyValues":[f"#EVENT_CATEGORY#{CATEGORIE_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.severityDescription_fr":"0",
              "XFRAMEWORK-EVENT.BusinessOperation.timestamp.month":[f"{MONTH_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.severityDescription_de":"0",
              "XFRAMEWORK-EVENT.BusinessOperation.status":f"{STATUS_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.severityDescription_en":"0",
              "softwareCode":f"XFRAMEWORK-EVENT",
              "XFRAMEWORK-EVENT.BusinessOperation.createDate_ddmmyyyy_dot":f"{DAY_EVENT}.{MONTH_EVENT}.{YEAR_EVENT}",
              "modificationDate_ddmmyyyy_dot":f"{DAY_EVENT}.{MONTH_EVENT}.{YEAR_EVENT}",
              "objectSubType":"",
              "creationDate":f"{YEAR_EVENT}{MONTH_EVENT}{DAY_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.softwareDescription_it":f"{LOGICIEL_EVENT}",
              "objectId":f"{ID_EVENT}",
              "creationDate_ddmmyyyy_slash":f"{DAY_EVENT}/{MONTH_EVENT}/{YEAR_EVENT}",
              "modificationTime":[f"{HOUR_EVENT}{MINUTE_EVENT}{SECONDE_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.type":f"{TYPE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.category":f"{CATEGORIE_EVENT}",
              "creationUserName":f"{USER_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.formattedEvent_it":f"<div class='event-message'>{MESSAGE_EVENT}<div class='message-content'>{FRAMEWORK_EVENT} - {objectTypeDescription_EVENT} - {SUB_EVENT}</div></div>",
              "XFRAMEWORK-EVENT.BusinessOperation.timestamp.year":[f"{YEAR_EVENT}"],
              "modificationDate_ddmmyyyy_slash":f"{DAY_EVENT}/{MONTH_EVENT}/{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.source":f"XECM",
              "objectSourceUri":"",
              "XFRAMEWORK-EVENT.BusinessOperation.softwareCode":f"{SOFTWARE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.message":f"{MESSAGE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.severity":"0",
              "XFRAMEWORK-EVENT.BusinessOperation.timestamp.minute":[f"{MINUTE_EVENT}"],
              "creationDate_ddmmyyyy_dot":f"{DAY_EVENT}.{MONTH_EVENT}.{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.severityDescription_it":"0",
              "creationDate_ddmmyyyy_dash":f"{DAY_EVENT}-{MONTH_EVENT}-{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.timestamp.second":[f"{SECONDE_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.statusDescription_de":f"{STATUS_DESC}",
              "XFRAMEWORK-EVENT.BusinessOperation.categoryDescription_it":f"{CATEGORIE_EVENT}",
              "objectSourceType":f"XFRAMEWORK-EVENT",
              "modificationUserFullName":f"{USER_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.categoryDescription_fr":f"{CATEGORIE_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.formattedEvent_de":f"<div class='event-message'>{MESSAGE_EVENT}<div class='message-content'>{FRAMEWORK_EVENT} - {objectTypeDescription_EVENT} - {SUB_EVENT}</div></div>",
              "XFRAMEWORK-EVENT.BusinessOperation.objectSubTypeDescription_it":f"{SUB_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.statusDescription_en":f"{STATUS_DESC}",
              "XFRAMEWORK-EVENT.BusinessOperation.server":f"{SERVEUR}",
              "XFRAMEWORK-EVENT.BusinessOperation.DateTime.dayOfMonth":[f"{DAY_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.formattedEvent_fr":f"<div class='event-message'>{MESSAGE_EVENT}<div class='message-content'>{FRAMEWORK_EVENT} - {objectTypeDescription_EVENT} - {SUB_EVENT}</div></div>",
              "XFRAMEWORK-EVENT.BusinessOperation.statusDescription_fr":f"{STATUS_DESC}",
              "XFRAMEWORK-EVENT.BusinessOperation.subTypeDescription_de":f"{SUB_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.subTypeDescription_fr":f"{SUB_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.subTypeDescription_it":f"{SUB_EVENT}",
              "modificationDate_ddmmyyyy_dash":f"{DAY_EVENT}-{MONTH_EVENT}-{YEAR_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.formattedEvent_en":f"<div class='event-message'>{MESSAGE_EVENT}<div class='message-content'>{FRAMEWORK_EVENT} - {objectTypeDescription_EVENT} - {SUB_EVENT}</div></div>",
              "XFRAMEWORK-EVENT.BusinessOperation.groupId":"0000000000000000",
              "XFRAMEWORK-EVENT.BusinessOperation.timestamp.dayOfMonth":[f"{DAY_EVENT}"],
              "XFRAMEWORK-EVENT.BusinessOperation.objectSubType":f"{SUB_EVENT}",
              "modificationDate":f"{YEAR_EVENT}{MONTH_EVENT}{DAY_EVENT}",
              "XFRAMEWORK-EVENT.BusinessOperation.statusDescription_it":f"{STATUS_DESC}"
            }
            
            
            # Préparer le payload pour Solr
            payload = {
                "add": {
                    "doc": event_message,
                    "commitWithin": 1000  # Commit automatique après 1 seconde
                }
            }
            
            # Envoyer la requête avec authentification
            response = requests.post(
                self.update_url,
                json=payload,
                timeout=self.timeout,
                auth=self.auth,
                headers={"Content-Type": "application/json"},
                verify=self.verify_ssl
            )
            
            # Vérifier le statut
            if response.status_code == 200:
                result = response.json()
                if result.get("responseHeader", {}).get("status") == 0:
                    return {
                        "error": False,
                        "return": f"GOOD"
                        }
                else:
                    return {
                        "error": True,
                        "return": f"ERROR : Erreur Solr: {result}"
                    }
            elif response.status_code == 401:
                return {
                        "error": True,
                        "return": f"ERROR : Erreur d'authentification: identifiants invalides"
                    }
            elif response.status_code == 403:
                return {
                        "error": True,
                        "return": f"ERROR : Accès refusé: permissions insuffisantes"
                    }
            else:
                return {
                    "error": True,
                    "return": f"ERROR : Erreur HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                    "error": True,
                    "return": f"ERROR : {e}"
                }
                
    def test_connection(self) -> bool:
        """
        Teste la connexion au serveur Solr.
        
        Returns:
            True si la connexion est établie, False sinon
        """
        try:
            test_url = f"{self.solr_url}/solr/admin/cores"
            response = requests.get(
                test_url,
                timeout=self.timeout,
                auth=self.auth,
                verify=self.verify_ssl
            )
            
            if response.status_code == 200:
                return {
                    "error": False,
                    "return": f"Connexion Solr réussie"
                }
            elif response.status_code == 401:
                return {
                    "error": True,
                    "return": f"Erreur d'authentification"
                }
            else:
                return {
                    "error": True,
                    "return": f"Erreur de connexion: {response.status_code}"
                }
                
        except Exception as e:
            return {
                    "error": True,
                    "return": f"ERROR : {e}"
                }