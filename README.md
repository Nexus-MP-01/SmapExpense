# SmapExpense - Gestionnaire de Notes de Frais VE

SmapExpense est une application web conçue pour automatiser la gestion
des frais de recharge de véhicules électriques à domicile. Elle se
connecte à votre borne **Smappee**, applique les tarifs officiels de la
**CREG (Belgique)**, génère automatiquement des notes de frais
mensuelles au format PDF et les envoi par mail à l'adresse choisie.

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

## 🛠️ Installation

### Prérequis

-   Python 3.8 ou supérieur
-   Compte Smappee (Client ID / Secret)
-   Serveur SMTP pour l'envoi d'emails

### 1. Cloner et Installer

``` bash
git clone <votre-repo-url>
cd SMAPPEE
pip install -r requirements.txt
```

Pour installer les librairies Python nécessaires, placez-vous à la racine du projet puis exécutez :

```bash
pip install -r requirements.txt


### 2. Configuration (.env)

Créez un fichier `.env` :

    # API Smappee
    SMAPPEE_CLIENT_ID=votre_client_id
    SMAPPEE_CLIENT_SECRET=votre_client_secret
    SMAPPEE_LOCATION_ID=votre_location_id

    # Email (SMTP)
    SMTP_SERVER=mail.votre-serveur.com
    SMTP_PORT=587
    SMTP_USER=votre@email.com
    SMTP_PASSWORD=votre_mot_de_passe
    NOTIFICATION_EMAIL=destinataire@email.com

    # App
    DEBUG=False
    HOST=0.0.0.0
    PORT=8050

Les paramètres peuvent aussi être configurés via l'interface web (onglet
Automatisation).

## ▶️ Utilisation

``` bash
python app.py
```

Accédez à l'application :
**http://localhost:8050**

-   **Analyse Manuelle** : exploration des données et tests.
-   **Automatisation** : état du planificateur, historique,
    configuration.

## 🍓 Installation sur Raspberry Pi (Headless)

### 1. Préparation

``` bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip git -y
```

### 2. Installation

Clonez le projet sur votre Raspberry Pi et installez les dépendances.

### 3. Création du Service (systemd)

Créez le fichier :

``` bash
sudo nano /etc/systemd/system/smappee.service
```

Contenu :

    [Unit]
    Description=SmapExpense Dashboard
    After=network.target

    [Service]
    User=pi
    WorkingDirectory=/home/pi/SmappeeApp/SMAPPEE
    ExecStart=/usr/bin/python3 /home/pi/SmappeeApp/SMAPPEE/app.py
    Restart=always
    RestartSec=10
    Environment="PYTHONUNBUFFERED=1"

    [Install]
    WantedBy=multi-user.target

### 4. Activation

``` bash
sudo systemctl daemon-reload
sudo systemctl enable smappee.service
sudo systemctl start smappee.service
```

Vérifier :

``` bash
sudo systemctl status smappee.service
```

L'application sera accessible à l'adresse :
**http://`<IP_DU_PI>`{=html}:8050**
