import paramiko
import mysql.connector
import re
from datetime import datetime

# Connexion SSH et récupération des logs du serveur Nginx
def ssh_connect_and_retrieve_logs(hostname, port, username, key_path, log_path, sudo_password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connexion au serveur {hostname}...")
        ssh.connect(hostname, port=port, username=username, key_filename=key_path)

        command = f"sudo -S cat {log_path}"
        stdin, stdout, stderr = ssh.exec_command(command)
        stdin.write(sudo_password + "\n")
        stdin.flush()

        logs = stdout.read().decode('utf-8')
        return logs

    except Exception as e:
        print(f"Erreur lors de la connexion ou de la récupération des logs : {e}")
        return None
    finally:
        ssh.close()

# Analyse des logs pour récupérer les tentatives d'accès échouées (Nginx)
def parse_logs_for_failed_attempts(logs):
    failed_attempts = []
    
    # Expression régulière pour capturer les tentatives d'accès échouées dans les logs Nginx
    regex = re.compile(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[error\] \d+#\d+: \*\d+ user "(.*?)": password mismatch, client: ([\d\.]+),')

    for line in logs.splitlines():
        match = regex.search(line)
        if match:
            timestamp_str, username, ip = match.groups()
            timestamp = datetime.strptime(timestamp_str.strip(), '%Y/%m/%d %H:%M:%S')
            failed_attempts.append((username, timestamp, ip))

    return failed_attempts

# Insertion des tentatives échouées dans la base de données
def store_failed_attempts_to_db(db_config, attempts):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        for attempt in attempts:
            username, timestamp, ip = attempt
            server_role = 'web_server'  # Spécification du rôle du serveur

            # Mise à jour de la requête d'insertion pour inclure server_role
            query = "INSERT INTO failed_logins (username, attempt_time, ip_address, server_role) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (username, timestamp, ip, server_role))

        connection.commit()
        print(f"{len(attempts)} tentatives d'accès échouées ont été stockées dans la base de données.")

    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":

    # Informations de connexion SSH
    hostname = "192.168.1.135"
    port = 22
    username = "alaa"
    key_path = "/home/alaa/.ssh/id_rsa"
    sudo_password = "alaa"
    
    # Chemin vers les logs Nginx
    log_path = "/var/log/nginx/error.log"

    # Informations de la base de données
    db_config = {
        'user': 'alaa',
        'password': 'alaa',
        'host': '192.168.1.140',
        'database': 'mariadb_logs'
    }

    # Récupération des logs via SSH
    logs = ssh_connect_and_retrieve_logs(hostname, port, username, key_path, log_path, sudo_password)

    if logs:
        # Analyse des logs pour les tentatives échouées
        failed_attempts = parse_logs_for_failed_attempts(logs)

        if failed_attempts:
            # Stockage des tentatives échouées dans la base de données
            store_failed_attempts_to_db(db_config, failed_attempts)
        else:
            print("Aucune tentative d'accès échouée trouvée dans les logs.")
    else:
        print("Impossible de récupérer les logs.")