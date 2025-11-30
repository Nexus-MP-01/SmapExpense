# SmapExpense - Gestionnaire de Notes de Frais VE

SmapExpense est une application web conçue pour automatiser la gestion
des frais de recharge de véhicules électriques à domicile. Elle se
connecte à votre borne **Smappee**, applique les tarifs officiels de la
**CREG (Belgique)**, génère automatiquement des notes de frais
mensuelles au format PDF et les envoie par mail à l'adresse choisie.

## 🚀 Fonctionnalités Principales

-   **Tableau de bord interactif** : Visualisation des coûts, de la
    consommation (kWh) et de la distribution des sessions de recharge.
-   **Intégration Smappee** : Récupération automatique des sessions via
    l'API Smappee ou import manuel de fichiers CSV.
-   **Tarification CREG Intelligente** : Calcul précis des coûts basé
    sur les tarifs trimestriels officiels.
-   **Génération de PDF** : Création d'une note de frais mensuelle
    détaillée.
-   **Automatisation Complète** : Processus complet (Récupération →
    Calcul → PDF → Email) exécuté automatiquement chaque mois.
-   **Notifications** : Envoi du rapport PDF par email via SMTP.

------------------------------------------------------------------------

## 🛠️ Installation Rapide (Local / PC)

### Prérequis

-   Python 3.8 ou supérieur
-   Compte Smappee (Client ID / Secret)
-   Serveur SMTP pour l'envoi d'emails

### 1. Cloner et Installer

``` bash
git clone https://github.com/Nexus-MP-01/SmapExpense.git
cd SmapExpense
pip install -r requirements.txt
```

### 2. Configuration

Créez un fichier `.env` à la racine et remplissez-le (voir section
Configuration plus bas).

### 3. Lancer

``` bash
python app.py
```

Accédez ensuite à :\
**http://localhost:8050**

------------------------------------------------------------------------

## 🍓 Installation Complète sur Raspberry Pi (Production)

Installation optimisée pour Raspberry Pi OS (Bookworm ou plus récent).

### 1. Préparation du système

``` bash
sudo apt update && sudo apt upgrade -y
sudo apt install git python3-pip python3-venv -y
```

### 2. Récupération du code

``` bash
cd ~
git clone https://github.com/Nexus-MP-01/SmapExpense.git
cd SmapExpense
```

### 3. Création de l'environnement virtuel (Venv)

``` bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configuration (.env)

Créez le fichier :

``` bash
nano .env
```

Contenu recommandé :

``` ini
# API Smappee
SMAPPEE_CLIENT_ID=votre_client_id
SMAPPEE_CLIENT_SECRET=votre_client_secret
SMAPPEE_LOCATION_ID=votre_location_id

# Email (SMTP)
SMTP_SERVER=mail.infomaniak.com
SMTP_PORT=587
SMTP_USER=votre@email.com
SMTP_PASSWORD=votre_mot_de_passe
NOTIFICATION_EMAIL=destinataire@email.com

# App Production
DEBUG=False
HOST=0.0.0.0
PORT=8050
```

### 5. Lancement automatique au démarrage (Systemd)

``` bash
sudo nano /etc/systemd/system/smappee.service
```

Service Systemd :

``` ini
[Unit]
Description=SmapExpense Dashboard
After=network.target

[Service]
User=<VOTRE_USER>
WorkingDirectory=/home/<VOTRE_USER>/SmapExpense
ExecStart=/home/<VOTRE_USER>/SmapExpense/venv/bin/python app.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

Activez et démarrez :

``` bash
sudo systemctl daemon-reload
sudo systemctl enable smappee.service
sudo systemctl start smappee.service
sudo systemctl status smappee.service
```

Votre application est accessible via :\
**http://`<IP_DU_RASPBERRY>`{=html}:8050**

------------------------------------------------------------------------

## ⚙️ Mises à jour futures

``` bash
cd ~/SmapExpense
git pull
./venv/bin/pip install -r requirements.txt
sudo systemctl restart smappee.service
```