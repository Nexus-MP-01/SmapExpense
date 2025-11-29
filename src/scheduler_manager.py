"""
Gestionnaire de planification (Scheduler) avec APScheduler
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.database import AutomationDB
from src.automation import run_scheduled_job
import atexit

class SchedulerManager:
    _scheduler = None

    @classmethod
    def start(cls):
        """Démarre le planificateur en arrière-plan"""
        if cls._scheduler is None:
            cls._scheduler = BackgroundScheduler()
            cls._scheduler.start()
            # Arrêter proprement le scheduler à la fermeture de l'app
            atexit.register(lambda: cls._scheduler.shutdown())
            
            # Initialiser la tâche basée sur la DB
            cls.update_schedule()

    @classmethod
    def update_schedule(cls):
        """Met à jour la tâche planifiée en fonction de la configuration en DB"""
        if cls._scheduler is None:
            return

        db = AutomationDB()
        config = db.get_config()
        
        # Supprimer la tâche existante si elle existe
        cls._scheduler.remove_all_jobs()
        
        # Valeurs par défaut : Dernier jour du mois à 23:59:59
        mode = config.get('schedule_mode', 'last_day') # 'last_day', 'first_day', 'disabled'
        time_str = config.get('schedule_time', '23:59')
        
        # --- AJOUT: Gestion du mode désactivé ---
        if mode == 'disabled':
            print("📅 Planification : Automatisation désactivée par l'utilisateur.")
            return
        # ---------------------------------------
        
        try:
            hour, minute = time_str.split(':')
        except:
            hour, minute = '23', '59'

        trigger = None
        
        if mode == 'first_day':
            # 1er jour du mois suivant
            trigger = CronTrigger(day=1, hour=hour, minute=minute, second=0)
        else:
            # Dernier jour du mois (défaut)
            # APScheduler gère "last" pour le dernier jour
            trigger = CronTrigger(day='last', hour=hour, minute=minute, second=59)

        # Ajouter la tâche
        cls._scheduler.add_job(
            func=run_scheduled_job,
            trigger=trigger,
            id='monthly_automation',
            name='Automatisation Mensuelle Recharge',
            replace_existing=True
        )
        
        print(f"📅 Planification mise à jour : Mode={mode}, Heure={hour}:{minute}")