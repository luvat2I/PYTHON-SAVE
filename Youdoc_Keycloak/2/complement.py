import configparser
import os
import sys
import string
DIGITS = '0123456789'          # positions qui acceptent uniquement chiffres si souhaité
ALPHANUM = '0123456789' + string.ascii_uppercase  # 0-9 puis A-Z (36 symboles)

# Ici on assume que chaque caractère suit la même alphabet ALPHANUM.
ALPHABET = ALPHANUM

def get_param(CONFIG_INI,PARAM1,PARAM2) :
    try:
        PARAM = CONFIG_INI[f'{PARAM1}'][f'{PARAM2}']
        return {
                "error": False,
                "return": PARAM
                }
    except Exception as e:
        return {
                "error": True,
                "return": f"ERROR : {e}"
                }
def get_bool_param(CONFIG_INI,PARAM1,PARAM2) :
    try:
        PARAM = CONFIG_INI.getboolean(f'{PARAM1}', f'{PARAM2}')
        return {
                "error": False,
                "return": PARAM
                }
    except Exception as e:
        return {
                "error": True,
                "return": f"ERROR : {e}"
                }
                
def get_CLIENT_ID(CONFIG_INI) :
    try:
        CLIENT_ID = CONFIG_INI['ENTRA_ID']['CLIENT_ID']
    except Exception as e:
        CLIENT_ID = "ERROR"
    return CLIENT_ID

def get_CLIENT_SECRET(CONFIG_INI) :
    try:
        CLIENT_SECRET = CONFIG_INI['ENTRA_ID']['CLIENT_SECRET']
    except Exception as e:
        CLIENT_SECRET = "ERROR"
    return CLIENT_SECRET


def get_token_path():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{script_name}.token")

def get_id_token_path():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{script_name}.id_token")
    
def get_access_token_path():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), f"{script_name}.access_token")
    
def demander_modif_tets():
    while True:
        reponse = input("Réalisez-vous la tâche ? (oui/non) : ").strip().lower()
        if reponse == "oui":
            print("Vous avez répondu oui.")
            break
        elif reponse == "non":
            print("Vous avez répondu non.")
            break
        else:
            print("Veuillez répondre par 'oui' ou 'non'.")


class valideTIMER:
    """
    Classe pour publier des événements XFRAMEWORK vers Solr avec authentification.
    """
    
    def __init__(
        self, 
        SERVICE_HEURE: str, 
        SERVICE_MINUTE: str
    ):
        """
        
        Args:
            
        """
        self.SERVICE_HEURE = SERVICE_HEURE
        self.SERVICE_MINUTE = SERVICE_MINUTE
    
    def getvalide(self, hour_time, minute_time):
        """
        
        """
        try:
            heure_valide = False
            minute_valide = False
            
            if hour_time == 0 :
                hour_time = 24
            if minute_time == 0 :
                minute_time = 60
            
            if self.SERVICE_HEURE == "*" :
                heure_valide = True
            elif self.SERVICE_HEURE.startswith("!") and hour_time == int(self.SERVICE_HEURE[1:]) :
                heure_valide = True
            elif self.SERVICE_HEURE.startswith("*/") :
                divise = int(self.SERVICE_HEURE[2:])
                result = hour_time / divise
                if result == round(result) :
                    heure_valide = True
            else :
                heure_valide = False
                
            if self.SERVICE_MINUTE == "*" :
                minute_valide = True
            elif self.SERVICE_MINUTE.startswith("!") and minute_time == int(self.SERVICE_MINUTE[1:]) :
                minute_valide = True
            elif self.SERVICE_MINUTE.startswith("*/") :
                divise = int(self.SERVICE_MINUTE[2:])
                result = minute_time / divise
                if result == round(result) :
                    minute_valide = True
            else :
                minute_valide = False
                
            if heure_valide and minute_valide : 
                return True
            else :
                return False
            
        except Exception as e:
            return False