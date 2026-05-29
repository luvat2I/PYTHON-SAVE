Write-Host "Installation de la bibliothèques..."
# Exécuter le script Python pour installer Selenium
Start-Process -FilePath $pythonExe -ArgumentList "-m pip install selenium" -Wait