$tempPath = Join-Path -Path $PSScriptRoot -ChildPath "temp"
$installPath = Join-Path -Path $PSScriptRoot -ChildPath "odbc"
$odbcPath = "$tempPath\msodbcsql18.msi"
$odbcUrl = "https://go.microsoft.com/fwlink/?linkid=2280794"  # Lien pour le pilote ODBC 18

# Créer le dossier temp s'il n'existe pas
if (-Not (Test-Path -Path $tempPath)) {
    New-Item -ItemType Directory -Path $tempPath
}

# Créer le dossier d'installation s'il n'existe pas
if (-Not (Test-Path -Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath
}

# Télécharger le fichier d'installation
Invoke-WebRequest -Uri $odbcUrl -OutFile $odbcPath

# Installer le pilote ODBC
Start-Process -FilePath $odbcPath -ArgumentList " /norestart" -Wait

# Vérifier si l'installation a réussi
if (Get-Package -Name "Microsoft ODBC Driver 18 for SQL Server" -ErrorAction SilentlyContinue) {
    Write-Host "Le pilote ODBC 18 a été installé avec succès."
} else {
    Write-Host "L'installation du pilote ODBC 18 a échoué."
}