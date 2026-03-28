# PrintBot AI - Cloud Deployment Guide

## 🌐 Deploy to the Cloud (No Computer Required!)

This guide shows you how to deploy PrintBot AI to a cloud server so it runs 24/7 without your computer.

---

## ☁️ Recommended Cloud Providers

| Provider | Cost/Month | Best For |
|----------|------------|----------|
| **DigitalOcean** | $12-24 | Beginners, easy setup |
| **Linode** | $12-24 | Good performance |
| **AWS Lightsail** | $10-20 | AWS ecosystem |
| **Hetzner** | €6-12 | Cheapest option |
| **Vultr** | $10-20 | Fast deployment |

---

## 🚀 Quick Deploy (DigitalOcean)

### Step 1: Create Droplet

1. Sign up at [digitalocean.com](https://digitalocean.com)
2. Click "Create" → "Droplets"
3. Choose:
   - **OS**: Ubuntu 22.04 (LTS)
   - **Plan**: Basic ($12/month - 2GB RAM)
   - **Datacenter**: Closest to your customers
   - **Authentication**: SSH key (recommended)
4. Click "Create Droplet"

### Step 2: Connect to Server

```bash
# Copy your server's IP address from DigitalOcean dashboard
ssh root@YOUR_SERVER_IP
```

### Step 3: Install Docker

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Start Docker
systemctl start docker
systemctl enable docker
```

### Step 4: Upload PrintBot AI

**Option A: Using SCP (from your computer)**
```bash
# From your local machine
scp -r /path/to/printbot-ai root@YOUR_SERVER_IP:/opt/
```

**Option B: Using Git**
```bash
# On the server
cd /opt
git clone https://github.com/yourusername/printbot-ai.git
```

### Step 5: Configure Environment

```bash
cd /opt/printbot-ai

# Create .env file
nano .env

# Fill in your API keys (same as local setup)
```

### Step 6: Start PrintBot AI

```bash
# Start with Docker Compose
docker compose up -d

# Check logs
docker compose logs -f

# Check status
docker compose ps
```

### Step 7: Access Dashboard

Open your browser:
```
http://YOUR_SERVER_IP
```

---

## 🔒 Secure Your Deployment

### Set Up Firewall

```bash
# Install UFW
apt install ufw -y

# Allow necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS (if using SSL)

# Enable firewall
ufw enable
```

### Set Up SSL (HTTPS) with Let's Encrypt

```bash
# Install Certbot
docker run -it --rm \
  -v /opt/printbot-ai/certbot-data:/etc/letsencrypt \
  -v /opt/printbot-ai/docker/nginx.conf:/etc/nginx/conf.d/default.conf \
  certbot/certbot certonly --standalone -d yourdomain.com

# Update nginx config to use SSL
nano docker/nginx.conf
# (Add SSL configuration)

# Restart
docker compose restart
```

### Set Up Domain Name

1. Buy a domain (Namecheap, GoDaddy, etc.)
2. Point A record to your server IP
3. Update nginx config with your domain

---

## 📊 Monitoring

### View Logs

```bash
# All logs
docker compose logs

# Specific service
docker compose logs printbot

# Follow logs in real-time
docker compose logs -f
```

### Check System Resources

```bash
# Docker stats
docker stats

# Server resources
htop

# Disk usage
df -h
```

### Set Up Alerts (Optional)

```bash
# Install monitoring
docker run -d \
  --name=netdata \
  -p 19999:19999 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  netdata/netdata
```

Access at: `http://YOUR_SERVER_IP:19999`

---

## 🔄 Updates

### Update PrintBot AI

```bash
cd /opt/printbot-ai

# Pull latest code
git pull

# Rebuild and restart
docker compose down
docker compose up -d --build
```

### Update Docker Images

```bash
docker compose pull
docker compose up -d
```

---

## 💾 Backups

### Automated Backups

```bash
# Create backup script
nano /opt/backup-printbot.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/printbot"
mkdir -p $BACKUP_DIR

# Backup data
tar -czf $BACKUP_DIR/printbot_data_$DATE.tar.gz /opt/printbot-ai/data

# Backup database
docker exec printbot-ai sqlite3 /app/data/printbot.db ".backup /tmp/backup.db"
docker cp printbot-ai:/tmp/backup.db $BACKUP_DIR/printbot_db_$DATE.db

# Keep only last 7 backups
ls -t $BACKUP_DIR/*.tar.gz | tail -n +8 | xargs rm -f
ls -t $BACKUP_DIR/*.db | tail -n +8 | xargs rm -f
```

Make executable and schedule:
```bash
chmod +x /opt/backup-printbot.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /opt/backup-printbot.sh" | crontab -
```

---

## 🛠️ Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs printbot

# Check for port conflicts
netstat -tlnp | grep 80

# Restart
docker compose down
docker compose up -d
```

### Out of Memory

```bash
# Check memory usage
free -h

# Add swap space
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Database Issues

```bash
# Access database
docker exec -it printbot-ai sqlite3 /app/data/printbot.db

# Check tables
.tables

# Backup before fixing
.cp /app/data/printbot.db /app/data/printbot.db.backup
```

---

## 💰 Cost Optimization

### Reduce Costs

1. **Use smaller droplet**: Start with 1GB RAM ($6/month)
2. **Hetzner Cloud**: Cheapest option (€3.29/month)
3. **AWS Spot Instances**: Up to 90% discount
4. **Turn off when not needed**: For testing

### Free Tier Options

| Provider | Free Tier | Limitations |
|----------|-----------|-------------|
| AWS | 12 months | 750 hours/month |
| Google Cloud | $300 credit | 90 days |
| Azure | $200 credit | 30 days |
| Oracle Cloud | Always free | Limited resources |

---

## 📱 Mobile Access

Once deployed, access your dashboard from anywhere:

```
http://YOUR_SERVER_IP
```

Or with domain:
```
https://yourdomain.com
```

---

## ✅ Post-Deploy Checklist

- [ ] Dashboard loads at `http://YOUR_SERVER_IP`
- [ ] All agents show as "running"
- [ ] API responds at `/api/status`
- [ ] SSL working (if configured)
- [ ] Firewall enabled
- [ ] Backups configured
- [ ] Monitoring set up
- [ ] Check-in works
- [ ] Manual override panel accessible

---

## 🆘 Getting Help

If you have issues:

1. Check logs: `docker compose logs -f`
2. Check system resources: `htop`
3. Restart: `docker compose restart`
4. Review this guide

---

**Your PrintBot AI is now running 24/7 in the cloud!** 🎉
