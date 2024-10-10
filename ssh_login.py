import paramiko
import os
import sys

menu = 0

# Forcer l'encodage UTF-8 de la sortie
sys.stdout.reconfigure(encoding='utf-8')

# Fonction pour se connecter et exécuter la commande
def ssh_connect_and_execute(host, port=22, username='monitor', private_key_path='/home/adrien/.ssh/id_ed25519', command=None):
    try:
        # Initialiser le client SSH
        client = paramiko.SSHClient()

        # Ajouter automatiquement les nouvelles clés SSH au known_hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Charger la clé privée
        private_key = paramiko.Ed25519Key(filename=private_key_path)

        # Se connecter au serveur en utilisant la clé privée
        client.connect(host, port=port, username=username, pkey=private_key)
        print("Connexion réussie !")

        # Si aucune commande n'est passée, demander à l'utilisateur d'en entrer une
        if not command:
            command = input("Entrez la commande à exécuter (ex : ls, df, etc.) : ")

        # Exécuter la commande shell
        stdin, stdout, stderr = client.exec_command(command)

        # Récupérer et afficher la sortie de la commande
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        if output:
            print("Résultat de la commande :")
            print(output)
        if error:
            print("Erreurs :")
            print(error)

    except paramiko.AuthenticationException:
        print("Erreur d'authentification.")
    except FileNotFoundError:
        print(f"Clé privée non trouvée : {private_key_path}")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    finally:
        # Fermer la connexion
        client.close()
        print("Connexion SSH fermée.")

# Configuration de la connexion SSH
print("1. Connexion FTP")
print("2. Connexion Web")
print("3. Connexion Mariadb")

menu = input("Entrez l'adresse IP du serveur : ")

hosts = {
        "1": "172.31.254.250",
        "2": "172.31.254.251",
        "3": "172.31.254.252"
}

host = hosts.get(menu)

if host:
    ssh_connect_and_execute(host)
else:
    print("Option invalide, veuillez réessayer")