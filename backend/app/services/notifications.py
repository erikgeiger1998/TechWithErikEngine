import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", 587))
        self.smtp_user = os.environ.get("SMTP_USER")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        self.recipient_email = os.environ.get("SMTP_USER") # Default to self

    def _get_html_body(self, recommendations: list) -> str:
        html = """
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f4f5; color: #18181b; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                h1 { color: #09090b; font-size: 24px; border-bottom: 1px solid #e4e4e7; padding-bottom: 10px; }
                .rec-card { border: 1px solid #e4e4e7; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: #fafafa; }
                .topic { font-size: 18px; font-weight: 600; color: #18181b; margin: 0 0 10px 0; }
                .roi { font-size: 20px; font-weight: bold; color: #10b981; }
                .metrics { font-size: 14px; color: #71717a; margin-bottom: 10px; }
                .evidence { font-size: 13px; color: #52525b; background: #e4e4e7; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-right: 5px; margin-bottom: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>☀️ Tech With Erik - Morning Brief</h1>
                <p>Here are your deterministic filming recommendations for today.</p>
        """
        
        for rec in recommendations:
            film_decision = "🎥 FILM TODAY" if rec.film_decision else "🛑 SKIP"
            html += f"""
                <div class="rec-card">
                    <h2 class="topic">{film_decision} - {rec.topic}</h2>
                    <div class="roi">ROI: {round(rec.confidence_percentage / 10.0, 1)}</div>
                    <div class="metrics">Trust Risk: {'LOW' if rec.trust_score >= 7.5 else 'HIGH'}</div>
                    <p style="font-size: 14px; color: #3f3f46;">{rec.reasoning}</p>
                </div>
            """
            
        html += """
                <p style="font-size: 12px; color: #a1a1aa; margin-top: 30px;">Generated automatically by your Editorial OS.</p>
            </div>
        </body>
        </html>
        """
        return html

    def send_morning_brief(self, recommendations: list):
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Skipping Morning Brief email.")
            return
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "☀️ Tech With Erik - Morning Brief"
        msg['From'] = self.smtp_user
        msg['To'] = self.recipient_email
        
        html_body = self._get_html_body(recommendations)
        msg.attach(MIMEText(html_body, 'html'))
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                logger.info(f"Morning Brief emailed to {self.recipient_email} successfully.")
        except Exception as e:
            logger.error(f"Failed to send Morning Brief email: {e}")
