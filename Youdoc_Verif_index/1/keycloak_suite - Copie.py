import requests
import jwt  # PyJWT
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from urllib.parse import urljoin



def keycloak_master_barear(KEYCLOAK_BASE, REALM, CLIENT_ID, GRANT_TYPE, USERNAME, PASSWORD ,TIMEOUT_TIME , VERIF_SSL):
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

def keycloak_client_liste(	KEYCLOAK_URL,
							TOKEN_BAREAR, 
							REALM_CLIENT,
							VERIF_SSL,
							MODE_DEV):
	error = False
	ID_APP = "KEYCLOAK"
	
	# Connexion
	if not error :
		try:
			users_url = urljoin(KEYCLOAK_URL, f"/admin/realms/{REALM_CLIENT}/clients")
			headers = {"Authorization": f"Bearer {TOKEN_BAREAR}"}
			resp = requests.get(users_url, headers=headers, verify=VERIF_SSL)
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "Connexion : ",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#traitement de la reponse
	if not error :
		try:
			resp.raise_for_status()
			clients = resp.json()
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "reponse : ",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	#return
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": clients,
				"error": "",
				"message": f"List : {clients}",
				"message2": ""
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0006",
				"message": f"{e}",
				"message2": ""
			}
			error = True



def keycloak_client_id(	KEYCLOAK_URL,
							TOKEN_BAREAR, 
							REALM_CLIENT,CLIENT,
							VERIF_SSL,
							MODE_DEV):
	error = False
	ID_APP = "KEYCLOAK"
	
	# Connexion
	if not error :
		try:
			users_url = urljoin(KEYCLOAK_URL, f"/admin/realms/{REALM_CLIENT}/clients")
			headers = {"Authorization": f"Bearer {TOKEN_BAREAR}"}
			resp = requests.get(users_url, headers=headers, verify=VERIF_SSL)
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "Connexion : ",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#traitement de la reponse
	if not error :
		try:
			resp.raise_for_status()
			clients = resp.json()
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "reponse : ",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	target = CLIENT
	
	client_id = next((c["id"] for c in clients if c.get("clientId") == target), None)
	
	#return
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": client_id,
				"error": "",
				"message": f"ID du client : {client_id}",
				"message2": f"{client_id}"
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0006",
				"message": f"{e}",
				"message2": ""
			}
			error = True





def keycloak_create_role(	KEYCLOAK_URL,
							TOKEN_BAREAR, 
							REALM_CLIENT,CLIENT_ID,
							ROLE_NAME,ROLE_DESCRIPTION,
							VERIF_SSL,
							MODE_DEV):
								
	error = False
	ID_APP = "KEYCLOAK"
	
	try:
		NEW_ROLE = {
			"name": f"{ROLE_NAME}",
			"description": f"{ROLE_DESCRIPTION}",
			"composite": False,
			"clientRole": True,
			"attributes": {}
		}
	except Exception as e:
		return {
			"code": ID_APP,
			"result": "",
			"error": "0001",
			"message": f"{e}",
			"message2": ""
		}
		error = True
		
	
	#users_url = urljoin(KEYCLOAK_BASE, f"admin/realms/{REALM}/users")
	if not error :
		try:
			users_url = urljoin(KEYCLOAK_URL, f"admin/realms/{REALM_CLIENT}/clients/{CLIENT_ID}/roles")
			headers = {
				"Authorization": f"Bearer {TOKEN_BAREAR}",
				"Content-Type": "application/json"
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#resp = requests.post(users_url, headers=headers, json=NEW_ROLE, verify=VERIF_SSL)
	if not error :
		try:
			
			resp = requests.post(users_url, headers=headers, json=NEW_ROLE, verify=VERIF_SSL)
			if resp.status_code == 201:
				return {
					"code": ID_APP,
					"result": resp.text,
					"error": "",
					"message": f"creation : {resp.text}",
					"message2": ""
				}
			else:
				return {
					"code": ID_APP,
					"result": "",
					"error": "0005",
					"message": f"Pas de creation : {resp.text}",
					"message2": ""
				}
				error = True
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0004",
				"message": f"{e}",
				"message2": ""
			}
			error = True




def keycloak_delete_role(	KEYCLOAK_URL,
							TOKEN_BAREAR, 
							REALM_CLIENT,CLIENT_ID,
							ROLE_NAME,ROLE_DESCRIPTION,
							VERIF_SSL,
							MODE_DEV):
	error = False
	ID_APP = "KEYCLOAK"
	
	# Connexion
	if not error :
		try:
			role_url = urljoin(KEYCLOAK_URL, f"/admin/realms/{REALM_CLIENT}/clients/{CLIENT_ID}/roles/{ROLE_NAME}")
			headers = {"Authorization": f"Bearer {TOKEN_BAREAR}"}
			resp = requests.delete(role_url, headers=headers, verify=VERIF_SSL)
			
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "Connexion : ",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#return
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": ROLE_NAME,
				"error": "",
				"message": f"suppression role: {ROLE_NAME}",
				"message2": f""
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0006",
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