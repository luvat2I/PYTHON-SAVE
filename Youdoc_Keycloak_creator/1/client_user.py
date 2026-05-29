import requests
from urllib.parse import urljoin
def client_user_creation(TOKEN,
							KEYCLOAK_BASE, REALM,
							USER_ID, USER_MAIL, USER_FIRSTNAME, USER_LASTNAME, USER_ENABLED, USER_VERIFIED, USER_PASSWORD, USER_TEMPORARY,
							VERIF_SSL):
	#client_user.client_user(TYPEACTION,token_gestion_access_token,KEYCLOAK_BASE, REALM, VERIF_SSL)
	error = False
	ID_APP = "XC002"
	
	try:
		NEW_USER = {
			"username": f"{USER_ID}",
			"email": f"{USER_MAIL}",
			"firstName": f"{USER_FIRSTNAME}",
			"lastName": f"{USER_LASTNAME}",
			"enabled": True,
			"emailVerified": True,
			"credentials": [
				{
					"type": "password",
					"value": f"passwordT2I",
					"temporary": False
				}
			]
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
			users_url = urljoin(KEYCLOAK_BASE, f"admin/realms/{REALM}/users")
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#headers
	if not error :
		try:
			headers = {
				"Authorization": f"Bearer {TOKEN}",
				"Content-Type": "application/json"
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
	
	#resp = requests.post(users_url, headers=headers, json=NEW_USER, verify=VERIF_SSL)
	if not error :
		try:
			
			resp = requests.post(users_url, headers=headers, json=NEW_USER, verify=VERIF_SSL)
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

def client_user_id(TOKEN,
					KEYCLOAK_BASE, REALM,
					USER_ID,
					VERIF_SSL):
	error = False
	ID_APP = "XC003"
	
	
	#users_url = urljoin(KEYCLOAK_BASE, f"admin/realms/{REALM}/users")
	if not error :
		try:
			users_url = urljoin(KEYCLOAK_BASE, f"admin/realms/{REALM}/users")
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0001",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	
	#headers = {"Authorization": f"Bearer {TOKEN}"}
	if not error :
		try:
			headers = {
				"Authorization": f"Bearer {TOKEN}"
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
	
	#params = {"username": USER_ID, "exact": "true"}
	if not error :
		try:
			params = {
				"username": USER_ID, "exact": "true"
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
	
	#resp = requests.get(users_url, headers=headers, params=params, verify=VERIF_SSL)
	if not error :
		try:
			resp = requests.get(users_url, headers=headers, params=params, verify=VERIF_SSL)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0003",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#resp.raise_for_status()
	if not error :
		try:
			resp.raise_for_status()
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#users = resp.json()
	if not error :
		try:
			users = resp.json()
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0005",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#return
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": users,
				"error": "",
				"message": f"ID : {users}",
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

def client_user_liste(TOKEN,
					KEYCLOAK_BASE, REALM,
					VERIF_SSL):
	error = False
	ID_APP = "XC004"
	
	#users_url = urljoin(KEYCLOAK_BASE, f"admin/realms/{REALM}/users")
	if not error :
		try:
			users_url = urljoin(KEYCLOAK_BASE, f"admin/realms/{REALM}/users")
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0001",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	#headers = {"Authorization": f"Bearer {TOKEN}"}
	if not error :
		try:
			headers = {"Authorization": f"Bearer {TOKEN}"}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#resp = requests.get(users_url, headers=headers, verify=VERIF_SSL)
	if not error :
		try:
			resp = requests.get(users_url, headers=headers, verify=VERIF_SSL)
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0003",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#resp.raise_for_status()
	if not error :
		try:
			resp.raise_for_status()
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0004",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	#users = resp.json()
	if not error :
		try:
			users = resp.json()
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "0005",
				"message": f"{e}",
				"message2": ""
			}
			error = True
			
	#return
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": users,
				"error": "",
				"message": f"List : {users}",
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