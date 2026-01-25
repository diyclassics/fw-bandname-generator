# DigitalOcean Droplet Setup Guide

A step-by-step guide to creating and configuring a DigitalOcean droplet for hosting web applications.

---

## Step 1: Create an Account

1. Go to [digitalocean.com](https://www.digitalocean.com/)
2. Sign up (you'll get free credits as a new user)
3. Add a payment method

---

## Step 2: Set Up SSH Keys (Recommended)

SSH keys are more secure than passwords. Do this on your **local machine** before creating the droplet.

### Check for existing keys

```bash
ls ~/.ssh/id_*.pub
```

### Generate a new key (if needed)

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

Press Enter to accept defaults. Don't set a passphrase if you want passwordless login.

### Copy your public key

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy the entire output (starts with `ssh-ed25519`).

### Add to DigitalOcean

1. Go to **Settings > Security > SSH Keys**
2. Click **Add SSH Key**
3. Paste your public key
4. Give it a name (e.g., "MacBook Pro")

---

## Step 3: Create the Droplet

1. Click **Create > Droplets**

2. **Choose Region**
   - Pick the datacenter closest to you or your users
   - For US East Coast: NYC1, NYC3, or TOR1

3. **Choose an Image**
   - Select **Ubuntu**
   - Choose **24.04 (LTS)** - Long Term Support, most stable

4. **Choose Size**
   - Click **Basic**
   - **Regular** (SSD)
   - **$6/mo** (1 GB RAM / 1 CPU / 25 GB SSD) is enough for multiple small apps
   - Upgrade later if needed

5. **Choose Authentication**
   - Select **SSH Key**
   - Check the box for your SSH key

6. **Choose Hostname**
   - Give it a meaningful name: `web-server` or `portfolio-apps`

7. **Optional: Enable Backups**
   - +20% cost, but worth it for production
   - Creates weekly automatic backups

8. Click **Create Droplet**

---

## Step 4: Connect to Your Droplet

Wait for the droplet to be created (~60 seconds), then note the **IP address**.

```bash
ssh root@YOUR_DROPLET_IP
```

First connection will ask to verify the fingerprint - type `yes`.

---

## Step 5: Initial Server Setup

### Update the system

```bash
apt update && apt upgrade -y
```

### Set timezone

```bash
timedatectl set-timezone America/New_York  # Or your timezone
```

List available timezones:
```bash
timedatectl list-timezones | grep America
```

### Create a non-root user (optional but recommended)

```bash
adduser deployer
usermod -aG sudo deployer
```

Copy SSH key to new user:
```bash
rsync --archive --chown=deployer:deployer ~/.ssh /home/deployer
```

Now you can SSH as `deployer@YOUR_IP` instead of root.

---

## Step 6: Install Essential Software

### Basic tools

```bash
apt install -y curl wget git unzip htop
```

### For Python/Flask apps

```bash
apt install -y python3 python3-pip python3-venv
```

### For web serving

```bash
apt install -y nginx
```

### For SSL certificates

```bash
apt install -y certbot python3-certbot-nginx
```

### Verify installations

```bash
python3 --version
nginx -v
certbot --version
```

---

## Step 7: Configure Firewall

DigitalOcean has a cloud firewall (recommended) or you can use `ufw` on the droplet.

### Option A: DigitalOcean Cloud Firewall (Recommended)

1. Go to **Networking > Firewalls**
2. Click **Create Firewall**
3. Add inbound rules:
   - SSH (22) - Your IP only, or all IPs
   - HTTP (80) - All IPs
   - HTTPS (443) - All IPs
4. Apply to your droplet

### Option B: UFW (On-Server Firewall)

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
ufw status
```

---

## Step 8: Configure SSH Security (Optional)

Edit SSH config:
```bash
nano /etc/ssh/sshd_config
```

Recommended changes:
```
PermitRootLogin no              # Disable root login
PasswordAuthentication no       # Disable password login (SSH key only)
```

Restart SSH:
```bash
systemctl restart ssh
```

**Warning:** Make sure you can SSH as your non-root user before disabling root login!

---

## Step 9: Set Up Automatic Updates (Optional)

```bash
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

Select "Yes" to enable automatic security updates.

---

## Your Droplet is Ready!

You now have a secure, updated Ubuntu server ready to host applications.

**Next steps:**
- Point a domain/subdomain to your droplet IP
- Deploy your application(s)
- Set up SSL with Let's Encrypt

---

## Quick Reference

| Task | Command |
|------|---------|
| SSH into server | `ssh root@YOUR_IP` or `ssh deployer@YOUR_IP` |
| Check disk space | `df -h` |
| Check memory | `free -h` |
| Check running processes | `htop` |
| Reboot | `reboot` |
| View system logs | `journalctl -xe` |
| Check nginx status | `systemctl status nginx` |

---

## Useful DigitalOcean Features

- **Snapshots**: Create a point-in-time backup ($0.06/GB/mo)
- **Floating IPs**: Static IP that survives droplet destruction (free)
- **Monitoring**: Free CPU/memory/disk graphs
- **Droplet Console**: Browser-based terminal access (for emergencies)
