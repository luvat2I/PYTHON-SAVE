import requests
import json
import urllib
from urllib.parse import urljoin
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timezone

class YdgGroupClass: 
    def __init__(self,ydg_url, ydg_tenant, ydg_user, ydg_password, ydg_timeout, ydg_ssl, kc_url, kc_clientid, kc_clientsecret, kc_realm,kc_timeout, kc_ssl, debug):
        
        self.ydg_url = ydg_url
        self.ydg_tenant = ydg_tenant
        self.ydg_user = ydg_user
        self.ydg_password = ydg_password
        self.ydg_timeout = ydg_timeout
        self.ydg_ssl = ydg_ssl
        self.ydg_token = None
        
        self.kc_url = kc_url
        self.kc_realm = kc_realm
        self.kc_clientid = kc_clientid
        self.kc_clientsecret = kc_clientsecret
        self.kc_granttype = "password"
        self.kc_username = ydg_user
        self.kc_password = ydg_password
        self.kc_timeout = kc_timeout
        self.kc_ssl = kc_ssl
        
        self.debug = debug
        self.token = None
        self.access_token = None
        self.refresh_token = None
        self.expires_in = None
        self.refresh_expires_in = None
        self.token_type = None
        self.scope = None
        
    def recup_barear(self): # recup_token_barear
        if self.debug : print(f">   > ++ > recup_barear")
        try :
            token_url = f"{self.kc_url}/realms/{self.kc_realm}/protocol/openid-connect/token"
            data = {
                "client_id": self.kc_clientid,
                "client_secret": self.kc_clientsecret,
                "username": self.kc_username,
                "password": self.kc_password,
                "grant_type": self.kc_granttype
            }
                
            if self.ydg_ssl:
                result = requests.post(token_url, data=data, timeout=self.kc_timeout)
            else:
                result = requests.post(token_url, data=data, timeout=self.kc_timeout, verify=self.ydg_ssl)
            
            result.raise_for_status()
            self.token = result.json()
            
            
            
            self.access_token = self.token.get("access_token")
            self.refresh_token = self.token.get("refresh_token")
            self.expires_in = self.token.get("expires_in")
            self.refresh_expires_in = self.token.get("refresh_expires_in")
            self.token_type = self.token.get("token_type")
            self.scope = self.token.get("scope")
            self.ydg_token = self.access_token
            
            if self.debug : 
                    print(f">   > ++ > {self.token}")
                    print(f">   > ++ > {self.expires_in}")
            return {
                "error": False,
                "return": self.access_token
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
                
                
    def token_valide(self):
        if self.debug : print(f">   > ++ > token_valide")
        try:
            header = jwt.get_unverified_header(self.ydg_token)
            decoded = jwt.decode(self.ydg_token, options={"verify_signature": False})
            if self.debug : 
                    print(f">   > ++ > token decodé = {decoded}")
            ts = int(decoded['exp'])
            verif_date = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            if self.debug : 
                    print(f">   > ++ > date exp = {verif_date}")
            exp_ts = int(decoded['exp'])
            is_expired = datetime.now(timezone.utc).timestamp() >= exp_ts
            return {
                "error": False,
                "return": is_expired
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
            
    def token_decode(self):
        if self.debug : print(f">   > ++ > token_decode")
        try:
            header = jwt.get_unverified_header(self.ydg_token)
            decoded = jwt.decode(self.ydg_token, options={"verify_signature": False})
            return {
                "error": False,
                "return": decoded
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
    
    
    def admin_group(self,group,action):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        service_context_obj = {
            "userId": self.ydg_user,
            "environmentName": self.ydg_tenant,
            "regionalSettings": "fr",
            "contextualRole": ""
        }
        SERVICE_CONTEXT = urllib.parse.quote(json.dumps(service_context_obj, separators=(",", ":")), safe='')
        check_url = f"{self.ydg_url}/xframework-security-web/rest/group/{group}?serviceContext={SERVICE_CONTEXT}"
        
        if action == "CREATION" :
            check_resp = requests.put(check_url, headers=headers, verify=False, timeout=30)
            check_text = check_resp.text
            if check_resp.status_code == 201 :
                return {
                "error": False,
                "return": f"{group} > Creation groupe > OK"
                }
            else :
                return {
                "error": True,
                "return": f"ERREUR > {check_text}"
                }
            # retour [201]> c bon
        if action == "SUPPRESSION" :
            check_resp = requests.delete(check_url, headers=headers, verify=False, timeout=30)
            check_text = check_resp.text
            if check_resp.status_code == 204 :
                return {
                "error": False,
                "return": f"{group} > Suppression groupe > OK"
                }
            elif check_resp.status_code == 500 :
                return {
                "error": False,
                "return": f"{group} > Suppression groupe > une erreur est survenu ou le groupe n'existe pas"
                }
            else :
                return {
                "error": True,
                "return": f"ERREUR > {check_text}"
                }
        
        return check_text
        
    def verif_group(self,group):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        service_context_obj = {
            "userId": self.ydg_user,
            "environmentName": self.ydg_tenant,
            "regionalSettings": "fr",
            "contextualRole": ""
        }
        SERVICE_CONTEXT = urllib.parse.quote(json.dumps(service_context_obj, separators=(",", ":")), safe='')
        check_url = f"{self.ydg_url}/xframework-security-web/rest/group/{group}?serviceContext={SERVICE_CONTEXT}"
        
        check_resp = requests.get(check_url, headers=headers, verify=False, timeout=30)

        if check_resp.status_code == 200 :
            return {
                "error": False,
                "return": f"{check_resp.status_code}"
            }
        else :
            return {
                "error": True,
                "return": f"ERREUR > {check_resp.status_code}"
            }
            
    def list_group(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        service_context_obj = {
            "userId": self.ydg_user,
            "environmentName": self.ydg_tenant,
            "regionalSettings": "fr",
            "contextualRole": ""
        }
        SERVICE_CONTEXT = urllib.parse.quote(json.dumps(service_context_obj, separators=(",", ":")), safe='')
        ORDER_BY_obj = {"order":[{"field":"name","descending":False},{"field":"displayName","descending":False}]}
        ORDER_BY = urllib.parse.quote(json.dumps(ORDER_BY_obj, separators=(",", ":")), safe='')
        
        
        check_url = f"{self.ydg_url}/xframework-security-web/rest/group?orderBy={ORDER_BY}&serviceContext={SERVICE_CONTEXT}"
        
        check_resp = requests.get(check_url, headers=headers, verify=False, timeout=30)
        
        if check_resp.status_code == 200 :
            
            check_resp.raise_for_status()
            resp = check_resp.json()
            data = resp.get("data", resp)
            
            return {
                "error": False,
                "return": f"{data}"
            }
        else :
            return {
                "error": True,
                "return": f"ERREUR > {check_resp.status_code}"
            }   
        
        