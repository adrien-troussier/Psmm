import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email():
    # Paramètres du serveur Outlook (Live.com)
    smtp_server = "smtp.office365.com"
    smtp_port = 587  # Port TLS
    sender_email = "alaa.k@live.fr"  # Votre adresse Outlook
    receiver_email = "kaidahmedalaa@gmail.com"  # Adresse du destinataire
    password = "enfsockffsfsyiab"  # Votre mot de passe Outlook

    # Créer le message email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email depuis Python via Outlook"

    # Corps du message
    body = "Bonjour, ceci est un e-mail de test envoyé via un script Python en utilisant Outlook."
    message.attach(MIMEText(body, "plain"))

    # Connexion au serveur SMTP et envoi de l'e-mail
    try:
        # Connexion au serveur SMTP Outlook
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Sécurise la connexion
        server.login(sender_email, password)  # Authentification

        # Envoyer l'e-mail
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email envoyé avec succès!")

        # Fermer la connexion au serveur
        server.quit()

    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")

# Exécution de la fonction
send_email()