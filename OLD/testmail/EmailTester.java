import javax.mail.*;
import javax.mail.internet.*;
import java.util.Properties;

public class EmailTester {
    public static void main(String[] args) {
        if (args.length < 4) {
            System.out.println("Usage: java EmailTester <to> <smtp_from_email> <smtp_host> <smtp_port> [smtp_login_email] [password]");
            return;
        }

        String to = args[0]; // Adresse e-mail à tester
        String smtpFromEmail = args[1]; // Adresse e-mail d'envoi
        String host = args[2]; // Serveur SMTP
        String port = args[3]; // Port SMTP
        String smtpLoginEmail = args.length > 4 ? args[4] : null; // Adresse e-mail de connexion (optionnelle)
        String password = args.length > 5 ? args[5] : null; // Mot de passe (optionnel)

        // Propriétés du mail
        Properties properties = System.getProperties();
        properties.setProperty("mail.smtp.host", host);
        properties.setProperty("mail.smtp.port", port);
        properties.put("mail.smtp.starttls.enable", "true");

        // Créer une session
        Session session;
        if (smtpLoginEmail != null && password != null && !password.isEmpty()) {
            // Authentification requise
            properties.put("mail.smtp.auth", "true");
            session = Session.getInstance(properties, new Authenticator() {
                protected PasswordAuthentication getPasswordAuthentication() {
                    return new PasswordAuthentication(smtpLoginEmail, password);
                }
            });
        } else {
            // Pas d'authentification
            properties.put("mail.smtp.auth", "false");
            session = Session.getInstance(properties);
        }

        try {
            // Créer un objet MimeMessage
            MimeMessage message = new MimeMessage(session);
            message.setFrom(new InternetAddress(smtpFromEmail)); // Utiliser l'adresse d'envoi
            message.addRecipient(Message.RecipientType.TO, new InternetAddress(to));
            message.setSubject("Test Email");
            message.setText("This is a test email.");

            // Envoyer le message
            Transport.send(message);
            System.out.println("Email sent successfully to " + to);
        } catch (MessagingException mex) {
            mex.printStackTrace();
            System.out.println("Failed to send email to " + to);
        }
    }
}
