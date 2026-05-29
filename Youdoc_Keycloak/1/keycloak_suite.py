import requests
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timezone
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from urllib.parse import urljoin

class Keycloak_youdoc:
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
            token_url = f"{self.kc_url}/realms/master/protocol/openid-connect/token"
            data = {
                "client_id": "admin-cli",
                "username": self.kc_username,
                "password": self.kc_password,
                "grant_type": "password"
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
                
                
    def token_valide(self):
        if self.debug : print(f">   > ++ > token_valide")
        try:
            header = jwt.get_unverified_header(self.access_token)
            decoded = jwt.decode(self.access_token, options={"verify_signature": False})
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
                    
    def id_role(self,role):
        if self.debug : print(f">   > ++ > id_role")
        try :
            role_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/clients/{self.kc_id_client}/roles"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(role_url, headers=headers, verify=self.kc_verifssl)
            if self.debug : print(f">   > ++ > {result}")
            result.raise_for_status()
            kc_roles = result.json()
            if self.debug : print(f">   > ++ > {kc_roles}")
            kc_role = next((ro for ro in kc_roles if ro["name"] == role), None)
            if self.debug : print(f">   > ++ > {kc_role}")
            if not kc_role:
                return {
                    "error": True,
                    "return": f"ERREUR > role {role} non trouvé"
                    }
            else :
                if self.debug : print(f">   > ++ > {kc_role["id"]}")
                return {
                    "error": False,
                    "return": kc_role["id"]
                    }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
                
    def recup_identity_provider(self,alias):
        if self.debug : print(f">   > ++ > recup_identity_provider")
        try :
            idp_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/identity-provider/instances/{alias}"
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(idp_url, headers=headers, verify=self.kc_verifssl)
            if self.debug : print(f">   > ++ > {result}")
            if result.status_code == 200:
                result.raise_for_status()
                kc_idp = result.json()
                if self.debug : print(f">   > ++ > {kc_idp["internalId"]}")
                return {
                    "error": False,
                    "return": kc_idp["internalId"]
                    }
            else :
                if self.debug : print(f">   > ++ > {result}")
                return {
                    "error": True,
                    "return": f"ERREUR > {result}"
                    }
                
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
        
    def admin_mapper(self,IDP_ALIAS,CLIENT,mapper,role,idazure,idmapper,action):

        if action == "CREATION" :
            NEW_MAPPER = {
                "name": f"{mapper}",
                "identityProviderAlias": f"{IDP_ALIAS}",
                "identityProviderMapper": "oidc-role-idp-mapper",
                "config": {
                    "claim": "groups",
                    "claim.value": f"{idazure}",
                    "role": f"{CLIENT}.{role}",
                    "sync.mode": "INHERIT" 
                }
            }

        mapper_url = ""
        if action == "CREATION" :
            mapper_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/identity-provider/instances/{IDP_ALIAS}/mappers"
        elif action == "SUPPRESSION" :
            mapper_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/identity-provider/instances/{IDP_ALIAS}/mappers/{idmapper}"
            
        if action == "CREATION" :
            headers = {"Authorization": f"Bearer {self.access_token}"}
        elif action == "SUPPRESSION" :
            headers = {"Authorization": f"Bearer {self.access_token}","Content-Type": "application/json"}
        
        if action == "CREATION" :
            result = requests.post(mapper_url, headers=headers, json=NEW_MAPPER, verify=self.kc_verifssl)
        elif action == "SUPPRESSION" :
            result = requests.delete(mapper_url, headers=headers, verify=self.kc_verifssl)
            
        if self.debug : print(f"{result}")
        if action == "CREATION" :
            if result.status_code == 201:
                return {
                    "error": False,
                    "return": f"{mapper} > Creation mapper > OK"
                    }
            elif result.status_code == 400:
                return {
                    "error": False,
                    "return": f"{mapper} > Creation mapper > Existe déjà"
                    }
            else :
                return {
                    "error": True,
                    "return": f"ERREUR > {mapper} > Creation mapper > {result}"
                    }
        elif action == "SUPPRESSION" :
            if result.status_code == 201 or result.status_code == 204 :
                return {
                    "error": False,
                    "return": f"{mapper} > Suppression mapper > OK"
                    }
            elif result.status_code == 404 :
                return {
                    "error": False,
                    "return": f"{mapper} > Suppression mapper > impossible un erreur est survenue ou le mapper n'existe pas"
                    }
                
            else :
                return {
                    "error": True,
                    "return": f"ERREUR > {mapper} > Suppression mapper > {result}"
                    }        
        
    def id_mapper(self,IDP_ALIAS,mapper):
        if self.debug : print(f">   > ++ > id_mapper")
        try :
            mappers_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/identity-provider/instances/{IDP_ALIAS}/mappers"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(mappers_url, headers=headers, verify=self.kc_verifssl)
            if self.debug : print(f">   > ++ > {result}")
            result.raise_for_status()
            kc_mappers = result.json()
            if self.debug : print(f">   > ++ > {kc_mappers}")
            kc_mapper = next((ro for ro in kc_mappers if ro["name"] == mapper), None)
            if self.debug : print(f">   > ++ > {kc_role}")
            if not kc_mapper:
                return {
                    "error": False,
                    "return": f"{mapper} > Suppression mapper > impossible un erreur est survenue ou le mapper n'existe pas"
                    }
            else :
                if self.debug : print(f">   > ++ > {kc_mapper["id"]}")
                return {
                    "error": False,
                    "return": kc_mapper["id"]
                    }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
 
    def verif_REALM(self):
        if self.debug : print(f">   > ++ > verif_realm")
        try :
            
            realm_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}"
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            if self.kc_verifssl:
                result = requests.get(realm_url, headers=headers, timeout=self.kc_timeout)
            else:
                result = requests.get(realm_url, headers=headers, timeout=self.kc_timeout, verify=self.kc_verifssl)
                
            if self.debug : print(f"{result.raise_for_status()}")
            
            if result.status_code == 200 or result.status_code == 401:
                return {
                "error": False,
                "return": result.raise_for_status()
                }
            else:
                return {
                "error": True,
                "return": result.raise_for_status()
                }
                
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }

    def verif_CLIENT(self,CLIENT):
        if self.debug : print(f">   > ++ > verif_realm")
        try :
            
            realm_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/clients"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            if self.kc_verifssl:
                result = requests.get(realm_url, headers=headers, timeout=self.kc_timeout)
            else:
                result = requests.get(realm_url, headers=headers, timeout=self.kc_timeout, verify=self.kc_verifssl)
            
            result.raise_for_status()
            kc_clients = result.json()
            if self.debug : print(f">   > ++ > {kc_clients}")

            kc_client = next((ro for ro in kc_clients if ro["name"] == CLIENT), None)
            if self.debug : print(f">   > ++ > {kc_client}")

            if not kc_client:
                return {
                "error": True,
                "return": ""
                }
                
            else :
                
                return {
                "error": False,
                "return": kc_clients
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }         
                
    def verif_IDP(self,IDP_ALIAS):
        if self.debug : print(f">   > ++ > verif_idp")
        try :
            idp_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/identity-provider/instances/"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(idp_url, headers=headers, verify=self.kc_verifssl)
            if self.debug : print(f">   > ++ > {result}")
            result.raise_for_status()
            kc_idps = result.json()
            if self.debug : print(f">   > ++ > {kc_idps}")
            kc_idp = next((ro for ro in kc_idps if ro["alias"] == IDP_ALIAS), None)
            if self.debug : print(f">   > ++ > {kc_idp}")
            if not kc_idp:
                return {
                "error": True,
                "return": kc_idp
                }
            else :
                return {
                "error": False,
                "return": kc_idp
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }

    def liste_role(self):
        try :
            role_url = ""
            role_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/clients/{self.kc_id_client}/roles"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(role_url, headers=headers, verify=self.kc_verifssl)
            if self.debug : print(f"{result}") 
            
            result.raise_for_status()
            resp = result.json()
            return {
                "error": False,
                "return": f"{resp}"
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
                
    def liste_mapper(self,IDP_ALIAS):
        try :
            role_url = ""
            mapper_url = f"{self.kc_url}/admin/realms/{self.kc_realmclient}/identity-provider/instances/{IDP_ALIAS}/mappers"
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            result = requests.get(mapper_url, headers=headers, verify=self.kc_verifssl)
            if self.debug : print(f"{result}") 
            result.raise_for_status()
            resp = result.json()
            return {
                "error": False,
                "return": f"{resp}"
                }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
                }
            