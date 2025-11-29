"""
Module d'envoi de notifications par email
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime


class EmailNotifier:
    """Classe pour envoyer des notifications par email"""
    
    def __init__(self, smtp_server, smtp_port, smtp_user, smtp_password, from_email=None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
    
    def send_automation_success(self, to_email, period_start, period_end, pdf_path=None):
        """
        Envoie un email de succès d'automatisation
        
        Args:
            to_email: Adresse email du destinataire
            period_start: Date de début de la période
            period_end: Date de fin de la période
            pdf_path: Chemin optionnel du PDF généré
        """
        subject = f"✅ Note de frais générée - {period_start} au {period_end}"
        
        body = f"""
        Bonjour,
        
        La note de frais mensuelle pour la période du {period_start} au {period_end} a été générée avec succès.
        
        Détails de l'automatisation:
        - Date d'exécution: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        - Période couverte: {period_start} → {period_end}
        - Statut: ✅ Succès
        
        Le document a été automatiquement:
        1. ✓ Généré au format PDF
        2. ✓ Envoyé vers Falco (gestion documentaire)
        
        Vous pouvez consulter le document dans votre espace Falco.
        
        ---
        Ceci est un message automatique généré par l'application Recharge.
        """
        
        return self._send_email(to_email, subject, body, pdf_path)
    
    def send_automation_error(self, to_email, period_start, period_end, error_message):
        """
        Envoie un email d'erreur d'automatisation
        
        Args:
            to_email: Adresse email du destinataire
            period_start: Date de début de la période
            period_end: Date de fin de la période
            error_message: Message d'erreur détaillé
        """
        subject = f"❌ Erreur automatisation - {period_start} au {period_end}"
        
        body = f"""
        Bonjour,
        
        Une erreur s'est produite lors de la génération automatique de la note de frais.
        
        Détails de l'erreur:
        - Date d'exécution: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        - Période concernée: {period_start} → {period_end}
        - Statut: ❌ Échec
        
        Message d'erreur:
        {error_message}
        
        Actions recommandées:
        1. Vérifier la configuration des API (Smappee, Falco)
        2. Consulter les logs de l'application
        3. Générer manuellement la note de frais si nécessaire
        
        ---
        Ceci est un message automatique généré par l'application Recharge.
        """
        
        return self._send_email(to_email, subject, body)
    
    def send_test_email(self, to_email):
        """Envoie un email de test"""
        subject = "🧪 Test de notification - Application Recharge"
        
        body = """
        Bonjour,
        
        Ceci est un email de test pour vérifier la configuration des notifications.
        
        Si vous recevez ce message, cela signifie que:
        - Le serveur SMTP est correctement configuré
        - Les identifiants sont valides
        - L'envoi d'emails fonctionne correctement
        
        Vous êtes prêt à recevoir les notifications automatiques !
        
        ---
        Ceci est un message de test.
        """
        
        return self._send_email(to_email, subject, body)
    
    def _send_email(self, to_email, subject, body, attachment_path=None):
        """
        Méthode privée pour envoyer un email
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Ajouter le corps du message
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Ajouter la pièce jointe si fournie
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
            
            # Connexion au serveur SMTP et envoi
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True, "Email envoyé avec succès"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Erreur d'authentification SMTP (vérifier identifiants)"
        except smtplib.SMTPException as e:
            return False, f"Erreur SMTP: {str(e)}"
        except Exception as e:
            return False, f"Erreur lors de l'envoi: {str(e)}"
    
    def test_connection(self):
        """Teste la connexion au serveur SMTP"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
            return True, "Connexion SMTP réussie"
        except smtplib.SMTPAuthenticationError:
            return False, "Erreur d'authentification SMTP"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"