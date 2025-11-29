"""
Endpoints Flask pour l'API REST
Permet l'intégration externe ou le déclenchement manuel via API
"""
from flask import Blueprint, request, jsonify
import threading
from src.automation import run_monthly_automation
from src.database import AutomationDB
from src.smappee_client import SmappeeClient
from src.email_notifier import EmailNotifier


# Créer un Blueprint Flask
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/automation/trigger', methods=['POST'])
def trigger_automation():
    """
    Endpoint pour déclencher l'automatisation mensuelle via API externe.
    
    Body JSON attendu:
    {
        "period_start": "2024-01-01",
        "period_end": "2024-01-31"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Corps de requête manquant'}), 400
        
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        
        if not period_start or not period_end:
            return jsonify({'error': 'period_start et period_end sont requis'}), 400
        
        # Lancer l'automatisation en arrière-plan
        thread = threading.Thread(
            target=run_monthly_automation,
            args=(period_start, period_end, False),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'Automatisation démarrée en arrière-plan',
            'period_start': period_start,
            'period_end': period_end
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/automation/status', methods=['GET'])
def get_automation_status():
    """
    Retourne le statut des dernières automatisations.
    
    Query params optionnels:
    - limit: nombre de runs à retourner (défaut: 10)
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        db = AutomationDB()
        runs = db.get_recent_runs(limit=limit)
        
        return jsonify({
            'total': len(runs),
            'runs': runs
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/automation/status/<int:run_id>', methods=['GET'])
def get_run_status(run_id):
    """Retourne le statut d'une exécution spécifique par son ID"""
    try:
        db = AutomationDB()
        runs = db.get_recent_runs(limit=100)
        
        run = next((r for r in runs if r['id'] == run_id), None)
        
        if not run:
            return jsonify({'error': 'Run non trouvé'}), 404
        
        return jsonify(run), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config/test-smappee', methods=['POST'])
def test_smappee():
    """
    Teste la connexion à l'API Smappee.
    
    Body JSON:
    {
        "client_id": "...",
        "client_secret": "..."
    }
    """
    try:
        data = request.get_json()
        
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        if not client_id or not client_secret:
            return jsonify({'error': 'client_id et client_secret requis'}), 400
        
        client = SmappeeClient(client_id, client_secret)
        success, message = client.test_connection()
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config/test-email', methods=['POST'])
def test_email():
    """
    Teste la configuration email SMTP.
    
    Body JSON:
    {
        "smtp_server": "...",
        "smtp_port": 587,
        "smtp_user": "...",
        "smtp_password": "...",
        "test_email": "..."
    }
    """
    try:
        data = request.get_json()
        
        smtp_server = data.get('smtp_server')
        smtp_port = data.get('smtp_port', 587)
        smtp_user = data.get('smtp_user')
        smtp_password = data.get('smtp_password')
        test_email = data.get('test_email')
        
        if not all([smtp_server, smtp_user, smtp_password, test_email]):
            return jsonify({'error': 'Tous les champs sont requis'}), 400
        
        notifier = EmailNotifier(smtp_server, smtp_port, smtp_user, smtp_password)
        
        # Test de connexion
        success, message = notifier.test_connection()
        if not success:
            return jsonify({'success': False, 'message': message}), 400
        
        # Envoi d'un email de test
        success, message = notifier.send_test_email(test_email)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check de l'application"""
    return jsonify({
        'status': 'healthy',
        'service': 'recharge-automation-api',
        'version': '2.0-standalone'
    }), 200