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
	

def chiffre_an(position,annee):
    """
    Retourne le chiffre (int) à la position donnée dans la représentation ISO de la date (YYYY-MM-DD)
    Positions indexées à partir de 0 sur la suite des chiffres uniquement.
    Ex : pour 2025-12-09, chiffres = ['2','0','2','5','1','2','0','9']
    chiffre_date(0) -> 2, chiffre_date(1) -> 0, etc.
    Retourne None si la position est hors limites ou si position < 0.
    """
    if position < 0:
        return None
    chiffres = [c for c in annee if c.isdigit()]
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

def luva_lic_calcul_an():
	error = False
	ID_APP = "LIC001"
	
	ma_lic_date = date.today().isoformat()
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9

	chiffre1 = chiffre_date(0)
	chiffre2 = chiffre_date(1)
	chiffre3 = chiffre_date(2)
	chiffre4 = chiffre_date(3)
	chiffre5 = chiffre_date(4)
	chiffre6 = chiffre_date(5)
	chiffre7 = chiffre_date(6)
	chiffre8 = chiffre_date(7)
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str(nombreY)
	nombre8 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}"
	
	print(f"Licence année :   {code_lic}")
	
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str((nombreW + nombreX + chiffre5)*2)
	nombre8 = str((nombreW + nombreY + chiffre6)*3)
	nombre9 = str(nombreY)
	nombre10 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}{nombre10}"
	
	print(f"Licence mois :    {code_lic}")
	
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9

	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str((nombreW + nombreX + chiffre5)*2)
	nombre8 = str((nombreW + nombreY + chiffre6)*3)
	nombre9 = str((nombreW + nombreX + chiffre7)*2)
	nombre10 = str((nombreW + nombreY + chiffre8)*3)
	nombre11 = str(nombreY)
	nombre12 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}{nombre10}{nombre11}{nombre12}"
	
	print(f"Licence journée : {code_lic}")
	
	nombre0 = random.randint(5, 9)  # inclusif : 1 à 4
	
	nombreannee = 5
	annee = "2025"
	
	chiffre1 = chiffre_an(0,annee)
	chiffre2 = chiffre_an(1,annee)
	chiffre3 = chiffre_an(2,annee)
	chiffre4 = chiffre_an(3,annee)
	
	nombreW = random.randint(1, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	
	nombre3 = str(chiffre3+chiffre4+nombreY)
	
	nombre4 = str((nombreW + nombreX + chiffre1)*2)
	nombre5 = str((nombreW + nombreY + chiffre2)*3)
	nombre6 = str((nombreW + nombreZ + chiffre3)*2)
	nombre7 = str((nombreY + nombreZ + chiffre4)*3)
	
	nombre8 = str((nombreW + nombreY + nombreX + nombreannee)*3)
	
	nombre9 = str(chiffre3)
	nombre8 = str(nombreY)
	nombre9 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}"
	
	print(f"Licence {nombreannee} années depuis {annee} : {code_lic}")


def luva_lic_calcul_mois():
	error = False
	ID_APP = "LIC002"
	
	ma_lic_date = date.today().isoformat()
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9

	chiffre1 = chiffre_date(0)
	chiffre2 = chiffre_date(1)
	chiffre3 = chiffre_date(2)
	chiffre4 = chiffre_date(3)
	chiffre5 = chiffre_date(4)
	chiffre6 = chiffre_date(5)
	chiffre7 = chiffre_date(6)
	chiffre8 = chiffre_date(7)
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str(nombreY)
	nombre8 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}"
	
	print(f"Licence année :   {code_lic}")
	
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str((nombreW + nombreX + chiffre5)*2)
	nombre8 = str((nombreW + nombreY + chiffre6)*3)
	nombre9 = str(nombreY)
	nombre10 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}{nombre10}"
	
	print(f"Licence mois :    {code_lic}")
	
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9

	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str((nombreW + nombreX + chiffre5)*2)
	nombre8 = str((nombreW + nombreY + chiffre6)*3)
	nombre9 = str((nombreW + nombreX + chiffre7)*2)
	nombre10 = str((nombreW + nombreY + chiffre8)*3)
	nombre11 = str(nombreY)
	nombre12 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}{nombre10}{nombre11}{nombre12}"
	
	print(f"Licence journée : {code_lic}")
	
	nombre0 = random.randint(5, 9)  # inclusif : 1 à 4
	
	nombreannee = 5
	annee = "2025"
	
	chiffre1 = chiffre_an(0,annee)
	chiffre2 = chiffre_an(1,annee)
	chiffre3 = chiffre_an(2,annee)
	chiffre4 = chiffre_an(3,annee)
	
	nombreW = random.randint(1, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	
	nombre3 = str(chiffre3+chiffre4+nombreY)
	
	nombre4 = str((nombreW + nombreX + chiffre1)*2)
	nombre5 = str((nombreW + nombreY + chiffre2)*3)
	nombre6 = str((nombreW + nombreZ + chiffre3)*2)
	nombre7 = str((nombreY + nombreZ + chiffre4)*3)
	
	nombre8 = str((nombreW + nombreY + nombreX + nombreannee)*3)
	
	nombre9 = str(chiffre3)
	nombre8 = str(nombreY)
	nombre9 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}"
	
	print(f"Licence {nombreannee} années depuis {annee} : {code_lic}")
	

def luva_lic_calcul_jour():
	error = False
	ID_APP = "LIC003"
	
	ma_lic_date = date.today().isoformat()
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9

	chiffre1 = chiffre_date(0)
	chiffre2 = chiffre_date(1)
	chiffre3 = chiffre_date(2)
	chiffre4 = chiffre_date(3)
	chiffre5 = chiffre_date(4)
	chiffre6 = chiffre_date(5)
	chiffre7 = chiffre_date(6)
	chiffre8 = chiffre_date(7)
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str(nombreY)
	nombre8 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}"
	
	print(f"Licence année :   {code_lic}")
	
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str((nombreW + nombreX + chiffre5)*2)
	nombre8 = str((nombreW + nombreY + chiffre6)*3)
	nombre9 = str(nombreY)
	nombre10 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}{nombre10}"
	
	print(f"Licence mois :    {code_lic}")
	
	nombre0 = random.randint(0, 4)  # inclusif : 1 à 4
	
	nombreW = random.randint(3, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9

	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	nombre3 = str((nombreW + nombreX + chiffre1)*2)
	nombre4 = str((nombreW + nombreY + chiffre2)*3)
	nombre5 = str((nombreW + nombreZ + chiffre3)*2)
	nombre6 = str((nombreY + nombreZ + chiffre4)*3)
	nombre7 = str((nombreW + nombreX + chiffre5)*2)
	nombre8 = str((nombreW + nombreY + chiffre6)*3)
	nombre9 = str((nombreW + nombreX + chiffre7)*2)
	nombre10 = str((nombreW + nombreY + chiffre8)*3)
	nombre11 = str(nombreY)
	nombre12 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}{nombre10}{nombre11}{nombre12}"
	
	print(f"Licence journée : {code_lic}")
	
	nombre0 = random.randint(5, 9)  # inclusif : 1 à 4
	
	nombreannee = 5
	annee = "2025"
	
	chiffre1 = chiffre_an(0,annee)
	chiffre2 = chiffre_an(1,annee)
	chiffre3 = chiffre_an(2,annee)
	chiffre4 = chiffre_an(3,annee)
	
	nombreW = random.randint(1, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	
	nombre3 = str(chiffre3+chiffre4+nombreY)
	
	nombre4 = str((nombreW + nombreX + chiffre1)*2)
	nombre5 = str((nombreW + nombreY + chiffre2)*3)
	nombre6 = str((nombreW + nombreZ + chiffre3)*2)
	nombre7 = str((nombreY + nombreZ + chiffre4)*3)
	
	nombre8 = str((nombreW + nombreY + nombreX + nombreannee)*3)
	
	nombre9 = str(chiffre3)
	nombre8 = str(nombreY)
	nombre9 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}"
	
	print(f"Licence {nombreannee} années depuis {annee} : {code_lic}")
	

def luva_lic_calcul_periode(annee, nombreannee):
	error = False
	ID_APP = "LIC004"
		
	nombre0 = random.randint(5, 9)  # inclusif : 1 à 4
	
	chiffre1 = chiffre_an(0,annee)
	chiffre2 = chiffre_an(1,annee)
	chiffre3 = chiffre_an(2,annee)
	chiffre4 = chiffre_an(3,annee)
	
	nombreW = random.randint(1, 9)  # inclusif : 1 à 9
	nombreX = random.randint(1, 9)  # inclusif : 1 à 9
	nombreY = random.randint(1, 9)  # inclusif : 1 à 9
	nombreZ = random.randint(1, 9)  # inclusif : 1 à 9
	
	nombre1 = str(nombreW)
	nombre2 = str(nombreX)
	
	nombre3 = str(chiffre3+chiffre4+nombreY)
	
	nombre4 = str((nombreW + nombreX + chiffre1)*2)
	nombre5 = str((nombreW + nombreY + chiffre2)*3)
	nombre6 = str((nombreW + nombreZ + chiffre3)*2)
	nombre7 = str((nombreY + nombreZ + chiffre4)*3)
	
	nombre8 = str((nombreW + nombreY + nombreX + nombreannee)*3)
	
	nombre9 = str(chiffre3)
	nombre8 = str(nombreY)
	nombre9 = str(nombreZ)
	
	code_lic = f"{nombre0}{nombre1}{nombre2}{nombre3}{nombre4}{nombre5}{nombre6}{nombre7}{nombre8}{nombre9}"
	
	return code_lic

def valide_licence(code_lic):
	error = False
	ID_APP = "LIC005"
	
	print(code_lic)
	
	chiffre0 = chiffre_lic(0,code_lic)
	
	nombreW = chiffre_lic(1,code_lic)
	nombreX = chiffre_lic(2,code_lic)
	
	print(chiffre0)
	nb_length = len(code_lic)
	print(nb_length)
	
	nombreZ = chiffre_lic((nb_length - 1),code_lic)
	nombreY = chiffre_lic((nb_length - 2),code_lic)
	
	print(nombreZ)
	print(nombreY)
	
	if chiffre0 >= 5 :
		print("periode")
	else :
		print("autres")
	
	
	