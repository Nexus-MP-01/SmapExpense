"""
Configuration centralisée de l'application Recharge
Charge les variables d'environnement depuis le fichier .env
"""
import os
from dotenv import load_dotenv

# Charger les variables du fichier .env s'il existe
load_dotenv()

class Config:
    """Configuration de l'application"""
    
    # Chemins
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    PDF_OUTPUT_DIR = os.path.join(DATA_DIR, 'generated_pdfs')
    
    # Fichiers
    CREG_TARIFFS_JSON_FILE = os.path.join(DATA_DIR, 'creg_tariffs.json')
    LOGO_PATH = os.path.join(ASSETS_DIR, 'logo_nexus-mp.png')
    
    # Paramètres de l'application
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8050))
    THREADED = True
    
    # Constantes métier
    TVA_RATE = 0.06
    
    # Régions disponibles pour les tarifs CREG
    REGIONS = ['Flandre', 'Bruxelles', 'Wallonie']
    DEFAULT_REGION = 'Bruxelles'
    
    # Configuration Dash
    SUPPRESS_CALLBACK_EXCEPTIONS = True
    
    # Logo dimensions (en cm)
    LOGO_WIDTH_CM = 3.64
    LOGO_HEIGHT_CM = 1.5
    
    # Couleurs
    SAGE_GREEN = '#98C0A3'
    SAGE_GREEN_HOVER = '#7FA88E'
    DARK_GREY = '#4a4a4a'
    LIGHT_GREY = '#f5f5f5'
    
    # --- Configuration Smappee (Chargée depuis .env) ---
    SMAPPEE_CLIENT_ID = os.environ.get('SMAPPEE_CLIENT_ID', '')
    SMAPPEE_CLIENT_SECRET = os.environ.get('SMAPPEE_CLIENT_SECRET', '')
    SMAPPEE_LOCATION_ID = os.environ.get('SMAPPEE_LOCATION_ID', '')
    
    # --- Configuration Email (Chargée depuis .env) ---
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL', '')
    
    # Intervalle de rafraîchissement automatique (en ms) pour le dashboard
    AUTO_REFRESH_INTERVAL = 30000  # 30 secondes
    
    @classmethod
    def ensure_data_dir(cls):
        """Crée les dossiers nécessaires s'ils n'existent pas"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.PDF_OUTPUT_DIR, exist_ok=True)
    
    @classmethod
    def ensure_assets_dir(cls):
        """Crée le dossier assets s'il n'existe pas"""
        os.makedirs(cls.ASSETS_DIR, exist_ok=True)