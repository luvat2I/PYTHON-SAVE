# Chemin où Poppler sera installé
$popplerPath = Join-Path -Path $PSScriptRoot -ChildPath "poppler"
$tempPath = Join-Path -Path $PSScriptRoot -ChildPath "temp"

# URL de téléchargement de Poppler
$popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"

# Chemin du fichier ZIP téléchargé
$zipPath = "$tempPath\poppler.zip"

# Télécharger Poppler
Invoke-WebRequest -Uri $popplerUrl -OutFile $zipPath

# Créer le dossier d'installation si nécessaire
if (-Not (Test-Path -Path $popplerPath)) {
    New-Item -ItemType Directory -Path $popplerPath
}

# Extraire le fichier ZIP
Expand-Archive -Path $zipPath -DestinationPath $popplerPath -Force

# Supprimer le fichier ZIP après extraction
Remove-Item -Path $zipPath

# Ajouter Poppler au PATH
$env:Path += ";$popplerPath\poppler-22.04.0-x86_64\bin"

# Afficher le chemin pour vérification
Write-Host "Poppler a été installé dans : $popplerPath"




Write-Host "Le chemin a été ajouté à la variable d'environnement PATH."



# Récupération la variable PATH actuelle
$pathActuel = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)

Write-Host "path actuelle $pathActuel"

# Vérifier si le chemin est déjà présent
#if (-not $pathActuel.Split(';') -contains $nouveauChemin) {
#    # Ajouter le nouveau chemin
#    $nouveauPath = $pathActuel + ";" + $nouveauChemin
#    [System.Environment]::SetEnvironmentVariable("Path", $nouveauPath, [System.EnvironmentVariableTarget]::Machine)
#    Write-Host "Le chemin a été ajouté avec succès."
#} else {
#    Write-Host "Le chemin est déjà présent dans la variable PATH."
#}