import pyodbc

class DatabaseConnection: 
    #classe de connexion SGBD SQL et DB2
    def __init__(self, db_type,driver, server, port, database, user, password,debug):
        self.db_type = db_type
        self.driver = driver
        self.server = server
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.debug = debug
        self.connection = None

    def connect(self): # Connexion au SGBD
        if self.debug : print(f"lancement de DatabaseConnection.connect")
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
                "error": False,
                "return": f"Connexion réussie à la base de données."
                }
        except pyodbc.Error as e:
            return {
                "error": True,
                "return": f"{e}"
                }
            
    def validate_connection(self): # Valide si la connexion est active.
        if self.debug : print(f"lancement de DatabaseConnection.validate_connection")
        
        if self.connection:
            try:
                cursor = self.connection.cursor()
                if self.db_type == 'DB2':
                    cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
                else :
                    cursor.execute("SELECT 1;")
                return {
                    "error": False,
                    "return": f"La connexion est valide"
                }
                
            except Exception as e:
                return {
                    "error": True,
                    "return": f"ERREUR > {e}"
                }
        else:
            
            
            return {
                "error": True,
                "return": f"ERREUR > Aucune connexion établie."
            }

    def execute_query(self, query, params=None): # Exécute une requête SQL et retourne tous les résultats
        ID_APP = "execute_query"
        if params is None:
            params = ()
        try:
            self.cursor.execute(query, params)
            return {
                "error": True,
                "return": self.cursor.fetchall()
            }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
            }
            
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
            return {
                "error": False,
                "return": f"Commit réussi"
            }
        except Exception as e:
            return {
                "error": True,
                "return": f"ERREUR > {e}"
            }

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
    