# src/automation.py
"""
Logique d'automatisation mensuelle - Flux simplifié
Smappee → Calcul avec CREG → PDF → Email
"""
import os
import pandas as pd
from datetime import datetime
from config import Config
from src.database import AutomationDB
from src.smappee_client import SmappeeClient
from src.email_notifier import EmailNotifier
from src.pdf_generator import generate_monthly_pdf_auto
from src.utils import get_previous_month_period, get_current_month_period

def run_scheduled_job():
    """
    Fonction appelée par le scheduler (APScheduler).
    Calcule automatiquement la période en fonction de la date du jour.
    """
    print("⏰ Exécution de la tâche planifiée...")
    now = datetime.now()
    
    # Si on est le 1er du mois, on traite le mois précédent
    if now.day == 1:
        start_date, end_date = get_previous_month_period()
    else:
        # Sinon on traite le mois courant
        start_date, end_date = get_current_month_period()
        
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()
    
    print(f"📅 Période calculée pour l'automatisation : {start_str} au {end_str}")
    
    run_monthly_automation(start_str, end_str, manual_trigger=False)


def run_monthly_automation(period_start, period_end, manual_trigger=False):
    """
    Exécute l'automatisation mensuelle complète.
    Récupère la config depuis la DB (prioritaire) ou le fichier config (fallback .env).
    """
    db = AutomationDB()
    
    # Créer une nouvelle exécution dans l'historique
    run_id = db.create_run(period_start, period_end)
    
    try:
        # Récupérer la configuration depuis la DB
        # Si la DB est vide, on prend les valeurs par défaut de Config (qui viennent du .env)
        db_config = db.get_config()
        
        # Helper pour prendre DB sinon Config/.env
        def get_conf(key, default_val):
            return db_config.get(key) if db_config and db_config.get(key) else default_val

        # 1. Config Email
        notification_email = get_conf('notification_email', Config.NOTIFICATION_EMAIL)
        
        # 2. Config Smappee
        smappee_client_id = get_conf('smappee_client_id', Config.SMAPPEE_CLIENT_ID)
        smappee_client_secret = get_conf('smappee_client_secret', Config.SMAPPEE_CLIENT_SECRET)
        smappee_location_id = get_conf('smappee_location_id', Config.SMAPPEE_LOCATION_ID)
        
        # 3. Config SMTP
        smtp_server = get_conf('smtp_server', Config.SMTP_SERVER)
        smtp_port = get_conf('smtp_port', Config.SMTP_PORT)
        smtp_user = get_conf('smtp_user', Config.SMTP_USER)
        smtp_password = get_conf('smtp_password', Config.SMTP_PASSWORD)
        
        # Vérification des configs critiques
        if not notification_email:
             raise Exception("Email de notification manquant (.env ou Config)")
        
        if not all([smappee_client_id, smappee_client_secret, smappee_location_id]):
            raise Exception("Configuration Smappee incomplète (Vérifiez .env ou Config)")

        if not all([smtp_server, smtp_user, smtp_password]):
             raise Exception("Configuration SMTP incomplète (Vérifiez .env ou Config)")

        # ====================================================================
        # ÉTAPE 1 : Récupération des données Smappee
        # ====================================================================
        db.update_run(run_id, 'fetch_data', 'pending', 'Connexion à Smappee...')
        
        smappee = SmappeeClient(smappee_client_id, smappee_client_secret)
        
        if not smappee.authenticate():
            raise Exception("Échec de l'authentification Smappee")
        
        # Appel avec 3 arguments : ID, Début, Fin
        df = smappee.get_charging_sessions(smappee_location_id, period_start, period_end)
        
        if df is None or len(df) == 0:
            msg = f"Aucune session trouvée pour la période {period_start} - {period_end}"
            print(f"⚠️ {msg}")
            db.update_run(run_id, 'fetch_data', 'warning', msg)
            return False, msg, run_id
        
        db.update_run(run_id, 'fetch_data', 'success', f'{len(df)} sessions récupérées')
        
        # ====================================================================
        # ÉTAPE 2 : Génération du PDF avec tarifs CREG
        # ====================================================================
        db.update_run(run_id, 'generate_pdf', 'pending', 'Génération du PDF...')
        
        # Utilisation de la colonne mappée par SmappeeClient
        vehicles = df['Nom de la borne de recharge'].unique().tolist()
        
        pdf_path = generate_monthly_pdf_auto(
            df, period_start, period_end, vehicles
        )
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise Exception("Erreur lors de la création du fichier PDF")
        
        db.update_run(run_id, 'generate_pdf', 'success', f'PDF généré: {os.path.basename(pdf_path)}', pdf_path=pdf_path)
        
        # ====================================================================
        # ÉTAPE 3 : Envoi par email
        # ====================================================================
        db.update_run(run_id, 'send_email', 'pending', f'Envoi à {notification_email}...')
        
        notifier = EmailNotifier(smtp_server, int(smtp_port), smtp_user, smtp_password)
        
        success, message = notifier.send_automation_success(
            notification_email, 
            period_start, 
            period_end, 
            pdf_path
        )
        
        if not success:
            raise Exception(f"Échec envoi email: {message}")
        
        db.update_run(run_id, 'send_email', 'success', f'Envoyé à {notification_email}')
        
        # ====================================================================
        # Finalisation
        # ====================================================================
        db.update_run(run_id, 'completed', 'success', 'Terminé avec succès')
        print("✅ Automatisation réussie.")
        return True, "Succès", run_id
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ Erreur: {error_message}")
        db.update_run(run_id, 'error', 'failed', error_message)
        
        # Tenter d'envoyer un mail d'alerte en cas d'échec
        try:
            # On ré-essaie de récupérer la config SMTP pour l'alerte
            config = db.get_config()
            s_server = config.get('smtp_server', Config.SMTP_SERVER)
            s_user = config.get('smtp_user', Config.SMTP_USER)
            s_pass = config.get('smtp_password', Config.SMTP_PASSWORD)
            s_port = int(config.get('smtp_port', Config.SMTP_PORT))
            target = config.get('notification_email', Config.NOTIFICATION_EMAIL)
            
            if s_server and s_user:
                notifier = EmailNotifier(s_server, s_port, s_user, s_pass)
                notifier.send_automation_error(target, period_start, period_end, error_message)
        except:
            pass # Si ça échoue aussi, on abandonne silencieusement l'alerte
        
        return False, error_message, run_id