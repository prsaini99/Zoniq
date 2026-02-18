# Deployment Guide — AWS EC2

## Prerequisites

- AWS Account
- A domain name (optional, for HTTPS)

---

## Step 1: Launch EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**
2. Choose:
   - **AMI**: Ubuntu 22.04 LTS
   - **Instance type**: `t2.medium` (2 vCPU, 4GB RAM) or `t3.medium`
   - **Storage**: 20GB+ gp3 EBS
3. **Security Group** — allow these inbound rules:
   | Port | Protocol | Source      | Purpose    |
   |------|----------|-------------|------------|
   | 22   | TCP      | Your IP     | SSH        |
   | 80   | TCP      | 0.0.0.0/0  | HTTP       |
   | 443  | TCP      | 0.0.0.0/0  | HTTPS      |
4. Create or select a key pair and download the `.pem` file

---

## Step 2: Connect to Instance

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<your-ec2-public-ip>
```

---

## Step 3: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group (no sudo needed for docker commands)
sudo usermod -aG docker $USER

# Apply group changes (or logout and login again)
newgrp docker

# Verify
docker --version
docker compose version
```

---

## Step 4: Clone and Configure

```bash
# Clone repository
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# Create environment file
cp .env.example .env
nano .env
```

### Production `.env` values to change:

```env
ENVIRONMENT=PROD
DEBUG=False
BACKEND_SERVER_WORKERS=4

# Use a strong password
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=zoniq_db
POSTGRES_USERNAME=zoniq_user

# IMPORTANT: Generate a real secret key
# python3 -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=<generated-secret-key>
HASHING_SALT=<generated-random-salt>

# Set to False for production
IS_DB_ECHO_LOG=False
IS_DB_FORCE_ROLLBACK=False

# Set your actual domain or EC2 public IP
FRONTEND_URL=http://<your-domain-or-ip>

# Fill in your real service credentials
RAZORPAY_KEY_ID=<your-live-key>
RAZORPAY_KEY_SECRET=<your-live-secret>
SMTP_USERNAME=<your-email>
SMTP_PASSWORD=<your-password>
```

---

## Step 5: Deploy

```bash
./deploy.sh
```

This will:
1. Build Docker images for backend and frontend
2. Start PostgreSQL, backend, frontend, and Nginx
3. Run database migrations automatically
4. Seed the admin user

Your app will be available at `http://<your-ec2-public-ip>`

---

## Step 6 (Optional): Custom Domain + HTTPS

### Point your domain to EC2

Add an **A record** in your DNS provider:
- **Type**: A
- **Name**: `@` (or your subdomain)
- **Value**: Your EC2 public IP

### Install SSL with Certbot

```bash
# Install Certbot
sudo apt install certbot -y

# Stop nginx temporarily
docker compose -f docker-compose.prod.yaml stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificate files will be at:
#   /etc/letsencrypt/live/yourdomain.com/fullchain.pem
#   /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Update `nginx/nginx.conf` to add HTTPS:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # ... rest of your location blocks ...
}
```

Add SSL volume to `docker-compose.prod.yaml` nginx service:

```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
  ports:
    - "80:80"
    - "443:443"
```

Then restart:

```bash
docker compose -f docker-compose.prod.yaml up -d nginx
```

### Auto-renew SSL

```bash
sudo crontab -e
# Add this line:
0 3 * * * certbot renew --quiet && docker restart zoniq_nginx
```

---

## Useful Commands

```bash
# View all logs
docker compose -f docker-compose.prod.yaml logs -f

# View specific service logs
docker compose -f docker-compose.prod.yaml logs -f backend

# Restart a service
docker compose -f docker-compose.prod.yaml restart backend

# Stop everything
docker compose -f docker-compose.prod.yaml down

# Stop and remove volumes (WARNING: deletes database data)
docker compose -f docker-compose.prod.yaml down -v

# Rebuild and redeploy after code changes
git pull
docker compose -f docker-compose.prod.yaml up -d --build

# Run a migration manually
docker exec -it zoniq_backend alembic upgrade head

# Access database shell
docker exec -it zoniq_db psql -U zoniq_user -d zoniq_db
```
