# Définir le chemin du dossier temporaire et le chemin d'installation
$tempPath = Join-Path -Path $PSScriptRoot -ChildPath "temp"
$pythonPath = "$tempPath\python-3.13.3.exe"
$installPath = Join-Path -Path $PSScriptRoot -ChildPath "python"
$pythoninstall = "$installPath"
$pythonexe = "$installPath\python.exe"

# Créer le dossier temp s'il n'existe pas
if (-Not (Test-Path -Path $tempPath)) {
    New-Item -ItemType Directory -Path $tempPath
}

# Créer le dossier d'installation s'il n'existe pas
if (-Not (Test-Path -Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath
}

$pythonInstallerUrl = "https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe"

Write-Host "Telechargement de Python... $pythonInstallerUrl"
Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $pythonPath

Write-Host "Installation de Python en cours..."
Start-Process -FilePath $pythonPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 TargetDir=$installPath" -Wait

Write-Host "Python a ete installe avec succes."


# Récupération la variable PATH actuelle
$pathActuel = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)

# Récupérer les chemins existants
$cheminsExistants = $pathActuel.Split(';') | ForEach-Object { $_.Trim() }
Write-Host "$pathActuel"
Write-Host "$installPath"
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

Write-Host "Installation de la bibliothèques..."
# Exécuter le script Python pour installer Selenium
Start-Process -FilePath $pythonExe -ArgumentList "-m pip install selenium" -Wait

