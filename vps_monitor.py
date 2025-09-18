#!/usr/bin/env python3
"""
StillMe VPS Monitor - Real-time monitoring script
Monitor VPS services và tự động alert khi có vấn đề
"""

import requests
import time
import json
import smtplib
from datetime import datetime
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Configuration
VPS_IP = "160.191.89.99"
AI_SERVER_PORT = 1216
GATEWAY_PORT = 21568
CHECK_INTERVAL = 60  # seconds
ALERT_EMAIL = "anhnguyen.nk86@gmail.com"

# Email configuration (from .env)
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "anhnguyen.nk86@gmail.com",
    "password": "your_app_password"  # Update this
}

class StillMeMonitor:
    def __init__(self):
        self.vps_ip = VPS_IP
        self.ai_port = AI_SERVER_PORT
        self.gateway_port = GATEWAY_PORT
        self.check_interval = CHECK_INTERVAL
        self.alert_email = ALERT_EMAIL
        self.last_alert_time = {}
        
    def test_service(self, port, service_name):
        """Test if service is responding"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.vps_ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def test_http_endpoint(self, url, service_name):
        """Test HTTP endpoint"""
        try:
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def send_alert(self, subject, message):
        """Send email alert"""
        try:
            # Check if we should send alert (avoid spam)
            now = datetime.now()
            if subject in self.last_alert_time:
                if (now - self.last_alert_time[subject]).seconds < 300:  # 5 minutes
                    return
            
            self.last_alert_time[subject] = now
            
            msg = MimeMultipart()
            msg['From'] = EMAIL_CONFIG['email']
            msg['To'] = self.alert_email
            msg['Subject'] = f"StillMe Alert: {subject}"
            
            body = f"""
StillMe VPS Monitoring Alert

Time: {now}
VPS IP: {self.vps_ip}

{message}

Please check the VPS immediately.

Best regards,
StillMe Monitoring System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            server.starttls()
            server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
            text = msg.as_string()
            server.sendmail(EMAIL_CONFIG['email'], self.alert_email, text)
            server.quit()
            
            print(f"Alert sent: {subject}")
            
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    def check_services(self):
        """Check all services and send alerts if needed"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check AI Server
        ai_port_ok = self.test_service(self.ai_port, "AI Server")
        ai_http_ok = self.test_http_endpoint(f"http://{self.vps_ip}:{self.ai_port}/health", "AI Server")
        
        # Check Gateway
        gateway_port_ok = self.test_service(self.gateway_port, "Gateway")
        gateway_http_ok = self.test_http_endpoint(f"http://{self.vps_ip}:{self.gateway_port}/health", "Gateway")
        
        # Status summary
        ai_status = "OK" if (ai_port_ok and ai_http_ok) else "FAIL"
        gateway_status = "OK" if (gateway_port_ok and gateway_http_ok) else "FAIL"
        
        print(f"[{timestamp}] AI Server: {ai_status}, Gateway: {gateway_status}")
        
        # Send alerts for failures
        if not (ai_port_ok and ai_http_ok):
            self.send_alert(
                "AI Server Down",
                f"AI Server is not responding on port {self.ai_port}.\n"
                f"Port accessible: {ai_port_ok}\n"
                f"HTTP accessible: {ai_http_ok}\n\n"
                f"Please SSH to VPS and run:\n"
                f"systemctl restart stillme-ai-server"
            )
        
        if not (gateway_port_ok and gateway_http_ok):
            self.send_alert(
                "Gateway Down", 
                f"Gateway is not responding on port {self.gateway_port}.\n"
                f"Port accessible: {gateway_port_ok}\n"
                f"HTTP accessible: {gateway_http_ok}\n\n"
                f"Please SSH to VPS and run:\n"
                f"systemctl restart stillme-gateway"
            )
        
        return {
            "timestamp": timestamp,
            "ai_server": {"port": ai_port_ok, "http": ai_http_ok, "status": ai_status},
            "gateway": {"port": gateway_port_ok, "http": gateway_http_ok, "status": gateway_status}
        }
    
    def run_monitoring(self):
        """Run continuous monitoring"""
        print(f"Starting StillMe VPS Monitoring...")
        print(f"VPS IP: {self.vps_ip}")
        print(f"Check interval: {self.check_interval} seconds")
        print(f"Alert email: {self.alert_email}")
        print("=" * 50)
        
        while True:
            try:
                result = self.check_services()
                
                # Save to log file
                with open("vps_monitor.log", "a") as f:
                    f.write(json.dumps(result) + "\n")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Error in monitoring: {e}")
                time.sleep(self.check_interval)

def main():
    monitor = StillMeMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()
