#!/bin/bash

# Define variables
SERVICE_NAME="flaskapp"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
APP_DIR="$(pwd)"
APP_ENTRYPOINT="${APP_DIR}/serve.sh"

# Check if serve.sh exists
if [ ! -f "$APP_ENTRYPOINT" ]; then
    echo "Error: ${APP_ENTRYPOINT} does not exist."
    exit 1
fi

# Create the systemd service file
sudo bash -c "cat > ${SERVICE_FILE}" << EOL
[Unit]
Description=Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
ExecStart=${APP_ENTRYPOINT}
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Start and enable the service
sudo systemctl start ${SERVICE_NAME}.service
sudo systemctl enable ${SERVICE_NAME}.service

echo "Service ${SERVICE_NAME} has been installed and started."
