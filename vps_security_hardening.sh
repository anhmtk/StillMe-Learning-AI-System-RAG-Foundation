#!/bin/bash
# StillMe VPS Security Hardening Script
# Run this script on the VPS to secure it

echo "🛡️ StillMe VPS Security Hardening"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SECTION]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_header "1. System Updates & Basic Security"
# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install essential security tools
print_status "Installing security tools..."
apt install -y ufw fail2ban htop iptables-persistent netstat-nat

print_header "2. Firewall Configuration (UFW)"
# Configure UFW firewall
print_status "Configuring UFW firewall..."

# Reset UFW to defaults
ufw --force reset

# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (port 22) - CRITICAL: Don't lock yourself out!
ufw allow 22/tcp comment 'SSH access'

# Allow StillMe services
ufw allow 21568/tcp comment 'StillMe Gateway'
ufw allow 1216/tcp comment 'StillMe AI Server'

# Allow HTTP/HTTPS for future use
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Enable UFW
ufw --force enable

print_status "UFW firewall configured and enabled"

print_header "3. SSH Security Hardening"
# SSH security configuration
print_status "Hardening SSH configuration..."

# Backup original SSH config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# SSH security settings
cat > /etc/ssh/sshd_config << 'EOF'
# StillMe VPS SSH Configuration
Port 22
Protocol 2

# Authentication
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Security settings
MaxAuthTries 3
MaxSessions 2
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 60

# Disable dangerous features
PermitEmptyPasswords no
X11Forwarding no
AllowTcpForwarding no
GatewayPorts no
PermitTunnel no

# Logging
SyslogFacility AUTH
LogLevel INFO

# Banner
Banner /etc/ssh/banner
EOF

# Create SSH banner
cat > /etc/ssh/banner << 'EOF'
***************************************************************************
                    STILLME AI VPS - AUTHORIZED ACCESS ONLY
***************************************************************************
This system is for the use of authorized users only. Individuals using
this computer system without authority, or in excess of their authority,
are subject to having all of their activities on this system monitored
and recorded by system personnel.

In the course of monitoring individuals improperly using this system,
or in the course of system maintenance, the activities of authorized
users may also be monitored.

Anyone using this system expressly consents to such monitoring and is
advised that if such monitoring reveals possible evidence of criminal
activity, system personnel may provide the evidence of such monitoring
to law enforcement officials.
***************************************************************************
EOF

# Restart SSH service
systemctl restart sshd

print_status "SSH security hardened"

print_header "4. Fail2Ban Configuration"
# Configure Fail2Ban for SSH protection
print_status "Configuring Fail2Ban..."

# Create custom jail for SSH
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[apache-auth]
enabled = false

[apache-badbots]
enabled = false

[apache-noscript]
enabled = false

[apache-overflows]
enabled = false
EOF

# Start and enable Fail2Ban
systemctl enable fail2ban
systemctl start fail2ban

print_status "Fail2Ban configured and started"

print_header "5. System Hardening"
# Disable unnecessary services
print_status "Disabling unnecessary services..."
systemctl disable bluetooth
systemctl disable cups
systemctl disable avahi-daemon

# Set secure file permissions
print_status "Setting secure file permissions..."
chmod 600 /etc/ssh/sshd_config
chmod 644 /etc/ssh/sshd_config.backup
chmod 600 /etc/ssh/banner

# Configure kernel parameters for security
print_status "Configuring kernel security parameters..."
cat >> /etc/sysctl.conf << 'EOF'

# StillMe VPS Security Parameters
# Disable IP forwarding
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Disable send redirects
net.ipv4.conf.all.send_redirects = 0

# Log martians
net.ipv4.conf.all.log_martians = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 1

# Ignore directed pings
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable IPv6 if not needed
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF

# Apply sysctl changes
sysctl -p

print_header "6. StillMe Service Security"
# Create secure directory for StillMe
print_status "Creating secure StillMe directory..."
mkdir -p /opt/stillme
chown root:root /opt/stillme
chmod 755 /opt/stillme

# Create logs directory
mkdir -p /var/log/stillme
chown root:root /var/log/stillme
chmod 755 /var/log/stillme

print_header "7. Monitoring & Logging"
# Install and configure log monitoring
print_status "Setting up log monitoring..."

# Create log rotation for StillMe
cat > /etc/logrotate.d/stillme << 'EOF'
/var/log/stillme/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload stillme-gateway stillme-ai > /dev/null 2>&1 || true
    endscript
}
EOF

# Install monitoring tools
apt install -y htop iotop nethogs

print_header "8. Backup Configuration"
# Setup automated backups
print_status "Setting up backup configuration..."

# Create backup script
cat > /opt/stillme/backup.sh << 'EOF'
#!/bin/bash
# StillMe Backup Script

BACKUP_DIR="/opt/stillme/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="stillme_backup_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

# Create backup
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    /opt/stillme \
    /etc/systemd/system/stillme-*.service \
    /etc/ssh/sshd_config \
    /etc/fail2ban/jail.local

# Keep only last 7 days of backups
find $BACKUP_DIR -name "stillme_backup_*.tar.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
EOF

chmod +x /opt/stillme/backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/stillme/backup.sh") | crontab -

print_status "Backup system configured"

print_header "9. Security Monitoring"
# Create security monitoring script
cat > /opt/stillme/security_monitor.sh << 'EOF'
#!/bin/bash
# StillMe Security Monitor

LOG_FILE="/var/log/stillme/security.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check for failed SSH attempts
FAILED_SSH=$(grep "Failed password" /var/log/auth.log | wc -l)
if [ $FAILED_SSH -gt 10 ]; then
    echo "$DATE - WARNING: High number of failed SSH attempts: $FAILED_SSH" >> $LOG_FILE
fi

# Check for banned IPs
BANNED_IPS=$(fail2ban-client status sshd | grep "Currently banned" | awk '{print $4}')
if [ ! -z "$BANNED_IPS" ]; then
    echo "$DATE - INFO: Currently banned IPs: $BANNED_IPS" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$DATE - WARNING: Disk usage high: ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
    echo "$DATE - WARNING: Memory usage high: ${MEM_USAGE}%" >> $LOG_FILE
fi
EOF

chmod +x /opt/stillme/security_monitor.sh

# Add to crontab for hourly monitoring
(crontab -l 2>/dev/null; echo "0 * * * * /opt/stillme/security_monitor.sh") | crontab -

print_status "Security monitoring configured"

print_header "10. Final Security Checks"
# Final security verification
print_status "Running final security checks..."

# Check UFW status
ufw status verbose

# Check Fail2Ban status
fail2ban-client status

# Check SSH configuration
sshd -t && print_status "SSH configuration is valid" || print_error "SSH configuration has errors"

# Check system services
print_status "Checking system services..."
systemctl is-active --quiet sshd && print_status "SSH service is running" || print_error "SSH service is not running"
systemctl is-active --quiet fail2ban && print_status "Fail2Ban is running" || print_error "Fail2Ban is not running"

print_header "Security Hardening Complete!"
echo -e "${GREEN}✅ VPS Security Hardening Completed Successfully!${NC}"
echo ""
echo "📋 Security Summary:"
echo "  🔥 Firewall (UFW): Enabled with custom rules"
echo "  🛡️  SSH: Hardened with security settings"
echo "  🚫 Fail2Ban: Active protection against brute force"
echo "  📊 Monitoring: Automated security monitoring"
echo "  💾 Backup: Daily automated backups"
echo "  🔒 System: Kernel parameters hardened"
echo ""
echo "⚠️  Important Notes:"
echo "  - SSH access is still allowed on port 22"
echo "  - StillMe services will be accessible on ports 21568 and 1216"
echo "  - Security logs are stored in /var/log/stillme/"
echo "  - Backup files are stored in /opt/stillme/backups/"
echo ""
echo "🔧 Next Steps:"
echo "  1. Deploy StillMe services"
echo "  2. Test all functionality"
echo "  3. Monitor security logs regularly"
echo "  4. Consider setting up SSL certificates"
echo ""
echo -e "${YELLOW}Remember to test SSH access before closing this session!${NC}"
