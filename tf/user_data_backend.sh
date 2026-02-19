#!/bin/bash
set -euo pipefail

BUCKET="${bucket}"
PORT="${backend_port}"
REGION="${region}"
APP_DIR="/opt/backend"

# Install dependencies
dnf update -y
dnf install -y nodejs npm unzip aws-cli

# Download and extract backend artifact from S3
mkdir -p "$APP_DIR"
aws s3 cp "s3://$BUCKET/backend.zip" /tmp/backend.zip --region "$REGION"
unzip -o /tmp/backend.zip -d "$APP_DIR"
rm /tmp/backend.zip

cd "$APP_DIR"

# Install Node.js dependencies if package.json is present
if [ -f package.json ]; then
  npm install --production
fi

# Create systemd service for automatic restarts and zero-downtime redeploys
cat > /etc/systemd/system/backend.service <<EOF
[Unit]
Description=Backend Application
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/node index.js
Restart=always
RestartSec=5
Environment=PORT=$PORT
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable backend
systemctl start backend
