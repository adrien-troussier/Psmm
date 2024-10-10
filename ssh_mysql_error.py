import paramiko
import mysql.connector
import re
from datetime import datetime

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

def parse_logs_for_failed_attempts(logs):
    failed_attempts = []
    
    # Ajustement de l'expression régulière pour capturer les tentatives échouées
    regex = re.compile(r"(\d{4}-\d{2}-\d{2} \s+\d{1,2}:\d{2}:\d{2}) \d+\s+\[Warning\] Access denied for user '([\w@]+)'@'([\d\.]+)' \(using password: (YES|NO)\)")

    for line in logs.splitlines():
        match = regex.search(line)
        if match:
            timestamp_str, username, ip, _ = match.groups()  # Ignorer le mot de passe
            timestamp = datetime.strptime(timestamp_str.strip(), '%Y-%m-%d %H:%M:%S')
            failed_attempts.append((username, timestamp, ip))

    return failed_attempts

def store_failed_attempts_to_db(db_config, attempts):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        for attempt in attempts:
            username, timestamp, ip = attempt
            query = "INSERT INTO failed_logins (username, attempt_time, ip_address) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, timestamp, ip))

        connection.commit()
        print(f"{len(attempts)} tentatives d'accès échouées ont été stockées dans la base de données.")

    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    hostname = "192.168.1.140"
    port = 22
    username = "alaa"
    key_path = "/home/alaa/.ssh/id_rsa"
    sudo_password = "alaa"
    log_path = "/var/log/mysql/error.log"

    db_config = {
        'user': 'alaa',
        'password': 'alaa',
        'host': '192.168.1.140',
        'database': 'mariadb_logs'
    }

    logs = ssh_connect_and_retrieve_logs(hostname, port, username, key_path, log_path, sudo_password)

    if logs:
        failed_attempts = parse_logs_for_failed_attempts(logs)

        if failed_attempts:
            store_failed_attempts_to_db(db_config, failed_attempts)
        else:
            print("Aucune tentative d'accès échouée trouvée dans les logs.")
    else:
        print("Impossible de récupérer les logs.")