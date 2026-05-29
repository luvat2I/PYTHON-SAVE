import zipfile
from pathlib import Path
import shutil

def liste_zip(fichier_text):
	error = False
	ID_APP = "liste_zip"
	
	with open(fichier_text, "r", encoding="utf-8") as f:
		for ligne in f:
			ligne = ligne.rstrip("\n")
			# traiter la ligne
			print(ligne)


def deplace_fic_rename(src_dir,dst_dir):
	src = Path(src_dir)
	dst = Path(dst_dir)
	shutil.copy(src, dst)

def deplace_fic(src_dir, dst_dir):
	error = False
	ID_APP = "deplace_fic"
	
	src = Path(src_dir)
	dst = Path(dst_dir)
	dst.mkdir(parents=True, exist_ok=True)

	for item in src.iterdir():
		if item.is_file():
			target = dst / item.name
			if target.exists():
				target.unlink()
			shutil.move(str(item), str(target))




def extract_zip(zip_path, dest_dir):
	error = False
	ID_APP = "extract_zip"
	
	# lecture du fichier INI
	if not error :
		try:
			zip_path = Path(zip_path)
			dest_dir = Path(dest_dir)
			dest_dir.mkdir(parents=True, exist_ok=True)
			
			with zipfile.ZipFile(zip_path, 'r') as z:
				for member in z.infolist():
					# Empêche le 'zip slip' en vérifiant le chemin final
					member_path = dest_dir.joinpath(member.filename)

					# Crée les dossiers parent si nécessaire
					member_path.parent.mkdir(parents=True, exist_ok=True)

					# Si l'entrée est un dossier, continue
					if member.is_dir():
						continue

					# Extrait le fichier
					with z.open(member) as source, open(member_path, "wb") as target:
						target.write(source.read())
					
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "001",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	
	if not error :
		try:
			return {
				"code": ID_APP,
				"result": "OK",
				"error": "",
				"message": f"Extraction de {zip_path} vers {dest_dir}",
				"message2": ""
			}
		except Exception as e:
			return {
				"code": ID_APP,
				"result": "",
				"error": "002",
				"message": f"{e}",
				"message2": ""
			}
			error = True
	