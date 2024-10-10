import paramiko
import os
import sys
import time
import getpass

# Forcer l'encodage UTF-8 de la sortie
sys.stdout.reconfigure(encoding='utf-8')

# Fonction pour se connecter via SSH et exécuter une commande MySQL
def ssh_connect_and_execute_mysql_command(host, port=22, username='monitor', private_key_path='/home/adrien/.ssh/id_ed25519', mysql_command=None):
    try:
        # Initialiser le client SSH
        client = paramiko.SSHClient()

        # Ajouter automatiquement les nouvelles clés SSH au known_hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Charger la clé privée
        private_key = paramiko.Ed25519Key(filename=private_key_path)

        # Se connecter au serveur en utilisant la clé privée
        client.connect(host, port=port, username=username, pkey=private_key)

        # Ouvrir un shell interactif
        shell = client.invoke_shell()

        # Demander le mot de passe pour MySQL
        mysql_password = getpass.getpass("Entrez le mot de passe MySQL pour l'utilisateur 'monitor' : ")

        # Exécuter la commande MySQL pour se connecter
        shell.send("mysql -u monitor -p\n")
        time.sleep(1)  # Attendre que le shell soit prêt

        # Envoyer le mot de passe
        shell.send(f"{mysql_password}\n")
        time.sleep(1)  # Attendre que la connexion soit établie

        # Envoyer la commande MySQL
        shell.send(f"{mysql_command}\n")
        time.sleep(1)  # Attendre l'exécution de la commande

        # Récupérer et afficher la sortie
        output = shell.recv(65535).decode('utf-8')
        print("Résultat de la commande MySQL :")
        print(output)

    except paramiko.AuthenticationException:
        print("Erreur d'authentification.")
    except FileNotFoundError:
        print(f"Clé privée non trouvée : {private_key_path}")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    finally:
        # Fermer la connexion SSH
        client.close()
        print("Connexion SSH fermée.")

host="172.31.254.252"
# Demander la commande SQL à exécuter
ssh_connect_and_execute_mysql_command(host, mysql_command="show databases;")