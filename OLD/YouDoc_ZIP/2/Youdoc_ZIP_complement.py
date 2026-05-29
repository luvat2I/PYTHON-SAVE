import configparser
import os
import sys
import string
DIGITS = '0123456789'          # positions qui acceptent uniquement chiffres si souhaité
ALPHANUM = '0123456789' + string.ascii_uppercase  # 0-9 puis A-Z (36 symboles)

# Ici on assume que chaque caractère suit la même alphabet ALPHANUM.
ALPHABET = ALPHANUM

def get_TENANT(CONFIG_INI) :
	try:
		TENANT = CONFIG_INI['ENTRA_ID']['TENANT']
	except Exception as e:
		TENANT = "ERROR"
	return TENANT

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
	
def ID_suivant(ID_en_cours):
	ID_en_cours = ID_en_cours.upper()
	arr = list(ID_en_cours)
	base = len(ALPHABET)
	idx_map = {c: i for i, c in enumerate(ALPHABET)}
	i = len(arr) - 1
	carry = 1
	while i >= 0 and carry:
		c = arr[i]
		if c not in idx_map:
			raise ValueError(f"Caractère invalide pour l'alphabet: {c}")
		val = idx_map[c] + carry
		arr[i] = ALPHABET[val % base]
		carry = val // base
		i -= 1
	if carry:
		# si débordement à gauche, préfixer le symbole correspondant (par exemple '1')
		arr.insert(0, ALPHABET[carry])
	return ''.join(arr)
	
def supprime_extension(filename):
    if filename.startswith('.') and filename.count('.') == 1:
        return filename
    dot = filename.rfind('.')
    return filename if dot <= 0 else filename[:dot]