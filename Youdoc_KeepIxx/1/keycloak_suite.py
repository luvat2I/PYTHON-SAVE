import requests
import jwt  # PyJWT
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from urllib.parse import urljoin

class Keycloak_youdoc: #classe de connexion SGBD SQL et DB2
    def __init__(self, kc_url,kc_realm,kc_realmclient,kc_clientid,kc_granttype,kc_username,kc_password,kc_timeout,kc_verifssl,kc_debug):
        
        self.kc_url = kc_url
        self.kc_realm = kc_realm
        self.kc_realmclient = kc_realmclient
        self.kc_clientid = kc_clientid
        self.kc_granttype = kc_granttype
        self.kc_username = kc_username
        self.kc_password = kc_password
        self.kc_timeout = kc_timeout
        self.kc_verifssl = kc_verifssl
        self.debug = kc_debug
        self.token = None
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.refresh_expires_in = None
        self.token_type = None
        self.scope = None
        self.kc_client = None
        self.kc_id_client = None

        

    def recup_token_barear(self): # recup_token_barear
        try :
            token_url = f"{self.kc_url}/realms/{self.kc_realm}/protocol/openid-connect/token"
            data = {
                "client_id": self.kc_clientid,
                "username": self.kc_username,
                "password": self.kc_password,
                "grant_type": self.kc_granttype
            }
                
            if self.kc_verifssl:
                result = requests.post(token_url, data=data, timeout=self.kc_timeout)
            else:
                result = requests.post(token_url, data=data, timeout=self.kc_timeout, verify=self.kc_verifssl)
            
            result.raise_for_status()
            self.token = result.json()
            
            
            
            self.access_token = self.token.get("access_token")
            self.refresh_token = self.token.get("refresh_token")
            self.expires_in = self.token.get("expires_in")
            self.refresh_expires_in = self.token.get("refresh_expires_in")
            self.token_type = self.token.get("token_type")
            self.scope = self.token.get("scope")
            
            
            if self.debug : 
                    print(f"")
                    print(f"{self.token}")
                    print(f"")
            return {
                "error": False,
                "return": self.access_token
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
                
    def recup_client_id(self,client):
        try :
            
            if self.access_token :
                self.kc_client = client
                
                token_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/clients"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                result = requests.get(token_url, headers=headers, verify=self.kc_verifssl)
                result.raise_for_status()
                liste_clients = result.json()
                target = self.kc_client
                if self.debug : 
                    print(f"")
                    print(f"{liste_clients}")
                    print(f"")
                self.kc_id_client = next((c["id"] for c in liste_clients if c.get("clientId") == target), None)
                
                if self.debug : print(f"l'id de {self.kc_client} est : {self.kc_id_client}")
                if self.kc_id_client :
                    return {
                        "error": False,
                        "return": self.kc_id_client
                        }
                else :
                    return {
                        "error": True,
                        "return": f"ERREUR > l'id de {self.kc_client} est introuvable sur le realm {self.kc_realmclient} à l'adresse {self.kc_url}"
                        }
                    
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
                
    def admin_role(self,role,action):
        
        if action == "CREATION" :
            NEW_ROLE = {
                "name": f"{role}",
                "description": f"{role}",
                "composite": False,
                "clientRole": True,
                "attributes": {}
            }
        
        role_url = ""
        if action == "CREATION" :
            role_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/clients/{self.kc_id_client}/roles"
        elif action == "SUPPRESSION" :
            role_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/clients/{self.kc_id_client}/roles/{role}"
        
        if action == "CREATION" :
            headers = {"Authorization": f"Bearer {self.access_token}"}
        elif action == "SUPPRESSION" :
            headers = {"Authorization": f"Bearer {self.access_token}","Content-Type": "application/json"}
        
        if action == "CREATION" :
            result = requests.post(role_url, headers=headers, json=NEW_ROLE, verify=self.kc_verifssl)
        elif action == "SUPPRESSION" :
            result = requests.delete(role_url, headers=headers, verify=self.kc_verifssl)
        if self.debug : 
                    print(f"")
                    print(f"{result}")
                    print(f"") 
        if action == "CREATION" :
            if result.status_code == 201:
                return {
                    "error": False,
                    "return": f"{role} > Creation role > OK"
                    }
            elif result.status_code == 409:
                return {
                    "error": False,
                    "return": f"{role} > Creation role > Existe déjà"
                    }
            else :
                return {
                    "error": True,
                    "return": f"ERREUR > {role} > Creation role > {result}"
                    }
        elif action == "SUPPRESSION" :
            if result.status_code == 201 or result.status_code == 204 :
                return {
                    "error": False,
                    "return": f"{role} > Suppression role > OK"
                    }
            elif result.status_code == 404 :
                return {
                    "error": False,
                    "return": f"{role} > Suppression role > impossible un erreur est survenue ou le role n'existe pas"
                    }
                
            else :
                return {
                    "error": True,
                    "return": f"ERREUR > {role} > Suppression role > {result}"
                    }
        