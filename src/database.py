"""
Gestion de la base de données pour le tracking des automatisations
"""
import sqlite3
import os
from datetime import datetime
from config import Config


class AutomationDB:
    """Classe pour gérer la base de données SQLite des automatisations"""
    
    def __init__(self):
        self.db_path = os.path.join(Config.DATA_DIR, 'automations.db')
        self.init_database()
    
    def init_database(self):
        """Initialise les tables de la base de données"""
        Config.ensure_data_dir()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des exécutions d'automatisation
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS automation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TIMESTAMP,
            period_start DATE,
            period_end DATE,
            status TEXT,
            step TEXT,
            message TEXT,
            pdf_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table de configuration (Key-Value store)
        # Utilisé aussi pour stocker le cache API (key='latest_api_cache')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS automation_config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_run(self, period_start, period_end):
        """Crée une nouvelle exécution d'automatisation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO automation_runs (run_date, period_start, period_end, status, step, message)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), period_start, period_end, 'pending', 'initialized', 'Automatisation initialisée'))
        
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return run_id
    
    def update_run(self, run_id, step, status, message='', pdf_path=None):
        """Met à jour une exécution d'automatisation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if pdf_path:
            cursor.execute('''
            UPDATE automation_runs 
            SET step = ?, status = ?, message = ?, pdf_path = ?, updated_at = ?
            WHERE id = ?
            ''', (step, status, message, pdf_path, datetime.now(), run_id))
        else:
            cursor.execute('''
            UPDATE automation_runs 
            SET step = ?, status = ?, message = ?, updated_at = ?
            WHERE id = ?
            ''', (step, status, message, datetime.now(), run_id))
        
        conn.commit()
        conn.close()
    
    def get_latest_run(self):
        """Récupère la dernière exécution"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM automation_runs 
        ORDER BY created_at DESC 
        LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_recent_runs(self, limit=10):
        """Récupère les dernières exécutions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM automation_runs 
        ORDER BY created_at DESC 
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def save_config(self, key, value):
        """Sauvegarde une valeur de configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO automation_config (key, value, updated_at)
        VALUES (?, ?, ?)
        ''', (key, value, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_config(self, key=None):
        """Récupère la configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if key:
            cursor.execute('SELECT value FROM automation_config WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            return row['value'] if row else None
        else:
            cursor.execute('SELECT key, value FROM automation_config')
            rows = cursor.fetchall()
            conn.close()
            return {row['key']: row['value'] for row in rows}
    
    def save_api_cache(self, json_data):
        """Sauvegarde le JSON des données API dans la DB pour préchargement"""
        self.save_config('latest_api_cache', json_data)
        
    def get_api_cache(self):
        """Récupère le JSON des données API depuis la DB"""
        return self.get_config('latest_api_cache')

    def delete_old_runs(self, days=90):
        """Supprime les anciennes exécutions (nettoyage)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        
        cursor.execute('''
        DELETE FROM automation_runs 
        WHERE created_at < datetime(?, 'unixepoch')
        ''', (cutoff_date,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted