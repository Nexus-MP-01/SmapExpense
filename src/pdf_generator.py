"""
Générateur de PDF pour note de frais mensuelle avec tarifs CREG (Simplifié)
"""
import io
import os
import pandas as pd
from dash import dcc
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from config import Config
from src.utils import MOIS_FR, load_creg_tariffs, get_tariff_for_period, get_quarter_from_date


def generate_monthly_pdf_data(json_data, start_date, end_date, selected_vehicles, region=None):
    """Génère la note de frais mensuelle basée sur les tarifs CREG"""
    if json_data is None or not selected_vehicles:
        return None
    
    df = pd.read_json(json_data)
    df['startTime'] = pd.to_datetime(df['startTime'])
    df['endTime'] = pd.to_datetime(df['endTime'])
    
    # Filtrer par période et véhicules
    mask = (df['startTime'].dt.date >= pd.to_datetime(start_date).date()) & \
           (df['startTime'].dt.date <= pd.to_datetime(end_date).date()) & \
           (df['rfid'].isin(selected_vehicles))
    df_filtered = df[mask].copy()
    
    # Calculer le coût avec tarifs CREG
    df_filtered['tariff_creg'] = df_filtered['startTime'].apply(
        lambda x: get_tariff_for_period(x, x)
    )
    df_filtered['cost'] = df_filtered['energyConsumed_kWh'] * df_filtered['tariff_creg']
    
    # Créer le PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés (identiques)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor(Config.SAGE_GREEN),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#555555'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor(Config.SAGE_GREEN),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    # Logo
    try:
        logo = Image(Config.LOGO_PATH, width=Config.LOGO_WIDTH_CM*cm, height=Config.LOGO_HEIGHT_CM*cm)
        logo.hAlign = 'LEFT'
        elements.append(logo)
        elements.append(Spacer(1, 0.5*cm))
    except:
        pass
    
    # Titre
    elements.append(Paragraph("Note de frais mensuelle - Recharge de véhicule électrique", title_style))
    
    start_dt = pd.to_datetime(start_date)
    periode_text = f"{MOIS_FR[start_dt.month]} {start_dt.year}"
    
    elements.append(Paragraph(periode_text, subtitle_style))
    
    date_now = datetime.now()
    elements.append(Paragraph(f"Document émis le {date_now.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.6*cm))
    
    # Note CREG
    quarter = get_quarter_from_date(start_date)
    note_text = f"<b>Tarif appliqué :</b> Tarif CREG {quarter}<br/>" \
                "Le tarif CREG (Commission de Régulation de l'Électricité et du Gaz) est utilisé par le SPF Finances " \
                "pour le calcul du remboursement des frais d'électricité liés à la recharge à domicile."
    elements.append(Paragraph(note_text, styles['Normal']))
    elements.append(Spacer(1, 0.8*cm))
    
    # Tarif appliqué
    elements.append(Paragraph("Tarif CREG appliqué", heading_style))
    avg_tariff = get_tariff_for_period(start_date, end_date)
    elements.append(Paragraph(
        f"{quarter} : {avg_tariff:.4f} € HTVA/kWh (soit {avg_tariff*1.06:.4f} € TVAC/kWh)",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.8*cm))
    
    # Montant à rembourser
    total_cost = df_filtered['cost'].sum()
    
    for vehicle in selected_vehicles:
        elements.append(Paragraph("Montant à rembourser", heading_style))
        
        vehicle_data = df_filtered[df_filtered['rfid'] == vehicle]
        vehicle_cost = vehicle_data['cost'].sum()
        vehicle_kwh = vehicle_data['energyConsumed_kWh'].sum()
        
        table_data = [['Description', 'Consommation (kWh)', 'Montant (EUR)']]
        table_data.append([
            f"{MOIS_FR[start_dt.month]} {start_dt.year}",
            f"{vehicle_kwh:.3f}",
            f"{vehicle_cost:.2f} €"
        ])
        
        monthly_table = Table(table_data, colWidths=[6*cm, 4*cm, 4*cm])
        monthly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(Config.DARK_GREY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(Config.LIGHT_GREY)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(monthly_table)
        elements.append(Spacer(1, 0.8*cm))
    
    # Message de synthèse
    summary_text = f"Une note de frais de <b>{total_cost:.2f} €</b> peut être réalisée pour le mois de {MOIS_FR[start_dt.month]} {start_dt.year}."
    elements.append(Paragraph(summary_text, styles['Normal']))
    
    # Générer le PDF
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"note_frais_mensuelle_{start_date}_{end_date}.pdf"
    
    return dcc.send_bytes(buffer.getvalue(), filename)


def generate_monthly_pdf_auto(df, start_date, end_date, selected_vehicles, region=None):
    """
    Génère la note de frais mensuelle et la sauvegarde sur disque (pour automatisation)
    """
    # Convertir les dates si nécessaire
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date).date()
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date).date()
    
    # Préparer les données (parsing identique à avant)
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
    
    # Filtrer par période et véhicules
    mask = (df['startTime'].dt.date >= start_date) & \
           (df['startTime'].dt.date <= end_date) & \
           (df['rfid'].isin(selected_vehicles))
    df_filtered = df[mask].copy()
    
    # Calculer le coût avec tarifs CREG
    df_filtered['tariff_creg'] = df_filtered['startTime'].apply(
        lambda x: get_tariff_for_period(x, x)
    )
    df_filtered['cost'] = df_filtered['energyConsumed_kWh'] * df_filtered['tariff_creg']
    
    # Créer le nom de fichier unique
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"note_frais_{start_date}_{end_date}_{timestamp}.pdf"
    pdf_path = os.path.join(Config.PDF_OUTPUT_DIR, filename)
    
    # Créer le PDF (même logique que generate_monthly_pdf_data)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        topMargin=1*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor(Config.SAGE_GREEN),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#555555'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor(Config.SAGE_GREEN),
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    # Logo
    try:
        logo = Image(Config.LOGO_PATH, width=Config.LOGO_WIDTH_CM*cm, height=Config.LOGO_HEIGHT_CM*cm)
        logo.hAlign = 'LEFT'
        elements.append(logo)
        elements.append(Spacer(1, 0.5*cm))
    except:
        pass
    
    # Titre
    elements.append(Paragraph("Note de frais mensuelle - Recharge de véhicule électrique", title_style))
    
    start_dt = pd.to_datetime(start_date)
    periode_text = f"{MOIS_FR[start_dt.month]} {start_dt.year}"
    
    elements.append(Paragraph(periode_text, subtitle_style))
    
    date_now = datetime.now()
    elements.append(Paragraph(f"Document émis le {date_now.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.6*cm))
    
    # Note CREG
    quarter = get_quarter_from_date(start_date)
    note_text = f"<b>Tarif appliqué :</b> Tarif CREG {quarter}<br/>" \
                "Le tarif CREG (Commission de Régulation de l'Électricité et du Gaz) est utilisé par le SPF Finances " \
                "pour le calcul du remboursement des frais d'électricité liés à la recharge à domicile."
    elements.append(Paragraph(note_text, styles['Normal']))
    elements.append(Spacer(1, 0.8*cm))
    
    # Tarif appliqué
    elements.append(Paragraph("Tarif CREG appliqué", heading_style))
    avg_tariff = get_tariff_for_period(start_date, end_date)
    elements.append(Paragraph(
        f"{quarter} : {avg_tariff:.4f} € HTVA/kWh (soit {avg_tariff*1.06:.4f} € TVAC/kWh)",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.8*cm))
    
    # Montant à rembourser
    total_cost = df_filtered['cost'].sum()
    
    for vehicle in selected_vehicles:
        elements.append(Paragraph("Montant à rembourser", heading_style))
        
        vehicle_data = df_filtered[df_filtered['rfid'] == vehicle]
        vehicle_cost = vehicle_data['cost'].sum()
        vehicle_kwh = vehicle_data['energyConsumed_kWh'].sum()
        
        table_data = [['Description', 'Consommation (kWh)', 'Montant (EUR)']]
        table_data.append([
            f"{MOIS_FR[start_dt.month]} {start_dt.year}",
            f"{vehicle_kwh:.3f}",
            f"{vehicle_cost:.2f} €"
        ])
        
        monthly_table = Table(table_data, colWidths=[6*cm, 4*cm, 4*cm])
        monthly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(Config.DARK_GREY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(Config.LIGHT_GREY)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(monthly_table)
        elements.append(Spacer(1, 0.8*cm))
    
    # Message de synthèse
    summary_text = f"Une note de frais de <b>{total_cost:.2f} €</b> peut être réalisée pour le mois de {MOIS_FR[start_dt.month]} {start_dt.year}."
    elements.append(Paragraph(summary_text, styles['Normal']))
    
    # Générer le PDF
    doc.build(elements)
    
    return pdf_path