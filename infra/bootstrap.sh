#!/usr/bin/env bash
# bootstrap.sh — Oracle Cloud Free Tier Ampere A1 (Ubuntu 22.04 ARM64)
# Run as root (or with sudo) on a fresh instance.
# Creates a deploy user, hardens SSH, installs Docker + Ollama.
set -euo pipefail

echo "=== 1/7  Creating deploy user ==="
if ! id deploy &>/dev/null; then
  adduser --disabled-password --gecos "Deploy" deploy
  usermod -aG sudo deploy
  echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/deploy
  chmod 0440 /etc/sudoers.d/deploy
  # Copy SSH authorized_keys from the default user (ubuntu/opc)
  mkdir -p /home/deploy/.ssh
  cp ~/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
  chown -R deploy:deploy /home/deploy/.ssh
  chmod 700 /home/deploy/.ssh
  chmod 600 /home/deploy/.ssh/authorized_keys
  echo "  deploy user created."
else
  echo "  deploy user already exists, skipping."
fi

echo "=== 2/7  Configuring UFW firewall ==="
apt-get update -qq
apt-get install -y -qq ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   comment "SSH"
ufw allow 80/tcp   comment "HTTP"
ufw allow 443/tcp  comment "HTTPS"
ufw allow 8080/tcp comment "Spring Boot API"
ufw --force enable
ufw status verbose
echo "  UFW configured."

echo "=== 3/7  Installing Docker ==="
if ! command -v docker &>/dev/null; then
  apt-get install -y -qq ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
  usermod -aG docker deploy
  systemctl enable docker
  echo "  Docker installed."
else
  echo "  Docker already installed, skipping."
fi
docker --version
docker compose version

echo "=== 4/7  Creating 4GB swap file ==="
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo "/swapfile none swap sw 0 0" >> /etc/fstab
  echo "  Swap enabled."
else
  echo "  Swap already exists, skipping."
fi
free -h

echo "=== 5/7  Installing fail2ban ==="
apt-get install -y -qq fail2ban
systemctl enable fail2ban
systemctl start fail2ban
echo "  fail2ban installed and running."

echo "=== 6/7  Installing Ollama (native ARM64) ==="
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
  echo "  Ollama installed."
else
  echo "  Ollama already installed, skipping."
fi

echo "=== 7/7  Pulling models ==="
# Set keep_alive to 5m for evaluation performance
export OLLAMA_KEEP_ALIVE=5m
ollama pull phi3:mini
ollama pull nomic-embed-text
echo "  Models pulled."

echo ""
echo "=========================================="
echo "  Bootstrap complete!"
echo "  Docker:  $(docker --version)"
echo "  Compose: $(docker compose version)"
echo "  Ollama:  $(ollama --version)"
echo "  Models:  $(ollama list)"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. SSH in as deploy: ssh deploy@<VPS_IP>"
echo "  2. Clone repo: git clone https://github.com/YagvallkyaMishra-31/Enterprise-Knowledge-Assistant.git"
echo "  3. cd Enterprise-Knowledge-Assistant"
echo "  4. docker compose -f infra/docker-compose.prod.yml up -d"
