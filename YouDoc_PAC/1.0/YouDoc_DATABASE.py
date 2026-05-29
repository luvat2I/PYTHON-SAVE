#pyinstaller PAC.spec
import os
import pyodbc
import pysolr
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import re
import time
import logging
import configparser
from datetime import datetime, timedelta

# import de mes dev
import log_aff

# Désactiver les avertissements de sécurité pour les requêtes non vérifiées
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lecture du fichier de configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Récupération de la configuration des log et du print (du fichier ini) 
enable_logging = config.getboolean('logging', 'enable_logging')
log_folder = config['logging']['log_folder']
enable_print = config.getboolean('logging', 'enable_print')

# Récupération des informations des connexion BDD (du fichier ini)
sgbd_db_type = config['SGBD']['db_type']
sgbd_driver = config['SGBD']['db_driver']
sgbd_server = config['SGBD']['db_server']
sgbd_port = config['SGBD']['db_port']
sgbd_username = config['SGBD']['db_username']
sgbd_password = config['SGBD']['db_password']
sgbd_database = config['SGBD']['db_database']

traitement_type = "DATABASE"

if enable_logging:
	os.makedirs(log_folder, exist_ok=True)  # Créer le dossier de log

# Configure le log si activé
if enable_logging:
	log_filename = os.path.join(log_folder, datetime.now().strftime("traitement_%Y-%m-%d.log"))
	logging.basicConfig(filename=log_filename, level=logging.INFO, 
						format='%(asctime)s - %(levelname)s > %(message)s')
else:
	logging.disable(logging.CRITICAL)  # Désactiver le logging si non activé
	
	

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
		try:
			connection_string = (
				f'DRIVER={{{self.driver}}};'
				f'SERVER={self.server};'
				f'PORT={self.port};'
				f'DATABASE={self.database};'
				f'UID={self.user};'
				f'PWD={self.password};'
				'TrustServerCertificate=yes;'
			)
			self.connection = pyodbc.connect(connection_string)
			self.cursor = self.connection.cursor()
			print("Connexion réussie à la base de données.")
		except pyodbc.Error as e:
			print(f"Erreur de connexion à la base de données: {e}")

	def validate_connection(self): # Valide si la connexion est active.
		if self.connection:
			try:
				cursor = self.connection.cursor()
				cursor.execute("SELECT 1;")
				print("La connexion est valide.")
				
			except pyodbc.Error as e:
				print(f"La connexion n'est pas valide: {e}")
		else:
			print("Aucune connexion établie.")

	def execute_query(self, query, params=None): # Exécute une requête SQL et retourne tous les résultats
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			return self.cursor.fetchall()  # Retourne tous les résultats
		except pyodbc.Error as e:
			print(f"Une erreur est survenue : {e}")
			return None
			
	def execute_query_count(self, query, params=None): # Exécute une requête SQL de count et retourne un unique résultat
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			if self.cursor.fetchone():
				retour = self.cursor.fetchone()  # Retourne un unique résultat
			else :
				retour = ""
			return retour  # Retourne un unique résultat
		except pyodbc.Error as e:
			print(f"Une erreur est survenue : {e}")
			return None
			
	def execute_query_save(self, query, params=None): # Exécute une requête d'update et commit
		if params is None:
			params = ()
		try:
			self.cursor.execute(query, params)
			self.connection.commit() # Commit le résultat
		except pyodbc.Error as e:
			print(f"Erreur ODBC : {e}")
			return None
		except Exception as e:
			print(f"Une erreur s'est produite : {e}")
			return None

	def close(self): # Cloture la co
		if self.connection:
			self.connection.close()
			print("Connexion fermée.")

# Utilisation de la classe
if __name__ == "__main__":

	# debut du log
	log_aff.log_base("INFO","#########################")
	log_aff.log_base("INFO","début du traitement")
	
	log_aff.log_info("INFO",f"SGBD > type : {sgbd_db_type} serveur : {sgbd_server} port : {sgbd_port} user : {sgbd_username} pass : {sgbd_password} base : {sgbd_database}",enable_print)
	
	if traitement_type == "DATABASE" : 
		
		log_aff.log_info("INFO","Création de la connexion SGBD SQL",enable_print)
		db = DatabaseConnection(sgbd_db_type, sgbd_driver, sgbd_server,sgbd_port, sgbd_database, sgbd_username, sgbd_password)
		db.connect()
		db.validate_connection()
		
		if sgbd_db_type == 'SQL2':
			log_aff.log_base("INFO","SGBD SQL")
			procedure_name = "PROC_ECM_PARAM"
			db_query_count = """
						SELECT name 
						FROM sys.objects 
						WHERE type = 'P' AND name = 'PROC_ECM_PARAM'
					"""
			log_aff.log_base("INFO",f"{db_query_count}")
			db_results_count = db.execute_query_count(db_query_count)
			log_aff.log_base("INFO",f"{db_query_count}")
			if db_results_count != "PROC_ECM_PARAM" :
				log_aff.log_base("INFO",f"injection de la procedure SQL dans la BDD")
				db_query = """ create PROCEDURE [dbo].[PROC_ECM_PARAM]
							
							AS
							BEGIN

							CREATE TABLE #folderTypes (VALEURS VARCHAR(40) NULL);


							-- pour cursor
							DECLARE @baseId nvarchar(max), @amatcd nvarchar(max), @ggd7nu nvarchar(max), @typeNme nvarchar(max), @pacDesc nvarchar(max)
							-- pour traitement
							DECLARE @OLDbaseId nvarchar(max), @OLDamatcd nvarchar(max), @OLDggd7nu nvarchar(max) = '', @OLDtypeNme nvarchar(max), @OLDpacDesc nvarchar(max), @paramdata  nvarchar(max), @formatedjson  nvarchar(max)
							DECLARE @rupture nvarchar(max), @OLDrupture nvarchar(max) = '', @folderLinkTypes nvarchar(max), @folderTypes nvarchar(max), @env nvarchar(max) = 'ENV002'

							DECLARE paramCursor CURSOR FOR
							SELECT ecm_pacref.baseId, ARAMREP.AMATCD, ARGGREP.GGD7NU, ecm_fldtyp.typeNme, ecm_pacref.pacDesc from ecm_pacref
							inner join ARAMREP on ARAMREP.AMAWCD = ecm_pacref.baseId left join ARGGREP on ARGGREP.GGAWCD = ecm_pacref.baseId
							left join ecm_fldtyp on ecm_fldtyp.base =  ecm_pacref.baseId
							order by ecm_pacref.baseId, ARAMREP.AMATCD, ARGGREP.GGD7NU, ecm_fldtyp.typeNme

							OPEN paramCursor

							FETCH NEXT FROM paramCursor
							INTO @baseId , @amatcd, @ggd7nu, @typeNme, @pacDesc
							WHILE @@FETCH_STATUS = 0
							BEGIN

								-- rupture sur changement de baseid 
								set @rupture = @baseId + @amatcd
								if @OLDrupture <> @rupture
								begin
									if @OLDrupture <> ''
									begin
										-- création de param DATABASE
										set @paramdata = '{"dataTypeLink":{"dataTypeId":"' +  @OLDamatcd + '","dataTypeDescription":"' + @OLDamatcd  + ' - Identifiant dossier","dataTypeKind":"02","idLength":15},' + @folderLinkTypes + '],' + @folderTypes +'],"isPacMode":false,"descriptions":[{"language":"fr","value":"' + @OLDpacDesc + '"}]}'
										set @formatedjson = '"databaseDescription_fr":"' + @OLDpacDesc  + '","databaseDescription_de":"' + @OLDpacDesc  + '","databaseDescription_it":"' + @OLDpacDesc  + '","databaseDescription_en":"' + @OLDpacDesc  + '"'
										
										if not exists (select 1 from ecm_param where param_id = @OLDbaseId and param_type = 'DATABASE')
										insert into ecm_param
										values ( @OLDbaseId, 'DATABASE',  @paramdata, 0, null, null, getdate(), null, @formatedjson, null, null )

									end	
									set @folderLinkTypes = '"folderLinkTypes":['
									set @folderTypes  = '"folderTypes":['
									set @OLDbaseId  = @baseId
									set @OLDamatcd = @amatcd
									-- set @OLDggd7nu = @ggd7nu 
									set @OLDpacDesc = @pacDesc
									set @OLDrupture = @rupture
									delete from #folderTypes
								end
								
								-- alimentation du folder type link si il est différent du précédent
								if @OLDggd7nu <> @ggd7nu
								begin

									-- ajout de la virgule entre chaque occurrence, si pas  la 1ere
									if @folderLinkTypes <> '"folderLinkTypes":['
									begin
										set @folderLinkTypes = @folderLinkTypes + ','
									end

									set @folderLinkTypes = @folderLinkTypes + '{"code":"' + @ggd7nu + '","descriptions":[{"language":"fr","value":"' + @ggd7nu + '"}]}'
									set @OLDggd7nu = @ggd7nu
								end

								-- ajout de chaque folderTypes s il nexiste pas deja
								if not exists (select 1 from #folderTypes where VALEURS = @typeNme)
								begin
									-- ajout de la virgule entre chaque occurrence, si pas  la 1ere
									if @folderTypes <> '"folderTypes":['
									begin
										set @folderTypes = @folderTypes + ','
									end	

									set @folderTypes = @folderTypes + '{"id":"' + @typeNme + '","autoIncrement":false}'
									insert into #folderTypes values (@typeNme)
								end

								FETCH NEXT FROM paramCursor
								INTO @baseId , @amatcd, @ggd7nu, @typeNme, @pacDesc
							END
							CLOSE paramCursor;
							DEALLOCATE paramCursor;

								if not exists (select 1 from ecm_param where param_id = @OLDbaseId and param_type = 'DATABASE')
								insert into ecm_param
								values ( @baseId, 'DATABASE',  @paramdata, 0, null, null, getdate(), null, @formatedjson, null, null )

							END """
				db.execute_query_save(db_query)
			log_aff.log_base("INFO",f"Presence du programme PROC_ECM_PARAM sur la BDD")	
			log_aff.log_base("INFO",f"Execution de la procedure PROC_ECM_PARAM")
			
			db_query = "EXECUTE PROC_ECM_PARAM"
			log_aff.log_base("INFO",f"Query : {db_query}")
			db.execute_query_save(db_query)
			
			log_aff.log_base("INFO","Fin de la Creation des databases dans ECM_PARAM.")
			
		if sgbd_db_type == 'SQL':
			
			db_query_pacref = "SELECT DISTINCT baseid, pacDesc FROM ecm_pacref"
			#ecm_pacref.baseid
			db_results_pacref = db.execute_query(db_query_pacref)
			
			caractere_special1 = '{'
			caractere_special2 = '}'
			caractere_special3 = '"'
			
			for row in db_results_pacref:
				print (f"pacref ligne > {row.baseid}")
				
				FORMATTED_JSON = f"{caractere_special3}databaseDescription_fr{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_de{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_it{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3},{caractere_special3}databaseDescription_en{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
				
				PARAM_DATA_FIN = f"{caractere_special3}language{caractere_special3}:{caractere_special3}fr{caractere_special3},{caractere_special3}value{caractere_special3}:{caractere_special3}{row.pacDesc}{caractere_special3}"
				
				db_query_ARAMREP = f"SELECT * FROM ARAMREP WHERE ARAMREP.AMAWCD = '{row.baseid}'"
				#db_query_ARAMREP = db_query_ARAMREP.upper()
				#aramrep.amatcd
				log_aff.log_base("INFO",f"query : {db_query_ARAMREP}")
				db_results_ARAMREP = db.execute_query(db_query_ARAMREP)
				
				db_query_ARGGREP = f"SELECT * FROM ARGGREP WHERE ARGGREP.GGAWCD = '{row.baseid}'"
				#ARGGREP.GGD7NU
				log_aff.log_base("INFO",f"query : {db_query_ARGGREP}")
				db_results_ARGGREP = db.execute_query(db_query_ARGGREP)
				
				db_query_FLDTYP = f"SELECT DISTINCT typeNme FROM ECM_FLDTYP WHERE ECM_FLDTYP.BASE = '{row.baseid}'"
				#ECM_FLDTYP.TYPENME
				log_aff.log_base("INFO",f"query : {db_query_FLDTYP}")
				db_results_FLDTYP = db.execute_query(db_query_FLDTYP)
				
				PARAM_ID = row.baseid
				print(f"PARAM_ID = {PARAM_ID}")
				
				PARAM_TYPE = f"DATABASE"
				print(f"PARAM_TYPE = {PARAM_TYPE}")
				
				PARAM_DATA = ""
				
				dataTypeLink = ""
				folderLinkTypes = ""
				folderTypes = ""
				print(len(db_results_ARAMREP))
				for index, row in enumerate(db_results_ARAMREP):
					print(f"info index : {index}")
					if index == len(db_results_ARAMREP) - 1: 
						print("info 1")
						dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2}"""
					else :
						print("info 2")
						dataTypeLink = dataTypeLink + f"""{caractere_special1}"dataTypeId":"{row.AMATCD}","dataTypeDescription":"{row.AMATCD} - Identifiant dossier","dataTypeKind":"02","idLength":15{caractere_special2},"""
						
				for index, row in enumerate(db_results_ARGGREP):
				
					if index == len(db_results_ARGGREP) - 1: 
						folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2}"""
						
					else :
						folderLinkTypes = folderLinkTypes + f"""{caractere_special1}"code":"{row.GGD7NU}","descriptions":[{caractere_special1}"language":"fr","value":"{row.GGD7NU}"{caractere_special2}]{caractere_special2},"""
				
				for index, row in enumerate(db_results_FLDTYP):
				
					if index == len(db_results_FLDTYP) - 1: 
						folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.typeNme}","autoIncrement":false{caractere_special2}"""
						
					else :
						folderTypes = folderTypes + f"""{caractere_special1}"id":"{row.typeNme}","autoIncrement":false{caractere_special2},"""
				
				PARAM_DATA = f"{caractere_special1}{caractere_special3}dataTypeLink{caractere_special3}:" + dataTypeLink + f","
				PARAM_DATA = PARAM_DATA + f"{caractere_special3}folderLinkTypes{caractere_special3}:[" + folderLinkTypes + f"],"
				PARAM_DATA = PARAM_DATA + f"{caractere_special3}folderTypes{caractere_special3}:[" + folderTypes + f"],"
				PARAM_DATA = PARAM_DATA + f"{caractere_special3}isPacMode{caractere_special3}:false,{caractere_special3}descriptions{caractere_special3}:[" + "{"
				PARAM_DATA = PARAM_DATA + PARAM_DATA_FIN
				PARAM_DATA = PARAM_DATA + "}]}"

				print(PARAM_DATA)
				
				RADIATED = "0"
				print(RADIATED)
				
				CREATION_USER = "NULL"
				print(CREATION_USER)
				MODIFICATION_USER = "NULL"
				print(MODIFICATION_USER)
				
				CREATION_DATE = "NULL"
				print(CREATION_DATE)
				MODIFICATION_DATE = "NULL"
				print(MODIFICATION_DATE)
				
				
				#SELECT * from ecm_pacref
				#pac_ref.pacDesc
				#where ecm_pacref.baseid
				print(FORMATTED_JSON)
				
				BR_ID_DOCUMENT = "NULL"
				print(BR_ID_DOCUMENT)
				BR_ID_FOLDER = "NULL"
				print(BR_ID_FOLDER)
				
				query_save = "INSERT INTO ecm_param (param_id, param_type,param_data,radiated,creation_user,modification_user,creation_date,modification_date,formatted_json,br_id_document,br_id_folder)"
				query_save = query_save + f" VALUES ('{PARAM_ID}','{PARAM_TYPE}','{PARAM_DATA}','0',NULL,NULL,NULL,NULL,'{FORMATTED_JSON}',NULL,NULL)"
				
				print(query_save)
				db.execute_query_save(query_save)
				
				
		db.close() # Ferme le co SGBD
		
		if sgbd_db_type == 'DB2':
			log_aff.log_base("INFO",f"Connexion SGBD DB2 non pris en compte pour le moment")
		
	log_aff.log_base("INFO","Traitement terminé.")
	
	print("Appuyez sur Entrée pour fermer la fenêtre.")
	input()