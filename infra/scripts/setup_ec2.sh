#!/bin/bash
# =============================================================
# SmartCampus AI — EC2 Setup Script
# Run this once on a fresh Ubuntu 22.04 EC2 t2.micro instance
# =============================================================

set -e

echo "🚀 Setting up SmartCampus AI on EC2..."

# ── System updates ────────────────────────────────────────────
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib nginx git curl

# ── PostgreSQL setup ──────────────────────────────────────────
sudo systemctl start postgresql
sudo systemctl enable postgresql

sudo -u postgres psql <<EOF
CREATE DATABASE smartcampus;
CREATE USER smartcampus_user WITH PASSWORD 'your_db_password_here';
GRANT ALL PRIVILEGES ON DATABASE smartcampus TO smartcampus_user;
EOF

echo "✅ PostgreSQL ready"

# ── App directory ─────────────────────────────────────────────
sudo mkdir -p /opt/smartcampus
sudo chown ubuntu:ubuntu /opt/smartcampus
cd /opt/smartcampus

# Clone your repo (replace with your GitHub URL)
# git clone https://github.com/yourusername/smartcampus-ai.git .

# ── Python virtual environment ────────────────────────────────
cd /opt/smartcampus/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python dependencies installed"

# ── Environment file ──────────────────────────────────────────
# Create .env — fill in your actual values!
cat > /opt/smartcampus/backend/.env << 'ENVEOF'
DEBUG=False
SECRET_KEY=CHANGE_THIS_TO_RANDOM_STRING
DATABASE_URL=postgresql://smartcampus_user:your_db_password_here@localhost:5432/smartcampus
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=smartcampus-pdfs-yourname
ANTHROPIC_API_KEY=sk-ant-your-key
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
COGNITO_REGION=us-east-1
ENVEOF

echo "⚠️  Edit /opt/smartcampus/backend/.env with your actual API keys!"

# ── Systemd service ───────────────────────────────────────────
sudo tee /etc/systemd/system/smartcampus.service << 'SERVICEEOF'
[Unit]
Description=SmartCampus AI FastAPI
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/smartcampus/backend
Environment="PATH=/opt/smartcampus/backend/venv/bin"
ExecStart=/opt/smartcampus/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable smartcampus
sudo systemctl start smartcampus

echo "✅ FastAPI service started"

# ── Nginx reverse proxy ───────────────────────────────────────
sudo tee /etc/nginx/sites-available/smartcampus << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
        client_max_body_size 25M;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
NGINXEOF

sudo ln -sf /etc/nginx/sites-available/smartcampus /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

echo "✅ Nginx configured"
echo ""
echo "🎉 Setup complete!"
echo "   API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)/api/v1"
echo "   Docs: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)/docs"
echo ""
echo "Next steps:"
echo "  1. Edit /opt/smartcampus/backend/.env with your API keys"
echo "  2. sudo systemctl restart smartcampus"
echo "  3. Deploy frontend to Vercel"
