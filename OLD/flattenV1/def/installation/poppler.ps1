# Chemin où Poppler sera installé
$popplerPath = Join-Path -Path $PSScriptRoot -ChildPath "poppler"
$tempPath = Join-Path -Path $PSScriptRoot -ChildPath "temp"

# Créer le dossier d'installation si nécessaire
if (-Not (Test-Path -Path $tempPath)) {
    New-Item -ItemType Directory -Path $tempPath
}
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
# Remove-Item -Path $zipPath

$installPath = "$popplerPath\poppler-24.08.0\Library\bin"

# Récupération la variable PATH actuelle
$pathActuel = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)

# Récupérer les chemins existants
$cheminsExistants = $pathActuel.Split(';') | ForEach-Object { $_.Trim() }

# Vérifier si le chemin est déjà présent
$cheminPresent = $false
foreach ($chemin in $cheminsExistants) {
    if ($chemin.Equals($installPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        $cheminPresent = $true
        break
    }
}

if (-not $cheminPresent) {
    # Ajouter le nouveau chemin
    $nouveauPath = $pathActuel + ";" + $installPath
    [System.Environment]::SetEnvironmentVariable("Path", $nouveauPath, [System.EnvironmentVariableTarget]::Machine)
    Write-Host "Le path windows a ete ajouté avec succes."
} else {
    Write-Host "Le path windows est deja present dans la variable PATH."
}


# Demande à l'utilisateur d'appuyer sur Entrée pour fermer PowerShell
Read-Host -Prompt "Appuyez sur Entree pour fermer PowerShell"