"""
Layout principal de l'application Recharge
Simplifié : sans Falco, sans facture annuelle, avec tarifs CREG et Planificateur Interne
"""
import dash_bootstrap_components as dbc
from dash import html

from src.components import (
    create_header,
    create_upload_section,
    create_parameters_section,
    create_automation_dashboard,
    create_automation_config_modal_simple,
    create_monthly_modal,
    create_creg_modal,
    create_stores,
    create_downloads,
    create_intervals
)
from config import Config


def create_layout():
    """Crée le layout complet de l'application"""
    return dbc.Container([
        # En-tête
        create_header(),
        
        # Menu de navigation avec tabs
        dbc.Tabs([
            # ================================================================
            # TAB 1: Analyse Manuelle
            # ================================================================
            dbc.Tab(
                label="📊 Analyse Manuelle",
                tab_id="tab-manual",
                label_style={
                    'color': Config.DARK_GREY,
                    'fontWeight': 'bold',
                    'fontSize': '16px'
                },
                active_label_style={
                    'color': Config.SAGE_GREEN,
                    'fontWeight': 'bold',
                    'fontSize': '16px'
                },
                children=[
                    html.Div([
                        # Section Upload
                        create_upload_section(),
                        
                        # Section Paramètres (dates, véhicules)
                        create_parameters_section(),
                        
                        # Container pour les graphiques (sera rempli dynamiquement)
                        html.Div(id='graphs-container'),
                    ], style={'padding': '20px 0'})
                ]
            ),
            
            # ================================================================
            # TAB 2: Automatisation
            # ================================================================
            dbc.Tab(
                label="🤖 Automatisation",
                tab_id="tab-automation",
                label_style={
                    'color': Config.DARK_GREY,
                    'fontWeight': 'bold',
                    'fontSize': '16px'
                },
                active_label_style={
                    'color': Config.SAGE_GREEN,
                    'fontWeight': 'bold',
                    'fontSize': '16px'
                },
                children=[
                    html.Div([
                        # Bannière informative
                        dbc.Alert([
                            html.H4("🎯 Flux d'automatisation mensuelle", className="alert-heading"),
                            html.P([
                                "L'application gère automatiquement l'envoi des notes de frais selon la planification définie :"
                            ]),
                            html.Ol([
                                html.Li([
                                    html.Strong("Récupération des données Smappee"),
                                    " - Les sessions de recharge du mois sont récupérées automatiquement"
                                ]),
                                html.Li([
                                    html.Strong("Génération du PDF"),
                                    " - La note de frais est générée avec les tarifs CREG du trimestre en cours"
                                ]),
                                html.Li([
                                    html.Strong("Envoi par email"),
                                    " - Le PDF est envoyé automatiquement au destinataire configuré"
                                ])
                            ]),
                            html.Hr(),
                            html.P([
                                "💡 ",
                                html.Strong("Astuce:"),
                                " Configurez d'abord vos API (Smappee et Email) via le bouton 'Configuration', puis testez manuellement avant d'activer la planification automatique."
                            ], className="mb-0")
                        ], style={"backgroundColor": "rgba(152, 192, 163, 0.2)", "borderColor": Config.SAGE_GREEN, "color": "#2c3e50"}, className="mb-4"),
                        
                        # Dashboard de monitoring
                        create_automation_dashboard(),
                        
                        # Note: La section d'aide n8n a été supprimée car le scheduler est maintenant interne.
                        
                    ], style={'padding': '20px 0'})
                ]
            ),
        ], id="main-tabs", active_tab="tab-manual", className="mb-4", style={
            'borderBottom': f'3px solid {Config.SAGE_GREEN}'
        }),
        
        # ================================================================
        # STORES pour la persistance des données
        # ================================================================
        *create_stores(),
        
        # ================================================================
        # COMPOSANTS d'intervalle pour rafraîchissement
        # ================================================================
        *create_intervals(),
        
        # ================================================================
        # MODALES
        # ================================================================
        create_monthly_modal(),  # Modale pour note de frais mensuelle
        create_creg_modal(),    # Modale pour gestion des tarifs CREG
        create_automation_config_modal_simple(),  # Modale config
        
        # ================================================================
        # DOWNLOADS
        # ================================================================
        *create_downloads()
        
    ], fluid=True, style={
        'backgroundColor': Config.LIGHT_GREY,
        'minHeight': '100vh',
        'padding': '20px'
    })