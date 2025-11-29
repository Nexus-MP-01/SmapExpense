# src/smappee_client.py
"""
Client pour l'API Smappee (Compatible v3)
Gère l'authentification OAuth2 et la récupération des sessions.
"""
import requests
import pandas as pd
from datetime import datetime
import time

class SmappeeClient:
    def __init__(self, client_id, client_secret):
        # URL de production standard pour l'API v3
        self.base_url = "https://app1pub.smappee.net/dev/v3"
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = 0
    
    def authenticate(self):
        """
        Authentification OAuth2 pour obtenir un access token.
        Utilise le flux 'client_credentials'.
        """
        token_url = f"{self.base_url}/oauth2/token"
        
        # Payload standard pour l'authentification API
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            print("🔑 Tentative d'authentification Smappee...")
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                # Calcul de l'expiration (buffer de 60s par sécurité)
                expires_in = token_data.get('expires_in', 3600)
                self.token_expiry = time.time() + expires_in - 60
                print("✅ Authentification Smappee réussie")
                return True
            else:
                print(f"❌ Erreur auth Smappee ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception lors de l'auth Smappee: {str(e)}")
            return False
    
    def _ensure_token(self):
        """Vérifie si le token est valide, sinon ré-authentifie"""
        if not self.access_token or time.time() > self.token_expiry:
            print("🔄 Renouvellement du token Smappee...")
            return self.authenticate()
        return True

    def get_charging_sessions(self, location_id, start_date_iso, end_date_iso):
        """
        Récupère les sessions de recharge pour une période.
        
        Args:
            location_id (str): ID de la service location
            start_date_iso (str): Date de début (ISO format YYYY-MM-DD)
            end_date_iso (str): Date de fin (ISO format YYYY-MM-DD)
        """
        if not self._ensure_token():
            return None

        # 1. Conversion des dates ISO en Timestamp Millisecondes (requis par Smappee)
        try:
            # On parse les dates (ex: "2024-01-01")
            dt_start = pd.to_datetime(start_date_iso)
            dt_end = pd.to_datetime(end_date_iso)
            
            # Conversion en millisecondes (Epoch * 1000)
            from_ts = int(dt_start.timestamp() * 1000)
            
            # Pour la fin, on force 23:59:59 si c'est une date simple pour couvrir toute la journée
            if "T" not in str(end_date_iso) and " " not in str(end_date_iso):
                 dt_end = dt_end.replace(hour=23, minute=59, second=59)
            to_ts = int(dt_end.timestamp() * 1000)
            
        except Exception as e:
            print(f"❌ Erreur de conversion des dates: {e}")
            return None

        # 2. Construction de la requête
        # Endpoint: /servicelocation/{id}/chargingsessions
        url = f"{self.base_url}/servicelocation/{location_id}/chargingsessions"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'from': from_ts,
            'to': to_ts
        }
        
        try:
            print(f"📡 Appel API Smappee (Location ID: {location_id})...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"📥 {len(data)} sessions brutes reçues.")
                return self.convert_to_dataframe(data)
            else:
                print(f"❌ Erreur API Smappee ({response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception lors de l'appel API: {str(e)}")
            return None
    
    def convert_to_dataframe(self, data):
        """
        Convertit les données JSON Smappee en DataFrame compatible avec l'application.
        NORMALISATION: Ajoute les colonnes 'startTime', 'endTime', 'rfid', 'energyConsumed_kWh'
        pour correspondre exactement à ce que parse_csv_contents produit.
        """
        if not data:
            return pd.DataFrame()

        formatted_data = []
        
        for session in data:
            try:
                # Smappee renvoie des timestamps en millisecondes
                start_ts = session.get('startTime')
                stop_ts = session.get('stopTime')
                
                if not start_ts or not stop_ts:
                    continue
                
                start_dt = datetime.fromtimestamp(start_ts / 1000)
                stop_dt = datetime.fromtimestamp(stop_ts / 1000)
                
                # Calcul de la durée format H:MM
                duration_seconds = (stop_dt - start_dt).total_seconds()
                hours, remainder = divmod(duration_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                duration_str = f"{int(hours):02}:{int(minutes):02}"
                
                # Récupération de l'énergie
                consumption = session.get('volume', 0) 
                
                # Nom de la borne / Connecteur
                station_name = session.get('chargingStationName', 'Borne Smappee')
                
                row = {
                    'Nom de la borne de recharge': station_name,
                    'De': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'À': stop_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'Durée [h:mm]': duration_str,
                    'kWh': consumption,
                    
                    # --- CHAMPS NORMALISÉS POUR L'APP ---
                    'startTime': start_dt,
                    'endTime': stop_dt,
                    'durationMinutes': (hours * 60) + minutes,
                    'energyConsumed_kWh': float(consumption),
                    'rfid': station_name # Smappee n'a pas toujours de RFID explicite, on utilise le nom de la borne par défaut
                }
                formatted_data.append(row)
                
            except Exception as e:
                print(f"⚠️ Erreur parsing session: {e}")
                continue
                
        df = pd.DataFrame(formatted_data)
        return df

    def test_connection(self):
        """Teste la connexion et l'authentification"""
        if self.authenticate():
            return True, "Authentification réussie"
        return False, "Échec de l'authentification (Vérifiez ID/Secret)"