import pyodbc
import requests
from requests.auth import HTTPBasicAuth

class SolrConnection: #classe de connexion solr
    def __init__(self, hostname,username, password, tenant, verif_ssl, debug):
        
        self.hostname = hostname
        self.username = username
        self.password = password
        self.tenant = tenant
        self.verif_ssl = verif_ssl
        self.debug = debug
    
    def SolrCount(self, query, rows): # Connexion au SGBD
        if self.debug : print(f"> SolrSearch > ")
        try :
            response = requests.get(
                f"https://{self.hostname}/solr/{self.tenant}/select",
                params={'q': query, 'rows': rows},
                auth=HTTPBasicAuth(self.username, self.password),
                verify=False  # Désactiver la vérification SSL
            )
            
            response.raise_for_status()  # Vérifier si la requête a réussi
            
            if self.debug : print(f"> SolrSearch > {response.status_code}")
            if self.debug : print(f"> SolrSearch > {response.json()}")
            if response.status_code == 200:
                total = response.json()['response']['numFound']
                return {
                        "error": False,
                        "return": total
                        }
            else :
                return {
                        "error": True,
                        "return": response.status_code
                        }
                        
        except Exception as e:
            
            if self.debug : print(f"> SolrSearch > {e}")
            
            return {
                    "error": True,
                    "return": f"{e}"
                    }
                    
                    
    def SolrVerifFOLDER(self, query): # Connexion au SGBD
        
        if self.debug : print(f"> SolrSearch > ")
        try :
            response = requests.get(
                f"https://{self.hostname}/solr/{self.tenant}/select",
                params={'q': query},
                auth=HTTPBasicAuth(self.username, self.password),
                verify=False  # Désactiver la vérification SSL
            )
            response.raise_for_status()  # Vérifier si la requête a réussi
            if self.debug : print(f"> SolrSearch > {response.status_code}")
            if self.debug : print(f"> SolrSearch > {response.json()}")
            if response.status_code == 200:
                if response.json()["response"]["numFound"] == 0 :
                    return {
                        "error": True,
                        "return": "N'existe pas"
                        }
                else :
                    return {
                        "error": False,
                        "return": response
                        }
            else :
                return {
                        "error": True,
                        "return": response.status_code
                        }
                        
        except Exception as e:
            
            if self.debug : print(f"> SolrSearch > {e}")
            
            return {
                    "error": True,
                    "return": f"{e}"
                    }     
                    
                    
                    
    
    def SolrListeID(self, query, rows, debut): # Connexion au SGBD
        
        if self.debug : print(f"> SolrSearch > ")
        try :
            response = requests.get(
                f"https://{self.hostname}/solr/{self.tenant}/select",
                params={'q': query, 'fl' : 'id', 'rows': rows,'sort': 'id ASC'},
                auth=HTTPBasicAuth(self.username, self.password),
                verify=False  # Désactiver la vérification SSL
            )
            
            response.raise_for_status()  # Vérifier si la requête a réussi
            
            if self.debug : print(f"> SolrSearch > {response.status_code}")
            if self.debug : print(f"> SolrSearch > {response.json()}")
            if response.status_code == 200:
                return {
                        "error": False,
                        "return": response
                        }
            else :
                return {
                        "error": True,
                        "return": response.status_code
                        }
                        
        except Exception as e:
            
            if self.debug : print(f"> SolrSearch > {e}")
            
            return {
                    "error": True,
                    "return": f"{e}"
                    }
                    
                    
                    
    def SolrListeID_Document_Folder(self, query): # Connexion au SGBD
        
        if self.debug : print(f"> SolrListeID_Document > ")
        #https://ydgluva24q:8984/solr/001/select?q=XECM.Document.folders.item.id:1002&fl=id
        try :
            response = requests.get(
                f"https://{self.hostname}/solr/{self.tenant}/select",
                params={'q': query, 'fl' : 'id'},
                auth=HTTPBasicAuth(self.username, self.password),
                verify=False  # Désactiver la vérification SSL
            )
            
            response.raise_for_status()  # Vérifier si la requête a réussi
            
            if self.debug : print(f"> SolrListeID_Document > {response.status_code}")
            if self.debug : print(f"> SolrListeID_Document > {response.json()}")
            if response.status_code == 200:
                return {
                        "error": False,
                        "return": response
                        }
            else :
                return {
                        "error": True,
                        "return": response.status_code
                        }
                        
        except Exception as e:
            
            if self.debug : print(f"> SolrListeID_Document > {e}")
            
            return {
                    "error": True,
                    "return": f"{e}"
                    }