from datetime import date
import random

def chiffre_date(position):
    """
    Retourne le chiffre (int) à la position donnée dans la représentation ISO de la date (YYYY-MM-DD)
    Positions indexées à partir de 0 sur la suite des chiffres uniquement.
    Ex : pour 2025-12-09, chiffres = ['2','0','2','5','1','2','0','9']
    chiffre_date(0) -> 2, chiffre_date(1) -> 0, etc.
    Retourne None si la position est hors limites ou si position < 0.
    """
    if position < 0:
        return None
    chiffres = [c for c in date.today().isoformat() if c.isdigit()]
    return int(chiffres[position]) if position < len(chiffres) else None
    

def chiffre_data(position,data):
    """
    Retourne le chiffre (int) à la position donnée dans la représentation ISO de la date (YYYY-MM-DD)
    Positions indexées à partir de 0 sur la suite des chiffres uniquement.
    Ex : pour 2025-12-09, chiffres = ['2','0','2','5','1','2','0','9']
    chiffre_date(0) -> 2, chiffre_date(1) -> 0, etc.
    Retourne None si la position est hors limites ou si position < 0.
    """
    if position < 0:
        return None
    chiffres = [c for c in data if c.isdigit()]
    return int(chiffres[position]) if position < len(chiffres) else None

def chiffre_lic(position,licence):
    """
    Retourne le chiffre (int) à la position donnée dans la représentation ISO de la date (YYYY-MM-DD)
    Positions indexées à partir de 0 sur la suite des chiffres uniquement.
    Ex : pour 2025-12-09, chiffres = ['2','0','2','5','1','2','0','9']
    chiffre_date(0) -> 2, chiffre_date(1) -> 0, etc.
    Retourne None si la position est hors limites ou si position < 0.
    """
    if position < 0:
        return None
    chiffres = [c for c in licence if c.isdigit()]
    return int(chiffres[position]) if position < len(chiffres) else None

def luva_lic_calcul(type,annee,mois,jour,duree,DEV):
    
    """
    type = AN
    type = MOIS
    type = JOURS
    type = DUREE
    
    """
    if DEV : print(f"Config > {type} {annee} {mois} {jour} {duree}")
    
    error = False
    ID_APP = "LIC001"
    
    nombre_inutil = str(random.randint(1, 9))  # Nombre random  : 1 à 9

    if type == "DUREE" :
        ANNEE_3 = chiffre_data(2,annee)
        ANNEE_4 = chiffre_data(3,annee)
        NB_DUREE_calcul = ANNEE_3 + ANNEE_4
        
        if len(str(NB_DUREE_calcul)) < 2 :
            NB_DUREE_2 = random.randint(0, 4)  # Nombre random : 1 à 4
        else :
            NB_DUREE_2 = random.randint(5, 9)  # Nombre random : 5 à 9
    else :
        NB_DUREE_2 = random.randint(1, 9)  # Nombre random : 5 à 9
        
    nombreW = random.randint(1, 9)  # Nombre random  : 1 à 9
    nombreX = random.randint(1, 9)  # Nombre random  : 1 à 9
    nombreY = random.randint(1, 9)  # Nombre random  : 1 à 9
    nombreZ = random.randint(1, 9)  # Nombre random  : 1 à 9
    
    if type == "DUREE" :
        NB_DUREE_1 = random.randint(5, 9)  # Nombre random : 5 à 9
    else : 
        NB_DUREE_1 = random.randint(0, 4)  # Nombre random : 1 à 4
    
    if DEV : print(f"{NB_DUREE_1}")    
    if DEV : print(f"{nombre_inutil}")
    if DEV : print(f"{NB_DUREE_2}")
    if DEV : print(f"{nombreW}")
    if DEV : print(f"{nombreX}")
    
    if type == "DUREE" :
        NB_DUREE_0 = int(duree) + int(nombreW) + int(nombreX) + int(nombreY) + int(nombreZ) + 10
    else :
        NB_DUREE_0 = random.randint(10, 54)  # Nombre random  : 1 à 9
    if DEV : print(f"{NB_DUREE_0}")
    
    if type == "AN" or  type == "MOIS" or  type == "JOURS" or  type == "DUREE" :    
        
        ANNEE_1 = chiffre_data(0,annee)
        ANNEE_2 = chiffre_data(1,annee)
        ANNEE_3 = chiffre_data(2,annee)
        ANNEE_4 = chiffre_data(3,annee)
        
        LIC_AN_1 = int(ANNEE_1) + int(nombreW) + int(nombreX) * 2
        LIC_AN_2 = int(ANNEE_2) + int(nombreW) + int(nombreY) * 3
        LIC_AN_3 = int(ANNEE_3) + int(nombreW) + int(nombreZ) * 2
        LIC_AN_4 = int(ANNEE_4) + int(nombreY) + int(nombreZ) * 3 
        
        if DEV : print(f"{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}")
        
    if type == "MOIS" or  type == "JOURS" :
        
        MOIS_1 = chiffre_data(0,mois)
        MOIS_2 = chiffre_data(1,mois)
        
        LIC_MOIS_1 = MOIS_1 + nombreW + nombreX * 2
        LIC_MOIS_2 = MOIS_2 + nombreW + nombreY * 3
        
        if DEV : print(f"{LIC_MOIS_1}{LIC_MOIS_2}")
    
    if type == "JOURS" :
        
        JOURS_1 = chiffre_data(0,jour)
        JOURS_2 = chiffre_data(1,jour)
        
        LIC_JOURS_1 = JOURS_1 + nombreW + nombreZ * 2
        LIC_JOURS_2 = JOURS_2 + nombreY + nombreZ * 3 
        
        if DEV : print(f"{LIC_JOURS_1}{LIC_JOURS_2}")
    
    if type == "DUREE" :
        
        NB_DUREE_calcul = ANNEE_3 + ANNEE_4
        
        NB_DUREE_3 = NB_DUREE_calcul
        
        if DEV : print(f"{NB_DUREE_3}")
    
    NB_DUREE_4 = ANNEE_4
    if DEV : print(f"{NB_DUREE_4}")
    
    if DEV : print(f"{nombreY}")
    if DEV : print(f"{nombreZ}")
        
    if type == "AN" :
        LICENCE = f"{NB_DUREE_1}{nombre_inutil}"
        LICENCE = f"{LICENCE}{NB_DUREE_2}"
        LICENCE = f"{LICENCE}{nombreW}{nombreX}"
        LICENCE = f"{LICENCE}{NB_DUREE_0}"
        LICENCE = f"{LICENCE}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
        LICENCE = f"{LICENCE}{NB_DUREE_4}"
        LICENCE = f"{LICENCE}{nombreY}{nombreZ}"
        
    if type == "MOIS" :
        LICENCE = f"{NB_DUREE_1}{nombre_inutil}"
        LICENCE = f"{LICENCE}{NB_DUREE_2}"
        LICENCE = f"{LICENCE}{nombreW}{nombreX}"
        LICENCE = f"{LICENCE}{NB_DUREE_0}"
        LICENCE = f"{LICENCE}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
        LICENCE = f"{LICENCE}{LIC_MOIS_1}{LIC_MOIS_2}"
        LICENCE = f"{LICENCE}{NB_DUREE_4}"
        LICENCE = f"{LICENCE}{nombreY}{nombreZ}"
        
    if type == "JOURS" :
        LICENCE = f"{NB_DUREE_1}{nombre_inutil}"
        LICENCE = f"{LICENCE}{NB_DUREE_2}"
        LICENCE = f"{LICENCE}{nombreW}{nombreX}"
        LICENCE = f"{LICENCE}{NB_DUREE_0}"
        LICENCE = f"{LICENCE}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
        LICENCE = f"{LICENCE}{LIC_MOIS_1}{LIC_MOIS_2}"
        LICENCE = f"{LICENCE}{LIC_JOURS_1}{LIC_JOURS_2}"
        LICENCE = f"{LICENCE}{NB_DUREE_4}"
        LICENCE = f"{LICENCE}{nombreY}{nombreZ}"
        
    if type == "DUREE" :
        LICENCE = f"{NB_DUREE_1}{nombre_inutil}"
        LICENCE = f"{LICENCE}{NB_DUREE_2}"
        LICENCE = f"{LICENCE}{nombreW}{nombreX}"
        LICENCE = f"{LICENCE}{NB_DUREE_0}"
        LICENCE = f"{LICENCE}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
        LICENCE = f"{LICENCE}{NB_DUREE_3}"
        LICENCE = f"{LICENCE}{NB_DUREE_4}"
        LICENCE = f"{LICENCE}{nombreY}{nombreZ}"
        
    if DEV : print(f"{LICENCE}")
    return LICENCE
        
def valide_licence(LICENCE_CLIENT,DEV):
    VALIDE = False
    
    try:
        DATE_TODAY = date.today().isoformat()
        
        if DEV : print(f"DATE_TODAY = {DATE_TODAY}")
        if DEV : print(f"LICENCE = {LICENCE_CLIENT}")
        
        NB_DUREE_1 = chiffre_lic(0,LICENCE_CLIENT)
        
        if DEV : print(f"Savoir si DUREE > {NB_DUREE_1}")
        if NB_DUREE_1 > 5 :
            TYPE = "DUREE"
        else :
            TYPE = "AUTRE"
        if DEV : print(f"TYPE > {TYPE}")
        
        nombre_inutil = chiffre_lic(1,LICENCE_CLIENT)
        if DEV : print(f"nombre_inutil > {nombre_inutil}")
        
        NB_DUREE_2 = chiffre_lic(2,LICENCE_CLIENT)
        if DEV : print(f"NB_DUREE_2 > {NB_DUREE_2}")
        
        nombreW = chiffre_lic(3,LICENCE_CLIENT)
        if DEV : print(f"nombreW > {nombreW}")
        
        nombreX = chiffre_lic(4,LICENCE_CLIENT)
        if DEV : print(f"nombreX > {nombreX}")
        
        nombreY = chiffre_lic((len(str(LICENCE_CLIENT))-2),LICENCE_CLIENT)
        if DEV : print(f"nombreY > {nombreY}")
        
        nombreZ = chiffre_lic((len(str(LICENCE_CLIENT))-1),LICENCE_CLIENT)
        if DEV : print(f"nombreZ > {nombreZ}")
        
        NB_DUREE_0_1 = chiffre_lic(5,LICENCE_CLIENT)
        NB_DUREE_0_2 = chiffre_lic(6,LICENCE_CLIENT)
        NB_DUREE_0 = f"{NB_DUREE_0_1}{NB_DUREE_0_2}"
        
        NB_DUREE_4 = chiffre_lic((len(str(LICENCE_CLIENT))-3),LICENCE_CLIENT)
            
        if TYPE == "DUREE" and NB_DUREE_2 < 5:
            NB_DUREE_3 = chiffre_lic((len(str(LICENCE_CLIENT))-4),LICENCE_CLIENT)
            if DEV : print(f"NB_DUREE_3 > {NB_DUREE_3}")
        if TYPE == "DUREE" and NB_DUREE_2 > 5:
            NB_DUREE_3_1 = chiffre_lic((len(str(LICENCE_CLIENT))-5),LICENCE_CLIENT)
            NB_DUREE_3_2 = chiffre_lic((len(str(LICENCE_CLIENT))-4),LICENCE_CLIENT)
            NB_DUREE_3 = f"{NB_DUREE_3_1}{NB_DUREE_3_2}"
            
            if DEV : print(f"NB_DUREE_3 > {NB_DUREE_3}")
        
        if TYPE == "DUREE" :
            NB_DUREE_3 = NB_DUREE_3 - NB_DUREE_4
            ANNEE_DEBUT = f"20{NB_DUREE_3}{NB_DUREE_4}"
            if DEV : print(f"ANNEE_DEBUT > {ANNEE_DEBUT}")
            
            ANNEE_FIN = str(int(ANNEE_DEBUT) +  int(NB_DUREE_2))
        
        ANNEE_1 = chiffre_data(0,DATE_TODAY)
        ANNEE_2 = chiffre_data(1,DATE_TODAY)
        ANNEE_3 = chiffre_data(2,DATE_TODAY)
        ANNEE_4 = chiffre_data(3,DATE_TODAY)
        ANNNEE = int(f"{ANNEE_1}{ANNEE_2}{ANNEE_3}{ANNEE_4}")
        
        if TYPE == "AUTRE" :
            
            ANNEE_1 = int(chiffre_data(0,DATE_TODAY))
            ANNEE_2 = chiffre_data(1,DATE_TODAY)
            ANNEE_3 = chiffre_data(2,DATE_TODAY)
            ANNEE_4 = chiffre_data(3,DATE_TODAY)
            
            LIC_AN_1 = int(ANNEE_1) + int(nombreW) + int(nombreX) * 2
            LIC_AN_2 = int(ANNEE_2) + int(nombreW) + int(nombreY) * 3
            LIC_AN_3 = int(ANNEE_3) + int(nombreW) + int(nombreZ) * 2
            LIC_AN_4 = int(ANNEE_4) + int(nombreY) + int(nombreZ) * 3 
            
            MOIS_1 = chiffre_data(4,DATE_TODAY)
            MOIS_2 = chiffre_data(5,DATE_TODAY)

            LIC_MOIS_1 = int(MOIS_1) + int(nombreW) + int(nombreX) * 2
            LIC_MOIS_2 = int(MOIS_2) + int(nombreW) + int(nombreY) * 3
            
            JOURS_1 = int(chiffre_data(6,DATE_TODAY))
            JOURS_2 = chiffre_data(7,DATE_TODAY)
            
            LIC_JOURS_1 = int(JOURS_1) + int(nombreW) + int(nombreZ) * 2
            LIC_JOURS_2 = int(JOURS_2) + int(nombreY) + int(nombreZ) * 3 
            
            LICENCE_AN = f"{NB_DUREE_1}{nombre_inutil}"
            LICENCE_AN = f"{LICENCE_AN}{NB_DUREE_2}"
            LICENCE_AN = f"{LICENCE_AN}{nombreW}{nombreX}"
            LICENCE_AN = f"{LICENCE_AN}{NB_DUREE_0}"
            LICENCE_AN = f"{LICENCE_AN}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
            LICENCE_AN = f"{LICENCE_AN}{NB_DUREE_4}"
            LICENCE_AN = f"{LICENCE_AN}{nombreY}{nombreZ}"
            
            if DEV : print(f"LICENCE_AN : {LICENCE_AN}")
            
            LICENCE_MOIS = f"{NB_DUREE_1}{nombre_inutil}"
            LICENCE_MOIS = f"{LICENCE_MOIS}{NB_DUREE_2}"
            LICENCE_MOIS = f"{LICENCE_MOIS}{nombreW}{nombreX}"
            LICENCE_MOIS = f"{LICENCE_MOIS}{NB_DUREE_0}"
            LICENCE_MOIS = f"{LICENCE_MOIS}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
            LICENCE_MOIS = f"{LICENCE_MOIS}{LIC_MOIS_1}{LIC_MOIS_2}"
            LICENCE_MOIS = f"{LICENCE_MOIS}{NB_DUREE_4}"
            LICENCE_MOIS = f"{LICENCE_MOIS}{nombreY}{nombreZ}"
            
            if DEV : print(f"LICENCE_MOIS : {LICENCE_MOIS}")
            
            LICENCE_JOUR = f"{NB_DUREE_1}{nombre_inutil}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{NB_DUREE_2}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{nombreW}{nombreX}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{NB_DUREE_0}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{LIC_MOIS_1}{LIC_MOIS_2}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{LIC_JOURS_1}{LIC_JOURS_2}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{NB_DUREE_4}"
            LICENCE_JOUR = f"{LICENCE_JOUR}{nombreY}{nombreZ}"
            
            print(f"LICENCE_JOUR : {LICENCE_JOUR}")
            
            if LICENCE_CLIENT == LICENCE_AN :
                VALIDE = True
            if LICENCE_CLIENT == LICENCE_MOIS :
                VALIDE = True
            if LICENCE_CLIENT == LICENCE_JOUR :
                VALIDE = True
        
        if not VALIDE :
            VALIDE = False
            VALIDE_LICENCE_DUREE = False
            
            ANNEE_1 = int(chiffre_data(0,ANNEE_DEBUT))
            ANNEE_2 = chiffre_data(1,ANNEE_DEBUT)
            ANNEE_3 = chiffre_data(2,ANNEE_DEBUT)
            ANNEE_4 = chiffre_data(3,ANNEE_DEBUT)
            
            LIC_AN_1 = int(ANNEE_1) + int(nombreW) + int(nombreX) * 2
            LIC_AN_2 = int(ANNEE_2) + int(nombreW) + int(nombreY) * 3
            LIC_AN_3 = int(ANNEE_3) + int(nombreW) + int(nombreZ) * 2
            LIC_AN_4 = int(ANNEE_4) + int(nombreY) + int(nombreZ) * 3 
            
            NB_DUREE_3 = NB_DUREE_3 + NB_DUREE_4
            
            LICENCE_DUREE = f"{NB_DUREE_1}{nombre_inutil}"
            LICENCE_DUREE = f"{LICENCE_DUREE}{NB_DUREE_2}"
            LICENCE_DUREE = f"{LICENCE_DUREE}{nombreW}{nombreX}"
            LICENCE_DUREE = f"{LICENCE_DUREE}{NB_DUREE_0}"
            LICENCE_DUREE = f"{LICENCE_DUREE}{LIC_AN_1}{LIC_AN_2}{LIC_AN_3}{LIC_AN_4}"
            LICENCE_DUREE = f"{LICENCE_DUREE}{NB_DUREE_3}"
            LICENCE_DUREE = f"{LICENCE_DUREE}{NB_DUREE_4}"
            LICENCE_DUREE = f"{LICENCE_DUREE}{nombreY}{nombreZ}"
            
            if DEV : print(f"LICENCE_DUREE : {LICENCE_DUREE}")
            
            if LICENCE_CLIENT == LICENCE_DUREE :
                VALIDE_LICENCE_DUREE = True
            
            if VALIDE_LICENCE_DUREE and (int(ANNEE_DEBUT) <= ANNNEE <= int(ANNEE_FIN)) :
                VALIDE = True
        
    except Exception as e:
        valide = False
    return VALIDE
    
    
    