"""
Composants UI réutilisables pour l'application Recharge - VERSION NETTOYÉE
"""
import sys
import os

# --- CORRECTIF IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# ------------------------

import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from datetime import datetime
from config import Config
from src.utils import get_month_button_texts, MOIS_FR


# ============================================================================
# HEADER
# ============================================================================

def create_header():
    """Crée l'en-tête de l'application"""
    return dbc.Row([
        dbc.Col(html.H1(
            "SmapExpense",
            className="text-center mb-4 mt-4",
            style={'color': '#2c3e50'}
        ))
    ])


# ============================================================================
# SECTION UPLOAD & DATA SOURCE
# ============================================================================

def create_upload_section():
    """Crée la section d'upload de fichiers et de récupération API"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        # Zone 1: Titre et Indicateur de Source
                        dbc.Col([
                            html.H5("📂 Source de Données", className="card-title"),
                            html.Div(id="data-source-indicator", className="mb-2")
                        ], width=12),
                    ]),
                    
                    dbc.Row([
                        # Zone 2: Bouton API Smappee (gauche)
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-cloud-download-alt me-2"), "Récupérer données Smappee"],
                                id="refresh-smappee-data-btn",
                                color="primary",
                                outline=False,
                                className="w-100 h-100",
                                style={"fontWeight": "bold", "backgroundColor": Config.SAGE_GREEN, "borderColor": Config.SAGE_GREEN}
                            ),
                            dbc.Tooltip(
                                "Télécharge les données du mois en cours depuis l'API Smappee et met à jour le cache.",
                                target="refresh-smappee-data-btn",
                            ),
                        ], width=4),
                        
                        # Zone 3: Zone Upload (droite)
                        dbc.Col([
                            dcc.Upload(
                                id='upload-data',
                                children=html.Div([
                                    html.I(className="fas fa-file-csv me-2"),
                                    'Glissez un CSV ou ',
                                    html.A('cliquez ici')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'cursor': 'pointer',
                                    'backgroundColor': '#f8f9fa',
                                    'color': '#6c757d'
                                },
                                multiple=False
                            ),
                        ], width=8),
                    ], className="align-items-center mb-2"),
                    
                    # Zone 4: Status global
                    html.Div(id='upload-status', className="mt-2")
                ])
            ], className="mb-4")
        ])
    ])


# ============================================================================
# SECTION PARAMÈTRES
# ============================================================================

def create_date_selector():
    """Crée le sélecteur de dates"""
    now = datetime.now()
    prev_text, curr_text, year_text = get_month_button_texts()
    
    return html.Div([
        html.Div(
            f"🗓️ Nous sommes le {now.day} {MOIS_FR[now.month]} {now.year}",
            style={
                'fontSize': '16px',
                'fontWeight': 'bold',
                'color': '#2c3e50',
                'marginBottom': '15px'
            }
        ),
        dbc.Row([
            dbc.Col([
                html.Label("Date de début:", style={'fontWeight': 'bold', 'fontSize': '0.85em'}),
                dcc.DatePickerSingle(
                    id='start-date',
                    display_format='DD/MM/YYYY',
                    style={'width': '100%', 'fontSize': '0.85em'}
                ),
            ], width=5),
            dbc.Col([
                html.Div([
                    # Label invisible pour pousser la flèche au niveau des champs de saisie (et pas au niveau des titres)
                    html.Label("Spacer", style={'visibility': 'hidden', 'display': 'block', 'marginBottom': '8px'}),
                    
                    # Le bouton flèche
                    dbc.Button(
                        "➜",
                        id='params-calculate-end-date-btn',
                        size='sm',
                        className='sage-button',
                        style={
                            'fontSize': '16px', 
                            'padding': '4px 15px', 
                            'borderRadius': '4px'
                        },
                        title="Fin du mois"
                    )
                ], 
                className="d-flex flex-column align-items-center"
                )
            ], width=2),
            dbc.Col([
                html.Label("Date de fin:", style={'fontWeight': 'bold', 'fontSize': '0.85em'}),
                dcc.DatePickerSingle(
                    id='end-date',
                    display_format='DD/MM/YYYY',
                    style={'width': '100%', 'fontSize': '0.85em'}
                ),
            ], width=5)
        ], className="mb-2"),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    prev_text,
                    id='select-previous-month-btn',
                    size='sm',
                    className='mb-2 sage-button',
                    style={'width': '100%', 'fontSize': '0.85em'}
                ),
            ], width=6),
            dbc.Col([
                dbc.Button(
                    curr_text,
                    id='select-current-month-btn',
                    size='sm',
                    className='mb-2 sage-button',
                    style={'width': '100%', 'fontSize': '0.85em'}
                ),
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    year_text,
                    id='select-current-year-btn',
                    size='sm',
                    className='mb-2 sage-button',
                    style={'width': '100%', 'fontSize': '0.85em'}
                ),
            ], width=6),
            dbc.Col([
                dbc.Button(
                    "Défaut",
                    id='select-default-dates-btn',
                    size='sm',
                    className='mb-2 sage-button',
                    style={'width': '100%', 'fontSize': '0.85em'}
                ),
            ], width=6)
        ])
    ])


def create_vehicle_selector():
    """Crée le sélecteur de véhicules"""
    return html.Div([
        html.Label("Véhicules détectés:", style={'fontWeight': 'bold'}),
        dcc.Checklist(
            id='vehicle-selection',
            options=[],
            value=[],
            labelStyle={'display': 'block', 'margin': '5px 0'},
            style={'maxHeight': '150px', 'overflowY': 'auto'}
        )
    ])


def create_parameters_section():
    """Crée la section des paramètres (simplifiée sans les prix)"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("⚙️ Paramètres", className="card-title"),
                    dbc.Row([
                        dbc.Col(create_date_selector(), width=6),
                        dbc.Col(create_vehicle_selector(), width=6),
                    ]),
                    html.Hr(),
                    dbc.Button(
                        [html.I(className="fas fa-table me-2"), "Gérer les tarifs CREG"],
                        id='open-creg-modal-btn',
                        className='sage-button',
                        style={'width': '100%'}
                    )
                ])
            ], className="mb-4")
        ])
    ])


# ============================================================================
# CARTES DE STATISTIQUES
# ============================================================================

def create_stats_cards(total_consumption, total_cost, avg_session, total_sessions):
    """Crée les cartes de statistiques"""
    sage_green = Config.SAGE_GREEN
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{total_consumption:.2f} kWh", style={'color': sage_green}),
                    html.P("Consommation Totale", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{total_cost:.2f} €", style={'color': sage_green}),
                    html.P("Coût Total (CREG)", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{avg_session:.2f} kWh", style={'color': sage_green}),
                    html.P("Moyenne par Session", className="text-muted")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{total_sessions}", style={'color': sage_green}),
                    html.P("Sessions Totales", className="text-muted")
                ])
            ])
        ], width=3)
    ], className="mb-4")


# ============================================================================
# BOUTONS PDF
# ============================================================================

def create_pdf_buttons():
    """Crée le bouton d'export PDF"""
    return dbc.Row([
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-file-pdf me-2"), "Générer Note de Frais Mensuelle"],
                id='export-monthly-btn',
                size='lg',
                className='mb-3 sage-button'
            )
        ], className="text-center")
    ])


# ============================================================================
# MODALE MENSUELLE
# ============================================================================

def create_monthly_modal():
    """Crée la modale pour la note de frais mensuelle"""
    prev_text, curr_text, _ = get_month_button_texts()
    
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("📅 Sélection de la période mensuelle")),
        dbc.ModalBody([
            html.Div(id='monthly-period-warning'),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.Label("Date de début:", style={'fontWeight': 'bold'}),
                    dcc.DatePickerSingle(
                        id='modal-monthly-start-date',
                        display_format='DD/MM/YYYY',
                        style={'width': '100%'}
                    ),
                ], width=5),
                dbc.Col([
                    html.Div([
                        html.Label(" ", style={
                            'fontWeight': 'bold',
                            'display': 'block',
                            'visibility': 'hidden'
                        }),
                        dbc.Button(
                            "➜",
                            id='calculate-monthly-end-date-btn',
                            size='sm',
                            className='sage-button',
                            style={'width': '100%', 'fontSize': '24px', 'padding': '8px'},
                            title="Calculer automatiquement la fin du mois"
                        )
                    ], style={
                        'display': 'flex',
                        'flexDirection': 'column',
                        'justifyContent': 'center',
                        'alignItems': 'center',
                        'height': '100%'
                    })
                ], width=2),
                dbc.Col([
                    html.Label("Date de fin:", style={'fontWeight': 'bold'}),
                    dcc.DatePickerSingle(
                        id='modal-monthly-end-date',
                        display_format='DD/MM/YYYY',
                        style={'width': '100%'}
                    ),
                ], width=5)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        curr_text,
                        id='select-current-month-modal-btn',
                        size='sm',
                        className='sage-button',
                        style={'width': '100%'}
                    ),
                ], width=4),
                dbc.Col([
                    dbc.Button(
                        prev_text,
                        id='select-previous-month-modal-btn',
                        size='sm',
                        className='sage-button',
                        style={'width': '100%'}
                    ),
                ], width=4),
                dbc.Col([
                    dbc.Button(
                        "Défaut",
                        id='select-default-dates-monthly-modal-btn',
                        size='sm',
                        className='sage-button',
                        style={'width': '100%'}
                    ),
                ], width=4)
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Annuler", id="close-monthly-modal", className="me-2", color="secondary"),
            dbc.Button("Générer la note de frais", id="confirm-monthly-pdf-btn", className="sage-button")
        ])
    ], id="modal-monthly-period", size="lg", is_open=False)


# ============================================================================
# MODALE GESTION TARIFS CREG
# ============================================================================

def create_creg_modal():
    """Crée la modale de gestion des tarifs CREG"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("📊 Gestion des Tarifs CREG")),
        dbc.ModalBody([
            html.P([
                "Les tarifs CREG (Commission de Régulation de l'Électricité et du Gaz) sont utilisés ",
                "par le SPF Finances pour le calcul du remboursement des frais d'électricité."
            ]),
            html.Hr(),
            # Bouton de rafraîchissement
            dbc.Row([
                dbc.Col(html.H5("Tableau des tarifs (Éditable)"), width=8),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="fas fa-sync-alt me-2"), "Actualiser"], 
                        id="refresh-creg-table-btn", 
                        size="sm", 
                        outline=True, 
                        color="primary",
                        className="w-100"
                    ), 
                    width=4
                )
            ], className="mb-2 align-items-center"),
            
            html.Div(id='creg-tariffs-table'),
            html.Hr(),
            
            # Formulaire d'ajout
            html.H6("Ajouter un tarif"),
            dbc.Row([
                dbc.Col([
                    dbc.Input(id="new-quarter-input", placeholder="Trimestre (ex: Q1/2026)", size="sm")
                ], width=5),
                dbc.Col([
                    dbc.Input(id="new-price-input", placeholder="Prix (ct€/kWh)", type="number", size="sm")
                ], width=4),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-plus me-2"), "Ajouter"],
                        id='add-tariff-btn',
                        className='sage-button',
                        size='sm',
                        style={'width': '100%'}
                    )
                ], width=3)
            ], className="mb-3"),
            
            html.Div(id='creg-save-status')
        ]),
        dbc.ModalFooter([
            dbc.Button("Fermer", id="close-creg-modal", className="me-2", color="secondary")
        ])
    ], id="creg-modal", size="lg", is_open=False)


# ============================================================================
# SECTION AUTOMATISATION - Dashboard
# ============================================================================

def create_delete_confirmation_modal():
    """Crée la modale de confirmation de suppression"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("⚠️ Confirmation")),
        dbc.ModalBody("Voulez-vous vraiment supprimer cette ligne de l'historique ?\nCette action est irréversible et nettoiera la base de données."),
        dbc.ModalFooter([
            dbc.Button("Non, annuler", id="cancel-delete-btn", className="me-auto", color="secondary"),
            dbc.Button("Oui, supprimer", id="confirm-delete-btn", color="danger")
        ])
    ], id="delete-run-modal", is_open=False)


def create_automation_dashboard():
    """Crée le dashboard de monitoring des automatisations"""
    return dbc.Card([
        dbc.CardHeader([
            html.H4("🤖 Automatisation Mensuelle", className="mb-0", style={'color': Config.SAGE_GREEN})
        ]),
        dbc.CardBody([
            
            # Statut actuel et Configuration Active
            dbc.Row([
                # Colonne 1: Statut
                dbc.Col([
                    html.H5("📊 Statut Actuel", style={'color': Config.DARK_GREY}),
                    html.Div(id='automation-current-status', className="mb-3")
                ], width=4),
                
                # Colonne 2: Prochaine Exécution
                dbc.Col([
                    html.H5("📅 Prochaine Exécution", style={'color': Config.DARK_GREY}),
                    html.Div(id='automation-next-run', className="mb-3")
                ], width=4),
                
                # Colonne 3: Configuration Active (NOUVEAU)
                dbc.Col([
                    html.H5("⚙️ Configuration Active", style={'color': Config.DARK_GREY}),
                    html.Div(id='automation-config-summary', className="mb-3")
                ], width=4)
            ], className="mb-4"),
            
            html.Hr(),
            
            # Zone d'alerte pour le déclenchement manuel
            html.Div(id='manual-trigger-alert', className="mb-3"),
            
            # Boutons d'action
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-play me-2"), "Exécuter Maintenant"],
                        id='manual-trigger-btn',
                        className='sage-button',
                        style={'width': '100%'}
                    )
                ], width=4),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-cog me-2"), "Configuration"],
                        id='open-config-modal-btn',
                        className='sage-button',
                        style={'width': '100%'}
                    )
                ], width=4),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-sync me-2"), "Rafraîchir"],
                        id='refresh-status-btn',
                        className='sage-button',
                        style={'width': '100%'}
                    )
                ], width=4)
            ], className="mb-4"),
            
            html.Hr(),
            
            # Historique
            html.H5("📋 Historique des Exécutions", style={'color': Config.SAGE_GREEN}),
            html.Div(id='automation-history-table'),
            
            # Modale de suppression et Store caché
            create_delete_confirmation_modal(),
            dcc.Store(id='run-to-delete-id')
        ])
    ], className="mb-4")


def create_automation_history_table(runs):
    """Crée le tableau d'historique des automatisations avec suppression"""
    if not runs:
        return dbc.Alert("Aucune exécution enregistrée", style={"backgroundColor": "rgba(152, 192, 163, 0.2)", "borderColor": Config.SAGE_GREEN, "color": "#2c3e50"})
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("Date", style={'backgroundColor': Config.DARK_GREY, 'color': 'white'}),
            html.Th("Période", style={'backgroundColor': Config.DARK_GREY, 'color': 'white'}),
            html.Th("Étape", style={'backgroundColor': Config.DARK_GREY, 'color': 'white'}),
            html.Th("Statut", style={'backgroundColor': Config.DARK_GREY, 'color': 'white'}),
            html.Th("Message", style={'backgroundColor': Config.DARK_GREY, 'color': 'white'}),
            html.Th("", style={'backgroundColor': Config.DARK_GREY, 'color': 'white', 'width': '50px'}) # Colonne suppression
        ]))
    ]
    
    rows = []
    for run in runs:
        status_badge = create_status_badge(run['status'])
        
        try:
            run_date = datetime.fromisoformat(run['run_date']).strftime('%d/%m/%Y %H:%M')
        except:
            run_date = run['run_date']
        
        # Bouton suppression avec pattern-matching ID
        delete_btn = dbc.Button(
            html.I(className="fas fa-trash-alt"),
            id={'type': 'delete-run-btn', 'index': run['id']},
            color="danger",
            outline=True,
            size="sm",
            className="border-0 bg-transparent",
            title="Supprimer cette ligne"
        )

        rows.append(html.Tr([
            html.Td(run_date),
            html.Td(f"{run['period_start']} → {run['period_end']}"),
            html.Td(run['step']),
            html.Td(status_badge),
            html.Td(run['message'], style={'fontSize': '0.85em'}),
            html.Td(delete_btn, style={'textAlign': 'center'})
        ]))
    
    table_body = [html.Tbody(rows)]
    
    return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True)


def create_status_badge(status):
    """Crée un badge de statut coloré"""
    status_colors = {
        'success': 'success',
        'pending': 'warning',
        'failed': 'danger',
        'error': 'danger',
        'warning': 'warning',
        'skipped': 'secondary'
    }
    
    status_icons = {
        'success': '✅',
        'pending': '⏳',
        'failed': '❌',
        'error': '❌',
        'warning': '⚠️',
        'skipped': '⏭️'
    }
    
    color = status_colors.get(status, 'secondary')
    icon = status_icons.get(status, '❓')
    
    return dbc.Badge(
        f"{icon} {status.upper()}",
        color=color,
        className="me-1"
    )


# ============================================================================
# MODALE DE CONFIGURATION AUTOMATISATION
# ============================================================================

def create_automation_config_modal_simple():
    """Crée la modale de configuration des APIs, Email et Planification"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("⚙️ Configuration de l'Automatisation")),
        dbc.ModalBody([
            # --- 1. CONFIGURATION PLANIFICATION (NOUVEAU) ---
            html.H5("⏰ Planification", style={'color': Config.SAGE_GREEN, 'fontWeight': 'bold'}),
            html.P("Définissez quand l'automatisation doit se lancer."),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Moment de l'envoi :", style={'fontWeight': 'bold'}),
                    dbc.Select(
                        id='schedule-mode-input',
                        options=[
                            {'label': 'Dernier jour du mois (recommandé)', 'value': 'last_day'},
                            {'label': '1er jour du mois suivant', 'value': 'first_day'},
                            {'label': 'Désactivé', 'value': 'disabled'} # AJOUT OPTION DÉSACTIVÉ
                        ],
                        value='last_day'
                    )
                ], width=8),
                dbc.Col([
                    html.Label("Heure :", style={'fontWeight': 'bold'}),
                    dbc.Input(
                        id='schedule-time-input',
                        type='time',
                        value='23:59'
                    )
                ], width=4)
            ], className="mb-4"),
            
            html.Hr(),

            # Configuration Smappee (Inchangé)
            html.H5("🔌 API Smappee", style={'color': Config.SAGE_GREEN, 'fontWeight': 'bold'}),
            html.P("Configurez vos identifiants Smappee pour récupérer automatiquement les données de recharge."),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Client ID:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='smappee-client-id-input', type='password', placeholder='Votre Client ID Smappee')
                ], width=4),
                dbc.Col([
                    html.Label("Client Secret:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='smappee-client-secret-input', type='password', placeholder='Votre Client Secret')
                ], width=4),
                dbc.Col([
                    html.Label("Location ID:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='smappee-location-id-input', type='text', placeholder='Service Location ID')
                ], width=4)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button([html.I(className="fas fa-vial me-2"), "Tester Smappee"], id='test-smappee-btn', className='sage-button', size='sm')
                ], width=6),
                dbc.Col([html.Div(id='smappee-test-result')], width=6)
            ], className="mb-4"),
            
            html.Hr(),
            
            # Configuration Email (Modifié pour inclure le destinataire)
            html.H5("📧 Notifications Email", style={'color': Config.SAGE_GREEN, 'fontWeight': 'bold'}),
            html.P("Configurez le serveur SMTP et le destinataire de la note de frais."),
            
            # --- NOUVEAU CHAMP : EMAIL DESTINATAIRE ---
            dbc.Row([
                dbc.Col([
                    html.Label("Destinataire de la note de frais :", style={'fontWeight': 'bold'}),
                    dbc.Input(
                        id='notification-email-input',
                        type='email',
                        placeholder='exemple@domaine.com',
                        value=Config.NOTIFICATION_EMAIL
                    )
                ], width=12)
            ], className="mb-3"),
            # -------------------------------------------
            
            dbc.Row([
                dbc.Col([
                    html.Label("Serveur SMTP:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='smtp-server-input', type='text', placeholder='mail.infomaniak.com')
                ], width=6),
                dbc.Col([
                    html.Label("Port SMTP:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='smtp-port-input', type='number', value=587, placeholder='587')
                ], width=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    html.Label("Email utilisateur (SMTP):", style={'fontWeight': 'bold'}),
                    dbc.Input(id='smtp-user-input', type='email', placeholder='votre@email.com')
                ], width=6),
                dbc.Col([
                    html.Label("Mot de passe:", style={'fontWeight': 'bold'}),
                    dbc.Input(id='smtp-password-input', type='password', placeholder='Mot de passe ou App Password')
                ], width=6)
            ], className="mb-2"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button([html.I(className="fas fa-vial me-2"), "Tester Email"], id='test-email-btn', className='sage-button', size='sm')
                ], width=6),
                dbc.Col([html.Div(id='email-test-result')], width=6)
            ], className="mb-4")
        ]),
        dbc.ModalFooter([
            dbc.Button("Annuler", id="close-config-modal", className="me-2", color="secondary"),
            dbc.Button([html.I(className="fas fa-save me-2"), "Sauvegarder"], id="save-config-btn", className="sage-button")
        ])
    ], id="automation-config-modal", size="xl", is_open=False)


# ============================================================================
# STORES ET DOWNLOADS
# ============================================================================

def create_stores():
    """Crée les composants de stockage de données"""
    return [
        dcc.Store(id='stored-data'),
        dcc.Store(id='default-dates', data={'min': None, 'max': None}),
    ]


def create_downloads():
    """Crée les composants de téléchargement"""
    return [
        dcc.Download(id="download-monthly-pdf")
    ]


def create_intervals():
    """Crée les composants d'intervalle pour rafraîchissement automatique"""
    return [
        dcc.Interval(
            id='automation-refresh-interval',
            interval=Config.AUTO_REFRESH_INTERVAL,  # 30 secondes
            n_intervals=0
        )
    ]