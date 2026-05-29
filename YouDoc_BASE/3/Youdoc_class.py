import zipfile
from pathlib import Path

def safe_extract_zip(zip_path: str, dest_dir: str):
	error = False
	ID_APP = "zipclass"
	
	zip_path = Path(zip_path)
	dest_dir = Path(dest_dir)
	dest_dir.mkdir(parents=True, exist_ok=True)

	with zipfile.ZipFile(zip_path, 'r') as z:
		for member in z.infolist():
			# Empêche le 'zip slip' en vérifiant le chemin final
			member_path = dest_dir.joinpath(member.filename)
			if not member_path.resolve().startswith(dest_dir.resolve()):
				raise Exception(f"Chemin dangereux détecté dans l'archive: {member.filename}")

			# Crée les dossiers parent si nécessaire
			member_path.parent.mkdir(parents=True, exist_ok=True)

			# Si l'entrée est un dossier, continue
			if member.is_dir():
				continue

			# Extrait le fichier
			with z.open(member) as source, open(member_path, "wb") as target:
				target.write(source.read())