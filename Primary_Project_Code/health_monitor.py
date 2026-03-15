import psutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from .config import Config
from .logger import get_logger

logger = get_logger(__name__, 'health_monitor.log')

class HealthMonitor:
    """Monitor system health and send alerts"""
    
    def __init__(self):
        self.cpu_threshold = Config.CPU_THRESHOLD
        self.ram_threshold = Config.RAM_THRESHOLD
        self.disk_threshold = Config.DISK_THRESHOLD
    
    def get_cpu_usage(self):
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    def get_ram_usage(self):
        """Get current RAM usage percentage"""
        return psutil.virtual_memory().percent
    
    def get_disk_usage(self, path='C:\\'):
        """Get disk usage percentage for a given path"""
        try:
            return psutil.disk_usage(path).percent
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return 0
    
    def check_system_health(self):
        """Check all system metrics and return results"""
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu': self.get_cpu_usage(),
            'ram': self.get_ram_usage(),
            'disk': self.get_disk_usage(),
            'alerts': []
        }
        
        # Check for issues
        if results['cpu'] > self.cpu_threshold:
            results['alerts'].append(f"⚠️  HIGH CPU USAGE: {results['cpu']:.1f}%")
            logger.warning(f"High CPU usage detected: {results['cpu']:.1f}%")
        
        if results['ram'] > self.ram_threshold:
            results['alerts'].append(f"⚠️  HIGH RAM USAGE: {results['ram']:.1f}%")
            logger.warning(f"High RAM usage detected: {results['ram']:.1f}%")
        
        if results['disk'] > self.disk_threshold:
            results['alerts'].append(f"⚠️  HIGH DISK USAGE: {results['disk']:.1f}%")
            logger.warning(f"High disk usage detected: {results['disk']:.1f}%")
        
        return results
    
    def send_email_alert(self, subject, body):
        """Send email alert about system issues"""
        try:
            if not all([Config.EMAIL_SENDER, Config.EMAIL_PASSWORD, Config.EMAIL_RECIPIENT]):
                logger.error("Email configuration is incomplete. Please set up .env file")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_SENDER
            msg['To'] = Config.EMAIL_RECIPIENT
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {Config.EMAIL_RECIPIENT}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def display_health(self, results):
        """Display health information in a formatted way"""
        print("\n" + "="*50)
        print("       SYSTEM HEALTH MONITOR")
        print("="*50)
        print(f"Timestamp: {results['timestamp']}")
        print(f"CPU Usage:  {results['cpu']:>6.1f}% ", end="")
        print("🟢" if results['cpu'] <= self.cpu_threshold else "🔴")
        print(f"RAM Usage:  {results['ram']:>6.1f}% ", end="")
        print("🟢" if results['ram'] <= self.ram_threshold else "🔴")
        print(f"Disk Usage: {results['disk']:>6.1f}% ", end="")
        print("🟢" if results['disk'] <= self.disk_threshold else "🔴")
        
        if results['alerts']:
            print("\n" + "-"*50)
            print("ALERTS:")
            for alert in results['alerts']:
                print(f"  {alert}")
            
            # Send email if there are alerts
            alert_body = f"""
System Health Alert Report
Timestamp: {results['timestamp']}

CPU Usage: {results['cpu']:.1f}%
RAM Usage: {results['ram']:.1f}%
Disk Usage: {results['disk']:.1f}%

Issues Detected:
{chr(10).join(results['alerts'])}

Please take necessary action.
            """
            self.send_email_alert("🚨 System Health Alert", alert_body)
        else:
            print("\n✅ All systems normal!")
        
        print("="*50 + "\n")
