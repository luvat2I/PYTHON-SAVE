# Chemin où webdriver sera installé (dans le dossier d'exécution du script)
$webdriverPath = Join-Path -Path $PSScriptRoot -ChildPath "webdriver"
$webdrivertemp = Join-Path -Path $PSScriptRoot -ChildPath "temp"

$webDriverVersion = "136.0.7103.113/win64/chromedriver-win64.zip" #version
$webdriverFolder = "chromedriver-win64\"
$webdriverwin = "$webdriverPath\$webdriverFolder"
$webdriverexe = "$webdriverwin\chromedriver.exe"


Write-Host "installation de webdriver $webDriverVersion dans $webdriverwin"

# Vérifiez si le dossier existe déjà
if (-Not (Test-Path -Path $webdriverPath)) {
    # Si le dossier n'existe pas, créez-le
    New-Item -Path $webdriverPath -ItemType Directory
    Write-Host "Le dossier $cheminDossier a ete cree"
} else {
    Write-Host "Le dossier $cheminDossier existe"
}

# Vérifiez si le dossier existe déjà
if (-Not (Test-Path -Path $webdrivertemp)) {
    # Si le dossier n'existe pas, créez-le
    New-Item -Path $webdrivertemp -ItemType Directory
    Write-Host "Le dossier a été créé : $cheminDossier"
} else {
    Write-Host "Le dossier $cheminDossier existe"
}

Write-Host "telechargement de webdriver dans $webdrivertemp\webdriver.zip"
# URL de téléchargement de chrome driver

$webdriverUrl = "https://storage.googleapis.com/chrome-for-testing-public/$webDriverVersion"

# Chemin du fichier ZIP téléchargé
$zipPath = "$webdrivertemp\webdriver.zip"

Write-Host "Telechargement de webdriver... $zipPath"
Invoke-WebRequest -Uri $webdriverUrl -OutFile $zipPath


# Extraction du fichier ZIP
Write-Host "extraction de webdriver dans $webdriverPath"
#Expand-Archive -Path $zipPath -DestinationPath $webdriverPath -Force
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $webdriverPath)


# Récupération la variable PATH actuelle
$pathActuel = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)

# Récupérer les chemins existants
$cheminsExistants = $pathActuel.Split(';') | ForEach-Object { $_.Trim() }

# Vérifier si le chemin est déjà présent
$cheminPresent = $false
foreach ($chemin in $cheminsExistants) {
    if ($chemin.Equals($webdriverwin, [System.StringComparison]::OrdinalIgnoreCase)) {
        $cheminPresent = $true
        break
    }
}

if (-not $cheminPresent) {
    # Ajouter le nouveau chemin
    $nouveauPath = $pathActuel + ";" + $webdriverwin
    [System.Environment]::SetEnvironmentVariable("Path", $nouveauPath, [System.EnvironmentVariableTarget]::Machine)
    Write-Host "Le path windows a ete ajouté avec succes."
} else {
    Write-Host "Le path windows est deja present dans la variable PATH."
}



