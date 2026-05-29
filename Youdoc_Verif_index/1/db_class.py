import pyodbc

class DatabaseConnection: #classe de connexion SGBD SQL et DB2
	def __init__(self, db_type,driver, server, port, database, user, password):
		self.db_type = db_type
		self.driver = driver
		self.server = server
		self.port = port
		self.database = database
		self.user = user
		self.password = password
		self.connection = None

	def connect(self): # Connexion au SGBD
		ID_APP = "connect"
		try:
		
			if self.db_type == 'DB2': # connexion DB2
				connection_string = (
					f'DRIVER={{iSeries access ODBC Driver}};'
					f'SYSTEM={self.server};'
					f'PORT={self.port};'
					f'DATABASE={self.database};'
					f'PROTOCOL=TCPIP;'
					f'UID={self.user};'
					f'PWD={self.password};'
				)
			else: # connexion SQL
				connection_string = (
					f'DRIVER={{{self.driver}}};'
					f'SERVER={self.server};'
					f'PORT={self.port};'
					f'DATABASE={self.database};'
					f'UID={self.user};'
					f'PWD={self.password};'
					f'Encrypt=no;'
                    f'TrustServerCertificate=yes;'
				)
			self.connection = pyodbc.connect(connection_string)
			self.cursor = self.connection.cursor()
			return {
				"code": ID_APP,
				"result": f"Connexion réussie à la base de données.",
				"error": "",
				"message": "",
				"message2": ""
			}
		except pyodbc.Error as e:
			return {
				"code": ID_APP,
				"result": f"Erreur de connexion à la base de données",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
			exit(1)  # Quitte l'application avec un code d'erreur
			
	def validate_connection(self): # Valide si la connexion est active.
		ID_APP = "validate_connection"
		
		if self.connection:
			try:
				cursor = self.connection.cursor()
				if self.db_type == 'DB2':
					cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
				else :
					cursor.execute("SELECT 1;")
				return {
					"code": ID_APP,
					"result": f"La connexion est valide",
					"error": "",
					"message": "",
					"message2": ""
				}
				
			except pyodbc.Error as e:
				return {
					"code": ID_APP,
					"result": f"La connexion n'est pas valide",
					"error": "001",
					"message": f"{e}",
					"message2": ""
				}
		else:
			
			return {
				"code": ID_APP,
				"result": f"Aucune connexion établie.",
				"error": "002",
				"message": f"{e}",
				"message2": ""
			}
			input("Appuyez sur une touche pour quitter...")
			exit(1)  # Quitte l'application avec un code d'erreur

	def execute_query(self, query, params=None): # Exécute une requête SQL et retourne tous les résultats
		ID_APP = "execute_query"
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchall()  # Retourne tous les résultats
		except Exception as e:
			
			return {
				"code": ID_APP,
				"result": f"Erreur lors de l'execution de la requete sql {query}",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
			exit(1)  # Quitte l'application avec un code d'erreur
			
	def execute_query_count(self, query, params=None): # Exécute une requête SQL de count et retourne un unique résultat
		ID_APP = "execute_query_count"
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchone()[0]  # Retourne un unique résultat
		except Exception as e:
			
			return {
				"code": ID_APP,
				"result": f"Erreur lors de l'execution de la requete sql {query}",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
			exit(1)  # Quitte l'application avec un code d'erreur
			
	def execute_query_save(self, query, params=None): # Exécute une requête d'update et commit
		ID_APP = "execute_query_save"
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			self.connection.commit() # Commit le résultat
		except Exception as e:
			return "ERROR"
			exit(1)  # Quitte l'application avec un code d'erreur

	def close(self): # Cloture la co
		ID_APP = "close"
		if self.connection:
			try:
				self.connection.close()
				return {
					"code": ID_APP,
					"result": f"Connexion fermée.",
					"error": "",
					"message": "",
					"message2": ""
				}
			except Exception as e:
				return {
				"code": ID_APP,
				"result": f"Erreur lors de la deconnexion {query}",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
				exit(1)  # Quitte l'application avec un code d'erreur
	