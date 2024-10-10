import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
from datetime import datetime, timedelta

# Fonction pour récupérer les tentatives échouées de la veille dans la base de données
def get_failed_attempts_from_db(db_config):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Récupérer les tentatives échouées de la veille
        yesterday = datetime.now() - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        query = """
        SELECT username, attempt_time, ip_address 
        FROM failed_logins 
        WHERE attempt_time BETWEEN %s AND %s
        """
        cursor.execute(query, (start_time, end_time))

        failed_attempts = cursor.fetchall()

        return failed_attempts

    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
        return []
    finally:
        cursor.close()
        connection.close()

# Fonction pour envoyer l'email avec les tentatives échouées
def send_email(failed_attempts):
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
    message["Subject"] = "Historique des tentatives de connexion échouées - Veille"

    # Générer le corps du message avec les tentatives échouées
    if failed_attempts:
        body = "Voici les tentatives de connexion échouées de la veille :\n\n"
        for attempt in failed_attempts:
            username, attempt_time, ip_address = attempt
            body += f"Utilisateur : {username}, Heure : {attempt_time}, IP : {ip_address}\n"
    else:
        body = "Aucune tentative de connexion échouée n'a été trouvée pour la veille."

    # Attacher le corps du message
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

# Configuration de la base de données
db_config = {
    'user': 'alaa',
    'password': 'alaa',
    'host': '192.168.1.140',
    'database': 'mariadb_logs'
}

# Récupérer les tentatives échouées de la veille
failed_attempts = get_failed_attempts_from_db(db_config)

# Envoyer l'e-mail à l'administrateur
send_email(failed_attempts)