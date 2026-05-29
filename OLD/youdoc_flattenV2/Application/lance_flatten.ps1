# Chemin vers le script Python
$scriptPath = "C:\LUVATEST\DEV\youdoc_flatten.py"  # Remplacez par le chemin vers votre script Python

if (Test-Path $scriptPath) {
	# Exécute le script Python
	python $scriptPath
} else {
	Write-Output "Le fichier Python n'existe pas à l'emplacement  : $scriptPath"
}