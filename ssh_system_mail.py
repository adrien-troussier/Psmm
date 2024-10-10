import paramiko
import pymysql
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration de la base de données
db_host = "192.168.1.140"
db_user = "alaa"
db_password = "alaa"
db_name = "system_stats"

# Informations des serveurs à monitorer
servers = [
    {"hostname": "192.168.1.140", "role": "mariadb"},
    {"hostname": "192.168.1.133", "role": "ftp"},
    {"hostname": "192.168.1.135", "role": "nginx_web"}
]

# Informations de connexion SSH
username = "alaa"
key_path = "/home/alaa/.ssh/id_rsa"
port = 22

# Seuils d'alerte
CPU_THRESHOLD = 70.0  # Pourcentage
RAM_THRESHOLD = 80.0  # Pourcentage
DISK_THRESHOLD = 90.0  # Pourcentage

# Commandes pour récupérer l'état système
commands = {
    "cpu": "top -bn1 | grep 'Cpu(s)'",
    "ram": "free -m",
    "disk": "df -h /"
}

# Fonction pour envoyer un email si une alerte est détectée
def send_alert_email(server_role, metric, value, threshold):
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    sender_email = "alaa.k@live.fr"
    receiver_email = "kaidahmedalaa@gmail.com"
    password = "enfsockffsfsyiab"

    subject = f"Alerte système : {metric} dépassé sur {server_role}"
    body = f"Attention, le {metric} sur le serveur {server_role} a atteint {value}%, dépassant le seuil de {threshold}%."

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        print(f"Alerte email envoyée pour {server_role} : {metric} = {value}%")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'alerte email : {e}")

# Fonction pour exécuter une commande sur un serveur via SSH
def ssh_connect_and_execute(hostname, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key_file(key_path)
        ssh.connect(hostname, port=port, username=username, pkey=private_key)

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        return output
    except Exception as e:
        print(f"Erreur lors de la connexion ou de l'exécution de la commande sur {hostname}: {e}")
        return None
    finally:
        ssh.close()

# Fonction pour extraire les informations système depuis les commandes
def get_system_status(hostname, role):
    status = {}
    
    # Récupérer l'état CPU
    cpu_output = ssh_connect_and_execute(hostname, commands['cpu'])
    if cpu_output:
        parts = cpu_output.strip().split(", ")
        cpu_user = float(parts[0].split()[1].replace(',', '.'))
        cpu_system = float(parts[1].split()[0].replace(',', '.'))
        cpu_idle = float(parts[3].split()[0].replace(',', '.'))
        cpu_usage = 100 - cpu_idle  # Calcul de l'utilisation totale du CPU
        status['cpu_user'] = cpu_user
        status['cpu_system'] = cpu_system
        status['cpu_idle'] = cpu_idle

        # Vérification du seuil CPU
        if cpu_usage > CPU_THRESHOLD:
            send_alert_email(role, "utilisation CPU", cpu_usage, CPU_THRESHOLD)

    # Récupérer l'état RAM
    ram_output = ssh_connect_and_execute(hostname, commands['ram'])
    if ram_output:
        parts = ram_output.strip().split("\n")[1].split()
        total_ram = int(parts[1])
        used_ram = int(parts[2])
        free_ram = int(parts[3])
        ram_usage = (used_ram / total_ram) * 100  # Pourcentage de RAM utilisée
        status['total_ram'] = total_ram
        status['used_ram'] = used_ram
        status['free_ram'] = free_ram

        # Vérification du seuil RAM
        if ram_usage > RAM_THRESHOLD:
            send_alert_email(role, "utilisation RAM", ram_usage, RAM_THRESHOLD)

    # Récupérer l'état DISK
    disk_output = ssh_connect_and_execute(hostname, commands['disk'])
    if disk_output:
        parts = disk_output.strip().split("\n")[1].split()
        total_disk = parts[1]
        used_disk = parts[2]
        free_disk = parts[3]
        disk_usage = float(parts[4].replace('%', ''))  # Utilisation disque en %
        status['total_disk'] = total_disk
        status['used_disk'] = used_disk
        status['free_disk'] = free_disk

        # Vérification du seuil DISK
        if disk_usage > DISK_THRESHOLD:
            send_alert_email(role, "utilisation Disque", disk_usage, DISK_THRESHOLD)
    
    return status

# Fonction pour insérer les données dans la base de données
def store_system_status(db_connection, server_role, status):
    try:
        with db_connection.cursor() as cursor:
            query = """
            INSERT INTO system_status (server_role, timestamp, cpu_user, cpu_system, cpu_idle, total_ram, used_ram, free_ram, total_disk, used_disk, free_disk)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            timestamp = datetime.now()
            cursor.execute(query, (
                server_role,
                timestamp,
                status.get('cpu_user', 0),
                status.get('cpu_system', 0),
                status.get('cpu_idle', 0),
                status.get('total_ram', 0),
                status.get('used_ram', 0),
                status.get('free_ram', 0),
                status.get('total_disk', 'N/A'),
                status.get('used_disk', 'N/A'),
                status.get('free_disk', 'N/A')
            ))
        db_connection.commit()
    except Exception as e:
        print(f"Erreur lors de l'insertion dans la base de données : {e}")

# Fonction pour supprimer les anciennes données (plus de 72 heures)
def delete_old_data(db_connection):
    try:
        with db_connection.cursor() as cursor:
            delete_query = """
            DELETE FROM system_status WHERE timestamp < %s
            """
            cutoff_time = datetime.now() - timedelta(hours=72)
            cursor.execute(delete_query, (cutoff_time,))
        db_connection.commit()
    except Exception as e:
        print(f"Erreur lors de la suppression des anciennes données : {e}")

if __name__ == "__main__":
    # Connexion à la base de données
    db_connection = pymysql.connect(host=db_host, user=db_user, password=db_password, db=db_name)
    
    # Récupérer l'état des ressources sur chaque serveur
    for server in servers:
        hostname = server['hostname']
        role = server['role']
        print(f"Récupération de l'état du serveur {role} ({hostname})")
        
        system_status = get_system_status(hostname, role)
        if system_status:
            store_system_status(db_connection, role, system_status)
    
    # Supprimer les anciennes données (plus de 72h)
    delete_old_data(db_connection)
    
    # Fermeture de la connexion à la base de données
    db_connection.close()