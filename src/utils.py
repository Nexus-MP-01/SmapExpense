"""
Fonctions utilitaires pour l'application Recharge - Fusion CREG + Manuel
"""
import sys
import os

# --- CORRECTIF IMPORT ---
# Ajoute le dossier parent (racine du projet) au chemin Python pour trouver config.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# ------------------------

import json
import pandas as pd
import base64
import io
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
from config import Config


# ============================================================================
# CONSTANTES
# ============================================================================

MOIS_FR = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril', 5: 'Mai', 6: 'Juin',
    7: 'Juillet', 8: 'Août', 9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

MOIS_FR_ABBR = ['', 'Jan.', 'Fév.', 'Mars', 'Avr.', 'Mai', 'Juin', 
                'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']

MOIS_FR_LOWER = {
    1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril', 5: 'mai', 6: 'juin',
    7: 'juillet', 8: 'août', 9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
}

DAYS_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DAYS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']


# ============================================================================
# GESTION DES PRIX (MANUEL & CREG)
# ============================================================================

def load_creg_tariffs():
    """Charge les tarifs CREG depuis le fichier JSON avec gestion d'erreurs"""
    default_tariffs = {
        'tariffs': [
            {'quarter': 'Q1/2026', 'price': 35.23},
            {'quarter': 'Q4/2025', 'price': 34.57},
            {'quarter': 'Q3/2025', 'price': 38.43},
            {'quarter': 'Q2/2025', 'price': 36.18},
            {'quarter': 'Q1/2025', 'price': 32.56}
        ]
    }

    try:
        with open(Config.CREG_TARIFFS_JSON_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                save_creg_tariffs(default_tariffs)
                return default_tariffs
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Fichier tarifs CREG corrompu ou absent, réinitialisation...")
        save_creg_tariffs(default_tariffs)
        return default_tariffs


def save_creg_tariffs(data):
    """Sauvegarde les tarifs CREG dans le fichier JSON"""
    Config.ensure_data_dir()
    with open(Config.CREG_TARIFFS_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_prices_from_json():
    """Charge les prix manuels depuis le fichier JSON"""
    try:
        with open(Config.PRICES_JSON_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'estimated_prices': {}, 'real_prices': {}}


def save_prices_to_json(data):
    """Sauvegarde les prix manuels dans le fichier JSON"""
    Config.ensure_data_dir()
    with open(Config.PRICES_JSON_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_current_quarter():
    """Retourne le trimestre actuel au format 'Q1/2025'"""
    now = datetime.now()
    month = now.month
    year = now.year
    if 1 <= month <= 3: quarter = 'Q1'
    elif 4 <= month <= 6: quarter = 'Q2'
    elif 7 <= month <= 9: quarter = 'Q3'
    else: quarter = 'Q4'
    return f"{quarter}/{year}"


def get_quarter_from_date(date):
    """Retourne le trimestre pour une date donnée"""
    if isinstance(date, str):
        date = pd.to_datetime(date)
    month = date.month
    year = date.year
    if 1 <= month <= 3: quarter = 'Q1'
    elif 4 <= month <= 6: quarter = 'Q2'
    elif 7 <= month <= 9: quarter = 'Q3'
    else: quarter = 'Q4'
    return f"{quarter}/{year}"


def get_tariff_for_date(date, region=None):
    """Récupère le tarif CREG pour une date donnée"""
    creg_data = load_creg_tariffs()
    quarter = get_quarter_from_date(date)
    for tariff in creg_data['tariffs']:
        if tariff['quarter'] == quarter:
            return tariff.get('price', 0) / 100
    return 0


def get_tariff_for_period(start_date, end_date, region=None):
    """Récupère le tarif CREG moyen pour une période"""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    if get_quarter_from_date(start) == get_quarter_from_date(end):
        return get_tariff_for_date(start)
    
    total_days = (end - start).days + 1
    weighted_sum = 0
    current = start
    while current <= end:
        tariff = get_tariff_for_date(current)
        weighted_sum += tariff
        current += timedelta(days=1)
    
    return weighted_sum / total_days if total_days > 0 else 0


def create_price_dict_from_lists(years, prices):
    """Crée un dictionnaire {année: prix} depuis deux listes"""
    return {years[i]: prices[i] for i in range(len(years))}


def parse_quarter(quarter_str):
    parts = quarter_str.split('/')
    return parts[0], int(parts[1])


def format_quarter(quarter, year):
    return f"{quarter}/{year}"


# ============================================================================
# UTILITAIRES DATES
# ============================================================================

def get_month_button_texts():
    now = datetime.now()
    current_month_text = f"{MOIS_FR_ABBR[now.month]} {now.year}"
    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1
    previous_month_text = f"{MOIS_FR_ABBR[prev_month]} {prev_year}"
    current_year_text = f"Année {now.year}"
    return previous_month_text, current_month_text, current_year_text


def calculate_end_date_12_months(start_date):
    start_dt = pd.to_datetime(start_date)
    end_dt = start_dt + relativedelta(months=12) - timedelta(days=1)
    return end_dt.date()


def calculate_end_of_month(start_date):
    start_dt = pd.to_datetime(start_date)
    last_day = calendar.monthrange(start_dt.year, start_dt.month)[1]
    end_dt = datetime(start_dt.year, start_dt.month, last_day).date()
    return end_dt


def is_full_month_period(start_date, end_date):
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    if start_dt.day != 1: return False
    if start_dt.month != end_dt.month or start_dt.year != end_dt.year: return False
    last_day_of_month = calendar.monthrange(start_dt.year, start_dt.month)[1]
    return end_dt.day == last_day_of_month


def is_12_months_period(start_date, end_date):
    """Vérifie si la période correspond à 12 mois"""
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    days_diff = (end_dt - start_dt).days + 1
    expected_end = start_dt + relativedelta(months=12) - timedelta(days=1)
    is_exact_12_months = (end_dt.date() == expected_end.date())
    is_year_duration = (365 <= days_diff <= 366)
    return is_exact_12_months or is_year_duration


def get_current_month_period():
    now = datetime.now()
    start = datetime(now.year, now.month, 1).date()
    next_month = now.month + 1 if now.month < 12 else 1
    next_year = now.year if now.month < 12 else now.year + 1
    end = (datetime(next_year, next_month, 1) - timedelta(days=1)).date()
    return start, end


def get_previous_month_period():
    now = datetime.now()
    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1
    start = datetime(prev_year, prev_month, 1).date()
    last_day = calendar.monthrange(prev_year, prev_month)[1]
    end = datetime(prev_year, prev_month, last_day).date()
    return start, end


def get_current_year_period():
    now = datetime.now()
    start = datetime(now.year, 1, 1).date()
    end = datetime(now.year, 12, 31).date()
    return start, end


def get_years_from_period(start_date, end_date):
    """Extrait toutes les années concernées par une période"""
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    start_year = start_dt.year
    end_year = end_dt.year
    return list(range(start_year, end_year + 1))


# ============================================================================
# TRAITEMENT DES DONNÉES
# ============================================================================

def parse_csv_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        df['startTime'] = pd.to_datetime(df['De'])
        df['endTime'] = pd.to_datetime(df['À'])
        df['rfid'] = df['Nom de la borne de recharge']
        
        def parse_duration(duration_str):
            try:
                parts = duration_str.strip().split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours * 60 + minutes
            except:
                return 0
        
        df['durationMinutes'] = df['Durée [h:mm]'].apply(parse_duration)
        df['energyConsumed_kWh'] = df['kWh'].astype(str).str.replace(',', '.').astype(float)
        return df
    except Exception as e:
        print(f"Erreur lors du parsing: {e}")
        return None


def filter_dataframe(df, start_date, end_date, selected_vehicles):
    mask = (df['startTime'].dt.date >= pd.to_datetime(start_date).date()) & \
           (df['startTime'].dt.date <= pd.to_datetime(end_date).date()) & \
           (df['rfid'].isin(selected_vehicles))
    return df[mask].copy()


def add_cost_columns(df_filtered, price_dict, cost_column_name='cost'):
    """Ajoute les colonnes de prix et coût au DataFrame (Méthode Manuelle)"""
    df_filtered['year'] = df_filtered['startTime'].dt.year
    df_filtered['price'] = df_filtered['year'].map(price_dict)
    df_filtered[cost_column_name] = df_filtered['energyConsumed_kWh'] * df_filtered['price']
    return df_filtered


def add_cost_columns_creg(df_filtered, region=None):
    """Ajoute les colonnes de prix et coût (Méthode CREG)"""
    df_filtered['tariff_creg'] = df_filtered['startTime'].apply(
        lambda x: get_tariff_for_date(x)
    )
    df_filtered['cost'] = df_filtered['energyConsumed_kWh'] * df_filtered['tariff_creg']
    return df_filtered


def calculate_statistics(df_filtered):
    return {
        'total_consumption': df_filtered['energyConsumed_kWh'].sum(),
        'total_cost': df_filtered['cost'].sum(),
        'avg_session': df_filtered['energyConsumed_kWh'].mean(),
        'total_sessions': len(df_filtered)
    }


def prepare_weekly_data(df_filtered):
    df_filtered['week'] = df_filtered['startTime'].dt.to_period('W')
    weekly_data = df_filtered.groupby('week').agg({
        'cost': 'sum',
        'energyConsumed_kWh': 'sum'
    }).reset_index()
    weekly_data['week_date'] = weekly_data['week'].apply(lambda x: x.start_time)
    return weekly_data


def prepare_monthly_data(df_filtered):
    df_filtered['month'] = df_filtered['startTime'].dt.to_period('M')
    monthly_data = df_filtered.groupby('month').agg({
        'cost': 'sum',
        'energyConsumed_kWh': 'sum'
    }).reset_index()
    monthly_data['month_str'] = monthly_data['month'].astype(str)
    monthly_data['month_date'] = monthly_data['month'].apply(lambda x: x.to_timestamp())
    return monthly_data


def prepare_daily_consumption(df_filtered):
    df_filtered['day_of_week'] = df_filtered['startTime'].dt.day_name()
    weekly_consumption = df_filtered.groupby('day_of_week')['energyConsumed_kWh'].sum().reindex(DAYS_ORDER).reset_index()
    weekly_consumption['day_fr'] = DAYS_FR
    return weekly_consumption


def prepare_duration_distribution(df_filtered):
    df_filtered['durationHours'] = df_filtered['durationMinutes'] / 60
    df_filtered['durationHours_rounded'] = df_filtered['durationHours'].round()
    
    duration_counts = df_filtered.groupby('durationHours_rounded').size().reset_index(name='sessions')
    duration_counts = duration_counts.sort_values('durationHours_rounded')
    
    if len(duration_counts) > 0:
        min_duration = int(duration_counts['durationHours_rounded'].min())
        max_duration = int(duration_counts['durationHours_rounded'].max())
        
        all_hours = pd.DataFrame({'durationHours_rounded': range(min_duration, max_duration + 1)})
        duration_counts = all_hours.merge(duration_counts, on='durationHours_rounded', how='left').fillna(0)
    
    return duration_counts


def format_currency(amount):
    return f"{amount:.2f} €"


def format_kwh(kwh):
    return f"{kwh:.3f} kWh"