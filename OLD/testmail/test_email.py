import subprocess
import os

def test_email(to_email, smtp_from_email, smtp_host, smtp_port, smtp_login_email=None, password=None):
    try:
        # Préparer les arguments pour le script Java
        args = [to_email, smtp_from_email, smtp_host, smtp_port]
        
        # Ajouter l'adresse e-mail de connexion et le mot de passe si fournis
        if smtp_login_email:
            args.append(smtp_login_email)
        if password:
            args.append(password)

        # Chemin vers les fichiers JAR dans le même dossier que le script Python
        jar_path = os.path.join(os.getcwd(), 'javax.mail.jar')
        activation_jar_path = os.path.join(os.getcwd(), 'activation.jar')

        # Appeler le script Java
        result = subprocess.run(
            ['java', '-cp', f"{jar_path};{activation_jar_path};.", 'EmailTester'] + args,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(result.stderr)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    to_email = "test@example.com"  # Remplacez par l'e-mail à tester
    smtp_from_email = "your_from_email@example.com"  # Adresse e-mail d'envoi
    smtp_host = "smtp.example.com"  # Serveur SMTP
    smtp_port = "587"  # Port SMTP

    # Test avec authentification
    smtp_login_email = "your_login_email@example.com"  # Votre adresse e-mail de connexion au SMTP (optionnelle)
    password = "your_password"  # Remplacez par votre mot de passe ou laissez None pour tester sans authentification
    test_email(to_email, smtp_from_email, smtp_host, smtp_port, smtp_login_email, password)

    # Test sans authentification
    # test_email(to_email, smtp_from_email, smtp_host, smtp_port)  # Décommente
