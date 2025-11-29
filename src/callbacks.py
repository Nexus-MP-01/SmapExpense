"""
Callbacks de l'application Recharge
Fusion: Logiciel actuel (Auto/CREG) + Ancien Dashboard (Graphs/Manuel)
"""
import sys
import os

# --- CORRECTIF IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# ------------------------

import pandas as pd
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import Input, Output, State, callback_context, ALL, no_update, html, dcc, dash_table
from datetime import datetime, timedelta

from config import Config
from src.utils import (
    parse_csv_contents,
    get_month_button_texts,
    calculate_end_date_12_months,
    calculate_end_of_month,
    get_current_month_period,
    get_previous_month_period,
    get_current_year_period,
    load_creg_tariffs,
    save_creg_tariffs,
    # Imports pour les calculs de graphs
    filter_dataframe,
    add_cost_columns_creg,
    calculate_statistics,
    prepare_weekly_data,
    prepare_monthly_data,
    prepare_daily_consumption,
    prepare_duration_distribution
)

# Imports pour l'UI dynamique
from src.components import create_stats_cards, create_pdf_buttons
from src.pdf_generator import generate_monthly_pdf_data
from src.database import AutomationDB
from src.smappee_client import SmappeeClient

def register_callbacks(app):
    """Enregistre tous les callbacks de l'application"""
    
    # ========================================================================
    # 1. GESTION CENTRALISÉE DES DONNÉES (CSV & API & CACHE)
    # ========================================================================
    
    @app.callback(
        [Output('stored-data', 'data'),
         Output('upload-status', 'children'),
         Output('start-date', 'date'),
         Output('end-date', 'date'),
         Output('start-date', 'min_date_allowed'),
         Output('start-date', 'max_date_allowed'),
         Output('end-date', 'min_date_allowed'),
         Output('end-date', 'max_date_allowed'),
         Output('vehicle-selection', 'options'),
         Output('vehicle-selection', 'value'),
         Output('default-dates', 'data'),
         Output('data-source-indicator', 'children')],
        [Input('upload-data', 'contents'),
         Input('refresh-smappee-data-btn', 'n_clicks')],
        [State('upload-data', 'filename'),
         State('stored-data', 'data')],
    )
    def manage_data_source(contents, refresh_clicks, filename, current_stored_data):
        """
        Master Callback: Gère le chargement des données.
        Priorité:
        1. Upload CSV (action explicite)
        2. Bouton Refresh API (action explicite)
        3. Chargement initial (Cache API si dispo)
        """
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'initial_load'
        
        df = None
        source_label = ""
        # On n'utilise plus msg pour le succès, seulement pour les erreurs
        error_msg = None
        
        # --- CAS 1: UPLOAD CSV ---
        if trigger_id == 'upload-data' and contents:
            df = parse_csv_contents(contents, filename)
            if df is not None:
                source_label = f"Fichier: {filename}"
                # Pas de message de succès, le badge suffit
            else:
                return (no_update, dbc.Alert("❌ Erreur lecture CSV", color="danger"), 
                        no_update, no_update, no_update, no_update, no_update, no_update, 
                        no_update, no_update, no_update, no_update)

        # --- CAS 2: REFRESH API ---
        elif trigger_id == 'refresh-smappee-data-btn':
            db = AutomationDB()
            config = db.get_config()
            client_id = config.get('smappee_client_id')
            client_secret = config.get('smappee_client_secret')
            location_id = config.get('smappee_location_id')
            
            if not all([client_id, client_secret, location_id]):
                return (no_update, dbc.Alert("⚠️ Configurez l'API Smappee d'abord", color="warning"),
                        no_update, no_update, no_update, no_update, no_update, no_update, 
                        no_update, no_update, no_update, no_update)
            
            # Récupérer données (monitoring depuis le début de l'année)
            now = datetime.now()
            start_monitor = datetime(now.year, 1, 1)
            client = SmappeeClient(client_id, client_secret)
            
            if client.authenticate():
                df = client.get_charging_sessions(location_id, start_monitor.isoformat(), now.isoformat())
                if df is not None and not df.empty:
                    # Sauvegarder dans le cache DB
                    json_data = df.to_json(date_format='iso')
                    db.save_api_cache(json_data)
                    source_label = "Smappee API (En direct)"
                else:
                    return (no_update, dbc.Alert("Aucune donnée trouvée ou erreur API", color="warning"),
                            no_update, no_update, no_update, no_update, no_update, no_update, 
                            no_update, no_update, no_update, no_update)
            else:
                return (no_update, dbc.Alert("❌ Erreur authentification Smappee", color="danger"),
                        no_update, no_update, no_update, no_update, no_update, no_update, 
                        no_update, no_update, no_update, no_update)

        # --- CAS 3: INITIAL LOAD (CACHE) ---
        elif trigger_id == 'initial_load':
            # Si on a déjà des données (rechargement de page partiel), on ne fait rien
            if current_stored_data: 
                return (no_update, no_update, no_update, no_update, no_update, no_update, 
                        no_update, no_update, no_update, no_update, no_update, no_update)
            
            # Sinon on cherche le cache
            db = AutomationDB()
            cached_json = db.get_api_cache()
            if cached_json:
                try:
                    df = pd.read_json(cached_json)
                    # Re-conversion des dates car read_json peut parfois perdre le type
                    if 'startTime' in df.columns:
                        df['startTime'] = pd.to_datetime(df['startTime'])
                        df['endTime'] = pd.to_datetime(df['endTime'])
                    source_label = "Smappee API (Cache)"
                except:
                    pass # Cache corrompu ou vide

        # --- TRAITEMENT COMMUN DU DATAFRAME ---
        if df is None:
             return (None, "", None, None, None, None, None, None, [], [], {'min': None, 'max': None}, "")

        # Calcul des dates min/max globales des données
        min_date = df['startTime'].min().date()
        max_date = df['endTime'].max().date()
        
        # Par défaut, on affiche tout
        default_start = min_date
        default_end = max_date
        
        vehicles = sorted(df['rfid'].astype(str).unique())
        vehicle_options = [{'label': f'🚗 {v}', 'value': v} for v in vehicles]
        
        status_content = ""
        
        default_dates = {'min': min_date.isoformat(), 'max': max_date.isoformat()}
        
        # Création du badge indicateur avec la couleur Vert Sauge
        indicator = dbc.Badge(
            source_label, 
            className="ms-2", 
            style={
                "fontSize": "1em",
                "backgroundColor": Config.SAGE_GREEN,  # Utilisation de la couleur personnalisée
                "color": "white"
            }
        )
        
        return (df.to_json(date_format='iso'), status_content, default_start, default_end,
                min_date, max_date, min_date, max_date, vehicle_options, vehicles, default_dates, indicator)
    
    
    # ========================================================================
    # 2. GESTION DES DATES - Sélection rapide
    # ========================================================================
    
    @app.callback(
        [Output('start-date', 'date', allow_duplicate=True),
         Output('end-date', 'date', allow_duplicate=True),
         Output('select-previous-month-btn', 'children'),
         Output('select-current-month-btn', 'children'),
         Output('select-current-year-btn', 'children')],
        [Input('select-current-month-btn', 'n_clicks'),
         Input('select-current-year-btn', 'n_clicks'),
         Input('select-previous-month-btn', 'n_clicks'),
         Input('select-default-dates-btn', 'n_clicks')],
        [State('default-dates', 'data')],
        prevent_initial_call=True
    )
    def select_period(month_clicks, year_clicks, prev_month_clicks, default_clicks, default_dates):
        """Sélectionne automatiquement le mois ou l'année"""
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        prev_text, curr_text, year_text = get_month_button_texts()
        
        if button_id == 'select-current-month-btn':
            start, end = get_current_month_period()
            return start, end, prev_text, curr_text, year_text
        
        elif button_id == 'select-previous-month-btn':
            start, end = get_previous_month_period()
            return start, end, prev_text, curr_text, year_text
            
        elif button_id == 'select-current-year-btn':
            start, end = get_current_year_period()
            return start, end, prev_text, curr_text, year_text
        
        elif button_id == 'select-default-dates-btn':
            if default_dates and default_dates.get('min') and default_dates.get('max'):
                start = pd.to_datetime(default_dates['min']).date()
                end = pd.to_datetime(default_dates['max']).date()
                return start, end, prev_text, curr_text, year_text
        
        return no_update, no_update, prev_text, curr_text, year_text

    # Callback pour la flèche dans les paramètres (calcul 12 mois)
    @app.callback(
        Output('end-date', 'date', allow_duplicate=True),
        Input('params-calculate-end-date-btn', 'n_clicks'),
        State('start-date', 'date'),
        prevent_initial_call=True
    )
    def params_calculate_end_date(n_clicks, start_date):
        """Calcule automatiquement 12 mois après la date de début"""
        if n_clicks and start_date:
            return calculate_end_date_12_months(start_date)
        return no_update

    # Callback pour la flèche dans la modale mensuelle
    @app.callback(
        Output('modal-monthly-end-date', 'date', allow_duplicate=True),
        Input('calculate-monthly-end-date-btn', 'n_clicks'),
        State('modal-monthly-start-date', 'date'),
        prevent_initial_call=True
    )
    def calculate_monthly_end_date_modal(n_clicks, start_date):
        """Calcule le dernier jour du mois"""
        if n_clicks and start_date:
            return calculate_end_of_month(start_date)
        return no_update


    # ========================================================================
    # 3. GÉNÉRATION DES GRAPHIQUES (AVEC TARIFS CREG)
    # ========================================================================
    
    @app.callback(
        Output('graphs-container', 'children'),
        [Input('stored-data', 'data'),
         Input('start-date', 'date'),
         Input('end-date', 'date'),
         Input('vehicle-selection', 'value')]
    )
    def update_graphs(json_data, start_date, end_date, selected_vehicles):
        """Met à jour les graphiques et statistiques"""
        
        if json_data is None or start_date is None or end_date is None or not selected_vehicles:
            return html.Div()
        
        df = pd.read_json(json_data)
        # Re-conversion des dates car read_json convertit en timestamp/string
        if 'startTime' in df.columns:
            df['startTime'] = pd.to_datetime(df['startTime'])
        if 'endTime' in df.columns:
            df['endTime'] = pd.to_datetime(df['endTime'])
        
        # 1. Filtrer
        df_filtered = filter_dataframe(df, start_date, end_date, selected_vehicles)
        
        if len(df_filtered) == 0:
            return dbc.Alert("Aucune donnée pour la période et les véhicules sélectionnés", color="warning")
        
        # 2. Calculer les coûts (AVEC CREG)
        # On utilise add_cost_columns_creg qui récupère les prix automatiquement
        df_filtered = add_cost_columns_creg(df_filtered)
        
        # 3. Préparer les données
        stats = calculate_statistics(df_filtered)
        weekly_data = prepare_weekly_data(df_filtered)
        monthly_data = prepare_monthly_data(df_filtered)
        daily_consumption = prepare_daily_consumption(df_filtered)
        duration_dist = prepare_duration_distribution(df_filtered)
        
        # 4. Créer les figures Plotly
        
        # Graphique 1: Combiné Semaine/Mois
        fig_combined = go.Figure()
        
        fig_combined.add_trace(go.Scatter(
            x=weekly_data['week_date'],
            y=weekly_data['cost'],
            mode='markers',
            name='Coût hebdomadaire',
            marker=dict(size=8, color=Config.SAGE_GREEN, opacity=0.7),
            customdata=weekly_data['energyConsumed_kWh'],
            hovertemplate='<b>Semaine:</b> %{x|%Y-%m-%d}<br><b>Coût:</b> %{y:.2f} €<br><b>Consommation:</b> %{customdata:.2f} kWh<extra></extra>'
        ))
        
        fig_combined.add_trace(go.Scatter(
            x=monthly_data['month_date'],
            y=monthly_data['cost'],
            mode='lines+markers',
            name='Tendance mensuelle',
            line=dict(color=Config.SAGE_GREEN, width=3),
            marker=dict(size=10, color=Config.SAGE_GREEN),
            customdata=monthly_data['energyConsumed_kWh'],
            hovertemplate='<b>Mois:</b> %{x|%Y-%m}<br><b>Coût:</b> %{y:.2f} €<br><b>Consommation:</b> %{customdata:.2f} kWh<extra></extra>'
        ))
        
        fig_combined.update_layout(
            title='Évolution des Coûts de Recharge (Tarifs CREG)',
            xaxis_title='Date',
            yaxis_title='Coût (€)',
            hovermode='closest',
            height=500,
            template='plotly_white',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Graphique 2: Jours de la semaine
        fig_weekly = go.Figure()
        fig_weekly.add_trace(go.Bar(
            x=daily_consumption['day_fr'],
            y=daily_consumption['energyConsumed_kWh'],
            marker=dict(color=Config.SAGE_GREEN),
            text=daily_consumption['energyConsumed_kWh'].round(1),
            textposition='auto'
        ))
        fig_weekly.update_layout(
            title='Consommation par Jour de la Semaine',
            xaxis_title='Jour',
            yaxis_title='Consommation Totale (kWh)',
            height=400,
            template='plotly_white'
        )
        
        # Graphique 3: Distribution Durée
        fig_duration = go.Figure()
        fig_duration.add_trace(go.Scatter(
            x=duration_dist['durationHours_rounded'],
            y=duration_dist['sessions'],
            mode='lines+markers',
            line=dict(color=Config.SAGE_GREEN, width=3),
            marker=dict(size=8, color=Config.SAGE_GREEN),
            fill='tozeroy',
            fillcolor='rgba(152, 192, 163, 0.3)',
            name='Sessions',
            hovertemplate='<b>Durée:</b> %{x}h<br><b>Nombre de sessions:</b> %{y}<extra></extra>'
        ))
        
        fig_duration.update_layout(
            title='Distribution du Temps de Recharge',
            xaxis_title='Durée de recharge (heures)',
            yaxis_title='Nombre de sessions',
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        # 5. Assembler le layout
        graphs = html.Div([
            # Cartes de stats
            create_stats_cards(
                stats['total_consumption'],
                stats['total_cost'],
                stats['avg_session'],
                stats['total_sessions']
            ),
            # Boutons actions
            create_pdf_buttons(),
            # Graphs
            dbc.Row([
                dbc.Col([dcc.Graph(figure=fig_combined)], width=12)
            ], className="mb-4"),
            dbc.Row([
                dbc.Col([dcc.Graph(figure=fig_weekly)], width=6),
                dbc.Col([dcc.Graph(figure=fig_duration)], width=6)
            ], className="mb-4")
        ])
        
        return graphs


    # ========================================================================
    # 4. GESTION TARIFS CREG
    # ========================================================================
    
    @app.callback(
        Output('creg-modal', 'is_open'),
        [Input('open-creg-modal-btn', 'n_clicks'),
         Input('close-creg-modal', 'n_clicks')],
        State('creg-modal', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_creg_modal(open_clicks, close_clicks, is_open):
        """Ouvre/ferme la modale CREG"""
        if open_clicks or close_clicks:
            return not is_open
        return is_open
    
    @app.callback(
        Output('creg-tariffs-table', 'children'),
        [Input('refresh-creg-table-btn', 'n_clicks'),
         Input('creg-modal', 'is_open')]
    )
    def display_creg_tariffs(n_clicks, is_open):
        """Affiche le tableau des tarifs CREG"""
        creg_data = load_creg_tariffs()
        tariffs = creg_data.get('tariffs', [])
        
        if not tariffs:
            return dbc.Alert("Aucun tarif CREG configuré", color="warning")
        
        columns = [
            {'name': 'Trimestre', 'id': 'quarter', 'type': 'text', 'editable': True},
            {'name': 'Tarif (ct€/kWh)', 'id': 'price', 'type': 'numeric', 'editable': True}
        ]
        
        table = dash_table.DataTable(
            id='creg-tariffs-datatable',
            columns=columns,
            data=tariffs,
            editable=True,
            row_deletable=True,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'sans-serif'},
            style_header={'backgroundColor': Config.DARK_GREY, 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}]
        )
        return table

    @app.callback(
        Output('creg-save-status', 'children'),
        Input('creg-tariffs-datatable', 'data'),
        prevent_initial_call=True
    )
    def save_creg_table_changes(rows):
        """Sauvegarde auto CREG"""
        if rows is None: return no_update
        creg_data = load_creg_tariffs()
        creg_data['tariffs'] = rows
        save_creg_tariffs(creg_data)
        return html.Div("✅ Modifications enregistrées", className="text-success mt-2", style={'fontSize': '0.9em'})

    @app.callback(
        [Output('creg-tariffs-table', 'children', allow_duplicate=True),
         Output('new-quarter-input', 'value'),
         Output('new-price-input', 'value')],
        Input('add-tariff-btn', 'n_clicks'),
        [State('new-quarter-input', 'value'),
         State('new-price-input', 'value')],
        prevent_initial_call=True
    )
    def add_creg_tariff(n_clicks, quarter, price):
        """Ajoute un tarif CREG"""
        if not n_clicks or not quarter or not price: return no_update, no_update, no_update
        creg_data = load_creg_tariffs()
        tariffs = creg_data.get('tariffs', [])
        tariffs.insert(0, {'quarter': quarter, 'price': float(price)})
        creg_data['tariffs'] = tariffs
        save_creg_tariffs(creg_data)
        return display_creg_tariffs(0, True), "", ""
    
    
    # ========================================================================
    # 5. AUTOMATISATION & CONFIGURATION
    # ========================================================================
    
    @app.callback(
        [Output('automation-current-status', 'children'),
         Output('automation-next-run', 'children'),
         Output('automation-config-summary', 'children'),
         Output('automation-history-table', 'children')],
        [Input('refresh-status-btn', 'n_clicks'),
         Input('automation-refresh-interval', 'n_intervals'),
         Input('main-tabs', 'active_tab')]
    )
    def update_automation_dashboard(n_clicks, n_intervals, active_tab):
        """Met à jour le dashboard d'automatisation"""
        from src.database import AutomationDB
        from src.components import create_automation_history_table, create_status_badge
        import calendar
        
        if active_tab != 'tab-automation':
            return no_update, no_update, no_update, no_update
        
        db = AutomationDB()
        latest = db.get_latest_run()
        
        if latest:
            status_badge = create_status_badge(latest['status'])
            try: run_date = datetime.fromisoformat(latest['run_date']).strftime('%d/%m/%Y %H:%M')
            except: run_date = latest['run_date']
            status = html.Div([
                status_badge,
                html.P(f"Dernière exécution : {run_date}", className="mb-1"),
                html.P(f"Étape : {latest['step']}", className="text-muted mb-0", style={'fontSize': '0.9em'})
            ])
        else:
            status = dbc.Alert("Aucune exécution enregistrée", style={"backgroundColor": "rgba(152, 192, 163, 0.2)", "borderColor": Config.SAGE_GREEN, "color": "#2c3e50"}, className="mb-0")
        
        # --- LECTURE CONFIG POUR AFFICHAGE ---
        # On lit la DB, avec fallback sur les variables d'env (Config)
        db_config = db.get_config()
        def get_conf(key, default):
            return db_config.get(key) if db_config and db_config.get(key) else default

        # 1. Email destinataire
        email_target = get_conf('notification_email', Config.NOTIFICATION_EMAIL)
        
        # 2. Smappee Status (On masque le secret)
        smappee_id = get_conf('smappee_client_id', Config.SMAPPEE_CLIENT_ID)
        if smappee_id and len(str(smappee_id)) > 4:
            smappee_display = f"✅ Configuré (...{str(smappee_id)[-4:]})"
        elif smappee_id:
            smappee_display = "✅ Configuré"
        else:
            smappee_display = "❌ Non configuré"

        # 3. SMTP Status
        smtp_server = get_conf('smtp_server', Config.SMTP_SERVER)
        smtp_display = f"✅ {smtp_server}" if smtp_server else "❌ Non configuré"

        # Création du résumé visuel
        config_summary = html.Div([
            html.P([
                html.I(className="fas fa-envelope me-2", style={'color': Config.SAGE_GREEN}),
                html.Strong("Destinataire : "), 
                html.Span(email_target, style={'fontFamily': 'monospace', 'backgroundColor': '#f0f0f0', 'padding': '2px 5px', 'borderRadius': '4px'})
            ], className="mb-2"),
            html.P([
                html.I(className="fas fa-plug me-2", style={'color': Config.SAGE_GREEN}),
                html.Strong("Smappee : "), 
                html.Span(smappee_display)
            ], className="mb-2"),
            html.P([
                html.I(className="fas fa-server me-2", style={'color': Config.SAGE_GREEN}),
                html.Strong("SMTP : "), 
                html.Span(smtp_display)
            ], className="mb-0"),
        ], style={'backgroundColor': 'white', 'padding': '10px', 'borderRadius': '8px', 'border': '1px solid #eee'})

        # Calcul de la prochaine exécution
        schedule_time = get_conf('schedule_time', '23:59')
        schedule_mode = get_conf('schedule_mode', 'last_day')
        mode_display = "Dernier jour du mois" if schedule_mode == 'last_day' else "1er jour du mois suivant"
        
        next_run_text = html.Div([
            html.P(f"Planifié : {mode_display} à {schedule_time}", className="mb-1", style={'fontWeight': 'bold'}),
            html.P("(Planificateur interne)", className="text-muted mb-0", style={'fontSize': '0.85em'})
        ])
        
        runs = db.get_recent_runs(limit=10)
        history = create_automation_history_table(runs)
        
        return status, next_run_text, config_summary, history

    @app.callback(
        [Output('automation-config-modal', 'is_open'),
         Output('schedule-mode-input', 'value'),
         Output('schedule-time-input', 'value'),
         Output('notification-email-input', 'value'),
         Output('smappee-client-id-input', 'value'),
         Output('smappee-client-secret-input', 'value'),
         Output('smappee-location-id-input', 'value'),
         Output('smtp-server-input', 'value'),
         Output('smtp-port-input', 'value'),
         Output('smtp-user-input', 'value'),
         Output('smtp-password-input', 'value')],
        
        [Input('open-config-modal-btn', 'n_clicks'),
         Input('close-config-modal', 'n_clicks'),
         Input('save-config-btn', 'n_clicks')],
        
        [State('automation-config-modal', 'is_open'),
         State('schedule-mode-input', 'value'),
         State('schedule-time-input', 'value'),
         State('notification-email-input', 'value'),
         State('smappee-client-id-input', 'value'),
         State('smappee-client-secret-input', 'value'),
         State('smappee-location-id-input', 'value'),
         State('smtp-server-input', 'value'),
         State('smtp-port-input', 'value'),
         State('smtp-user-input', 'value'),
         State('smtp-password-input', 'value')]
    )
    def toggle_config_modal(open_clicks, close_clicks, save_clicks, is_open,
                           sched_mode, sched_time, notif_email,
                           smappee_id, smappee_secret, smappee_location,
                           smtp_server, smtp_port, smtp_user, smtp_pass):
        """Ouvre/ferme la modale config et sauvegarde les données"""
        from src.database import AutomationDB
        from src.scheduler_manager import SchedulerManager
        from config import Config
        
        ctx = callback_context
        if not ctx.triggered:
            return (is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        db = AutomationDB()
        
        if button_id == 'open-config-modal-btn':
            config = db.get_config()
            return (
                True,
                config.get('schedule_mode', 'last_day'),
                config.get('schedule_time', '23:59'),
                config.get('notification_email', Config.NOTIFICATION_EMAIL),
                config.get('smappee_client_id', ''),
                config.get('smappee_client_secret', ''),
                config.get('smappee_location_id', ''),
                config.get('smtp_server', ''),
                config.get('smtp_port', 587),
                config.get('smtp_user', ''),
                config.get('smtp_password', '')
            )
            
        elif button_id == 'close-config-modal':
            return (False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)
            
        elif button_id == 'save-config-btn':
            if sched_mode: db.save_config('schedule_mode', sched_mode)
            if sched_time: db.save_config('schedule_time', sched_time)
            if notif_email: db.save_config('notification_email', notif_email)
            
            if smappee_id: db.save_config('smappee_client_id', smappee_id)
            if smappee_secret: db.save_config('smappee_client_secret', smappee_secret)
            if smappee_location: db.save_config('smappee_location_id', smappee_location)
            if smtp_server: db.save_config('smtp_server', smtp_server)
            if smtp_port: db.save_config('smtp_port', str(smtp_port))
            if smtp_user: db.save_config('smtp_user', smtp_user)
            if smtp_pass: db.save_config('smtp_password', smtp_pass)
            
            # Mise à jour du planificateur
            SchedulerManager.update_schedule()
            
            return (False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)
            
        return (is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)

    @app.callback(
        Output('smappee-test-result', 'children'),
        Input('test-smappee-btn', 'n_clicks'),
        [State('smappee-client-id-input', 'value'),
         State('smappee-client-secret-input', 'value')],
        prevent_initial_call=True
    )
    def test_smappee(n_clicks, client_id, client_secret):
        from src.smappee_client import SmappeeClient
        if not n_clicks or not client_id or not client_secret: return ""
        client = SmappeeClient(client_id, client_secret)
        success, message = client.test_connection()
        return dbc.Alert(message, color="success" if success else "danger", className="mb-0")

    @app.callback(
        Output('email-test-result', 'children'),
        Input('test-email-btn', 'n_clicks'),
        [State('smtp-server-input', 'value'),
         State('smtp-port-input', 'value'),
         State('smtp-user-input', 'value'),
         State('smtp-password-input', 'value'),
         State('notification-email-input', 'value')],
        prevent_initial_call=True
    )
    def test_email(n_clicks, smtp_server, smtp_port, smtp_user, smtp_pass, notif_email):
        from src.email_notifier import EmailNotifier
        from config import Config
        
        target_email = notif_email if notif_email else Config.NOTIFICATION_EMAIL
        
        if not n_clicks or not all([smtp_server, smtp_user, smtp_pass]): return ""
        notifier = EmailNotifier(smtp_server, int(smtp_port), smtp_user, smtp_pass)
        success, message = notifier.send_test_email(target_email)
        return dbc.Alert(f"✅ {message} (envoyé à {target_email})" if success else f"❌ {message}", color="success" if success else "danger", className="mb-0")

    @app.callback(
        Output('automation-history-table', 'children', allow_duplicate=True),
        Input('manual-trigger-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def manual_trigger_automation(n_clicks):
        from src.automation import run_monthly_automation
        from src.utils import get_previous_month_period
        from src.components import create_automation_history_table
        from src.database import AutomationDB
        import threading
        if not n_clicks: return no_update
        start, end = get_previous_month_period()
        thread = threading.Thread(target=run_monthly_automation, args=(start.isoformat(), end.isoformat(), True), daemon=True)
        thread.start()
        db = AutomationDB()
        runs = db.get_recent_runs(limit=10)
        return create_automation_history_table(runs)
    
    # Callback pour la modale mensuelle PDF (Verrouillé avec prevent_initial_call=True)
    @app.callback(
        [Output('modal-monthly-period', 'is_open'),
         Output('modal-monthly-start-date', 'date'),
         Output('modal-monthly-end-date', 'date'),
         Output('download-monthly-pdf', 'data', allow_duplicate=True)],
        [Input('export-monthly-btn', 'n_clicks'),
         Input('close-monthly-modal', 'n_clicks'),
         Input('confirm-monthly-pdf-btn', 'n_clicks')],
        [State('modal-monthly-start-date', 'date'),
         State('modal-monthly-end-date', 'date'),
         State('start-date', 'date'),
         State('end-date', 'date'),
         State('stored-data', 'data'),
         State('vehicle-selection', 'value'),
         State('modal-monthly-period', 'is_open')],
        prevent_initial_call=True
    )
    def handle_monthly_export(export_clicks, close_clicks, confirm_clicks, modal_start, modal_end, 
                             main_start, main_end, json_data, selected_vehicles, is_open):
        """Gère la modale mensuelle"""
        ctx = callback_context
        if not ctx.triggered: return no_update, no_update, no_update, no_update
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'export-monthly-btn' and export_clicks:
            # Ouvre la modale avec les dates sélectionnées
            return True, main_start, main_end, None
        
        elif button_id == 'close-monthly-modal':
            return False, no_update, no_update, None
            
        elif button_id == 'confirm-monthly-pdf-btn' and confirm_clicks:
            # Génère le PDF
            if json_data and modal_start and modal_end:
                # Appelle la génération PDF avec les tarifs CREG par défaut
                pdf_data = generate_monthly_pdf_data(json_data, modal_start, modal_end, selected_vehicles, region=None)
                return False, no_update, no_update, pdf_data
                
        return no_update, no_update, no_update, no_update