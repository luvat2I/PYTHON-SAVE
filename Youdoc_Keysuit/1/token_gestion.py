import requests
import jwt  # PyJWT
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

def token_gestion_client(KEYCLOAK_BASE, REALM, CLIENT_ID,GRANT_TYPE, USERNAME, PASSWORD, CLIENT_SECRET ,TIMEOUT_TIME , VERIF_SSL):
	error = False
	ID_APP = "XC001"
	try:
		
		token_url = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
		data = {
			"grant_type": "password",
			"client_id": CLIENT_ID,
			"client_secret": CLIENT_SECRET,
			"username": USERNAME,
			"password": PASSWORD,
			"grant_type": GRANT_TYPE
			}
		
		if VERIF_SSL:
			result = requests.post(token_url, data=data, timeout=TIMEOUT_TIME)
		else:
			result = requests.post(token_url, data=data, timeout=TIMEOUT_TIME, verify=VERIF_SSL)
	except Exception as e:
		return {
			"code": ID_APP,
			"result": "",
			"error": "0001",
			"message": f"{e}",
			"message2": ""
		}
		error = True
	
	# result.raise_for_status()
	if not error :
		try:
			result.raise_for_status()
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": result.json(),
				"error": "",
				"message": "",
				"message2": ""
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0003",
				"message": f"{e}",
				"message2": ""
			}
			error = True



def token_gestion_realm(KEYCLOAK_BASE, REALM, CLIENT_ID, GRANT_TYPE, USERNAME, PASSWORD ,TIMEOUT_TIME , VERIF_SSL):
	error = False
	ID_APP = "XC001"
	try:
		token_url = f"{KEYCLOAK_BASE}/realms/{REALM}/protocol/openid-connect/token"
		data = {
			"grant_type": "password",
			"client_id": CLIENT_ID,
			"username": USERNAME,
			"password": PASSWORD,
			"grant_type": GRANT_TYPE
		}
		
		if VERIF_SSL:
			result = requests.post(token_url, data=data, timeout=TIMEOUT_TIME)
		else:
			result = requests.post(token_url, data=data, timeout=TIMEOUT_TIME, verify=VERIF_SSL)
	except Exception as e:
		return {
			"code": ID_APP,
			"result": "",
			"error": "0001",
			"message": f"{e}",
			"message2": ""
		}
		error = True
	
	# result.raise_for_status()
	if not error :
		try:
			result.raise_for_status()
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": result.json(),
				"error": "",
				"message": "",
				"message2": ""
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0003",
				"message": f"{e}",
				"message2": ""
			}
			error = True

def token_decode(TOKEN):
	try:
		header = jwt.get_unverified_header(TOKEN)
		decoded = jwt.decode(TOKEN, options={"verify_signature": False})
		print (decoded)
		#return decoded
	except Exception as e:
		print (f"{e}")