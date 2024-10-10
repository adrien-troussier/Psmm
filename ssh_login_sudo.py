import paramiko
import os
import sys
import getpass  # Importation du module pour masquer le mot de passe

# Forcer l'encodage UTF-8 de la sortie
sys.stdout.reconfigure(encoding='utf-8')

# Fonction pour se connecter et exécuter une commande avec sudo
def ssh_connect_and_execute(host, port=22, username='monitor', private_key_path='/home/adrien/.ssh/id_ed25519', command=None, sudo_password=None):
    try:
        # Initialiser le client SSH
        client = paramiko.SSHClient()

        # Ajouter automatiquement les nouvelles clés SSH au known_hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Charger la clé privée
        private_key = paramiko.Ed25519Key(filename=private_key_path)

        # Se connecter au serveur en utilisant la clé privée
        client.connect(host, port=port, username=username, pkey=private_key)
        print(f"Connexion réussie à {host} !")

        # Si aucune commande n'est passée, demander à l'utilisateur d'en entrer une
        if not command:
            command = input("Entrez la commande à exécuter (ex : ls, df, etc.) : ")

        # Ajouter sudo à la commande et passer le mot de passe sudo
        full_command = f"echo {sudo_password} | sudo -S {command}"

        # Exécuter la commande avec sudo
        stdin, stdout, stderr = client.exec_command(full_command)

        # Récupérer et afficher la sortie de la commande
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        if output:
            print("Résultat de la commande :")
            print(output)
        if error:
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

# Affichage du menu pour la sélection du serveur
print("Sélectionnez l'option de connexion :")
print("1. Connexion FTP")
print("2. Connexion Web")
print("3. Connexion MariaDB")

# Demander à l'utilisateur de choisir une option
menu = input("Entrez le numéro correspondant au type de connexion : ")

# Dictionnaire pour les adresses IP des différents serveurs
hosts = {
    "1": "172.31.254.250",  # Serveur FTP
    "2": "172.31.254.251",  # Serveur Web
    "3": "172.31.254.252"   # Serveur MariaDB
}

# Vérifier si l'option est valide et assigner l'hôte correspondant
host = hosts.get(menu)

if host:
    # Demander le mot de passe sudo sans l'afficher
    sudo_password = getpass.getpass("Entrez le mot de passe sudo : ")

    # Exécuter la fonction avec la clé privée et l'utilisateur fixés
    ssh_connect_and_execute(host, sudo_password=sudo_password)
else:
    print("Option invalide, veuillez réessayer.")