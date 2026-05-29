Write-Host "Installation"
$pythonScript = "youdoc_flatten.py"
Start-Process python -ArgumentList $pythonScript, "start" -Verb RunAs

Write-Host "PyPDF2 pdf2image reportlab requests ont ete installes avec succes."

# Demande à l'utilisateur d'appuyer sur Entrée pour fermer PowerShell
Read-Host -Prompt "Appuyez sur Entree pour fermer PowerShell"