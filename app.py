"""
Point d'entrée de l'application Recharge
"""
import dash
import dash_bootstrap_components as dbc

from config import Config
from src.layout import create_layout
from src.callbacks import register_callbacks
from src.scheduler_manager import SchedulerManager

def create_app():
    """Crée et configure l'application Dash"""
    
    # Initialiser l'application Dash avec Bootstrap
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=Config.SUPPRESS_CALLBACK_EXCEPTIONS
    )
    
    # Charger le template HTML personnalisé
    try:
        with open('template.html', 'r', encoding='utf-8') as f:
            app.index_string = f.read()
    except FileNotFoundError:
        print("⚠️ Fichier template.html non trouvé, utilisation du template par défaut")
    
    # Définir le titre de l'application
    app.title = "SmapExpense"
    
    # Créer le layout
    app.layout = create_layout()
    
    # Enregistrer les callbacks
    register_callbacks(app)
    
    # S'assurer que le dossier data existe
    Config.ensure_data_dir()
    
    # Démarrer le planificateur de tâches (Scheduler)
    # Cela chargera la configuration depuis la DB et lancera le CronTrigger
    SchedulerManager.start()
    
    return app


def main():
    """Lance l'application"""
    app = create_app()
    
    print("=" * 60)
    print("🚗 Application Recharge démarrée avec succès !")
    print("=" * 60)
    print(f"📍 URL locale: http://localhost:{Config.PORT}")
    print(f"🌐 URL réseau: http://{Config.HOST}:{Config.PORT}")
    print("=" * 60)
    print("Appuyez sur CTRL+C pour arrêter l'application")
    print("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=Config.THREADED
    )


if __name__ == '__main__':
    main()