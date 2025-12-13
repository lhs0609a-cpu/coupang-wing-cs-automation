"""
Notification Service
Handles email, Slack, and other notifications
"""
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from loguru import logger

from ..config import settings


class NotificationService:
    """
    Service for sending notifications via multiple channels
    """

    def __init__(self):
        self.email_enabled = bool(
            getattr(settings, 'SMTP_HOST', None) and
            getattr(settings, 'SMTP_USER', None)
        )
        self.slack_enabled = bool(getattr(settings, 'SLACK_WEBHOOK_URL', None))

    def send_alert(self, message: str, level: str = "info", channels: List[str] = None):
        """
        Send alert notification

        Args:
            message: Alert message
            level: Alert level (info, warning, error, critical)
            channels: List of channels to send to (email, slack). Default: all enabled
        """
        if channels is None:
            channels = []
            if self.email_enabled:
                channels.append('email')
            if self.slack_enabled:
                channels.append('slack')

        logger.info(f"Sending {level} alert: {message}")

        if 'email' in channels and self.email_enabled:
            self._send_email_alert(message, level)

        if 'slack' in channels and self.slack_enabled:
            self._send_slack_alert(message, level)

    def send_daily_report(self, report: Dict, time: str = 'morning'):
        """
        Send daily report

        Args:
            report: Report data dictionary
            time: Time of day (morning, evening)
        """
        subject = f"{'🌅 Morning' if time == 'morning' else '🌆 Evening'} Daily Report - {report['date']}"

        # Format report as HTML email
        html_content = self._format_report_html(report, time)

        # Format report as Slack message
        slack_message = self._format_report_slack(report, time)

        if self.email_enabled:
            self._send_email(
                subject=subject,
                html_content=html_content,
                to_addresses=getattr(settings, 'REPORT_EMAIL_RECIPIENTS', [])
            )

        if self.slack_enabled:
            self._send_slack_message(slack_message)

    def send_high_risk_inquiry_alert(self, inquiry_id: int, inquiry_text: str, risk_factors: List[str]):
        """
        Send alert for high-risk inquiry

        Args:
            inquiry_id: Inquiry ID
            inquiry_text: Inquiry text
            risk_factors: List of risk factors
        """
        message = f"""
🚨 High-Risk Inquiry Detected

Inquiry ID: {inquiry_id}
Content: {inquiry_text[:200]}...

Risk Factors:
{chr(10).join(f'- {factor}' for factor in risk_factors)}

Action Required: Please review manually
        """.strip()

        self.send_alert(message, level="warning")

    def send_error_notification(self, error: str, context: Dict = None):
        """
        Send error notification

        Args:
            error: Error message
            context: Additional context
        """
        message = f"""
❌ System Error

Error: {error}

Context:
{json.dumps(context, indent=2) if context else 'N/A'}

Time: {datetime.utcnow().isoformat()}
        """.strip()

        self.send_alert(message, level="error")

    def send_success_notification(self, message: str):
        """
        Send success notification

        Args:
            message: Success message
        """
        self.send_alert(f"✅ {message}", level="info")

    def _send_email_alert(self, message: str, level: str):
        """Send email alert"""
        subject = f"[{level.upper()}] Coupang Wing CS Alert"

        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }

        html_content = f"""
        <html>
        <body>
            <h2>{emoji_map.get(level, '')} Alert</h2>
            <p><strong>Level:</strong> {level.upper()}</p>
            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <hr>
            <pre>{message}</pre>
        </body>
        </html>
        """

        self._send_email(
            subject=subject,
            html_content=html_content,
            to_addresses=getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
        )

    def _send_email(self, subject: str, html_content: str, to_addresses: List[str]):
        """Send email via SMTP"""
        if not to_addresses:
            logger.warning("No email recipients configured")
            return

        try:
            smtp_host = getattr(settings, 'SMTP_HOST', None)
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_user = getattr(settings, 'SMTP_USER', None)
            smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
            from_address = getattr(settings, 'SMTP_FROM', smtp_user)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_address
            msg['To'] = ', '.join(to_addresses)

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.success(f"Email sent to {len(to_addresses)} recipients")

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

    def _send_slack_alert(self, message: str, level: str):
        """Send Slack alert"""
        color_map = {
            'info': '#36a64f',
            'warning': '#ff9900',
            'error': '#ff0000',
            'critical': '#8b0000'
        }

        slack_message = {
            'attachments': [{
                'color': color_map.get(level, '#36a64f'),
                'title': f'{level.upper()} Alert',
                'text': message,
                'footer': 'Coupang Wing CS Automation',
                'ts': int(datetime.utcnow().timestamp())
            }]
        }

        self._send_slack_message(slack_message)

    def _send_slack_message(self, message: Dict):
        """Send message to Slack"""
        try:
            webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            if not webhook_url:
                return

            with httpx.Client() as client:
                response = client.post(webhook_url, json=message)
                response.raise_for_status()

            logger.success("Slack message sent")

        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")

    def _format_report_html(self, report: Dict, time: str) -> str:
        """Format report as HTML"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .metric {{ background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .metric-title {{ font-weight: bold; color: #333; }}
                .metric-value {{ font-size: 24px; color: #0066cc; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
            </style>
        </head>
        <body>
            <h1>{'🌅 Morning' if time == 'morning' else '🌆 Evening'} Daily Report</h1>
            <p><strong>Date:</strong> {report['date']}</p>

            <h2>📊 Inquiries</h2>
            <div class="metric">
                <div class="metric-title">Total Inquiries</div>
                <div class="metric-value">{report['inquiries']['total']}</div>
            </div>
            <div class="metric">
                <div class="metric-title">Urgent</div>
                <div class="metric-value">{report['inquiries']['urgent']}</div>
            </div>
            <div class="metric">
                <div class="metric-title">Requires Human Review</div>
                <div class="metric-value">{report['inquiries']['requires_human']}</div>
            </div>

            <h2>💬 Responses</h2>
            <div class="metric">
                <div class="metric-title">Total Responses</div>
                <div class="metric-value">{report['responses']['total']}</div>
            </div>
            <div class="metric">
                <div class="metric-title">Average Confidence</div>
                <div class="metric-value">{report['responses']['avg_confidence']}%</div>
            </div>

            <h2>🤖 Automation</h2>
            <div class="metric">
                <div class="metric-title">Auto-Approved</div>
                <div class="metric-value">{report['automation']['auto_approved']}</div>
            </div>
            <div class="metric">
                <div class="metric-title">Automation Rate</div>
                <div class="metric-value">{report['automation']['automation_rate']}%</div>
            </div>

            <h2>📈 Categories</h2>
            <table>
                <tr><th>Category</th><th>Count</th></tr>
                {''.join(f'<tr><td>{cat}</td><td>{count}</td></tr>' for cat, count in report['categories'].items())}
            </table>

            <hr>
            <p><small>Generated by Coupang Wing CS Automation System</small></p>
        </body>
        </html>
        """
        return html

    def _format_report_slack(self, report: Dict, time: str) -> Dict:
        """Format report as Slack message"""
        emoji = '🌅' if time == 'morning' else '🌆'

        text = f"{emoji} *{time.title()} Daily Report* - {report['date']}\n\n"
        text += f"📊 *Inquiries*\n"
        text += f"• Total: {report['inquiries']['total']}\n"
        text += f"• Urgent: {report['inquiries']['urgent']}\n"
        text += f"• Requires Human: {report['inquiries']['requires_human']}\n\n"

        text += f"💬 *Responses*\n"
        text += f"• Total: {report['responses']['total']}\n"
        text += f"• Avg Confidence: {report['responses']['avg_confidence']}%\n\n"

        text += f"🤖 *Automation*\n"
        text += f"• Auto-Approved: {report['automation']['auto_approved']}\n"
        text += f"• Automation Rate: {report['automation']['automation_rate']}%\n\n"

        text += f"📈 *Top Categories*\n"
        for cat, count in list(report['categories'].items())[:5]:
            text += f"• {cat}: {count}\n"

        return {
            'text': text,
            'username': 'CS Automation Bot',
            'icon_emoji': ':robot_face:'
        }
