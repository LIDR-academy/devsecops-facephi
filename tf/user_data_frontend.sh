#!/bin/bash
set -euo pipefail

BUCKET="${bucket}"
PORT="${frontend_port}"
REGION="${region}"
APP_DIR="/opt/frontend"

# Install dependencies
dnf update -y
dnf install -y nodejs npm unzip aws-cli

# Download and extract frontend artifact from S3
mkdir -p "$APP_DIR"
aws s3 cp "s3://$BUCKET/frontend.zip" /tmp/frontend.zip --region "$REGION"
unzip -o /tmp/frontend.zip -d "$APP_DIR"
rm /tmp/frontend.zip

# Install the 'serve' static file server globally
npm install -g serve

# Create systemd service to serve the static build
cat > /etc/systemd/system/frontend.service <<EOF
[Unit]
Description=Frontend Application
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/serve -s . -l $PORT
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable frontend
systemctl start frontend
