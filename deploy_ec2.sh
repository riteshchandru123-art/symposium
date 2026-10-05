#!/usr/bin/env bash
# Run this ON the EC2 instance (after SSHing in), not on your local machine.
#
# Assumes: Ubuntu 22.04+ instance, security group allows inbound TCP 8000
# (and 22 for SSH). See DEPLOY.md for the security group / launch steps.
#
# Usage:
#   chmod +x deploy_ec2.sh
#   ./deploy_ec2.sh

set -euo pipefail

echo "== Installing Docker =="
if ! command -v docker &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker "$USER"
    echo "Docker installed. You may need to log out and back in for group changes to apply."
else
    echo "Docker already installed, skipping."
fi

echo "== Checking for .env =="
if [ ! -f .env ]; then
    echo "No .env found. Copy .env.example to .env and fill in real values first:"
    echo "  cp .env.example .env"
    echo "  nano .env   # set DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, DB_PASSWORD, API keys"
    exit 1
fi

echo "== Building and starting containers (production config) =="
sudo docker compose -f docker-compose.prod.yml up --build -d

echo "== Waiting for containers to be healthy =="
sleep 10
sudo docker compose -f docker-compose.prod.yml ps

echo ""
echo "Done. The app should be reachable at http://<this-instance-public-ip>:8000"
echo "Create an admin user with:"
echo "  sudo docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo "Seed demo data with:"
echo "  sudo docker compose -f docker-compose.prod.yml exec web python manage.py seed_data"
