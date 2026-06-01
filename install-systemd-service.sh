#!/bin/bash
# Installation script for systemd service and reverse proxy setup
# For Raspberry Pi and Python environment setup

set -e  # Exit on any error

echo "=== Monhubeclipse systemd Installation ==="

# Update system
echo -e "\nUpdating system packages...\n"
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo -e "\nInstalling system dependencies...\n"
sudo apt install -y nginx

# Create systemd service file
echo -e "\nCreating systemd service file...\n"
SERVICE_FILE="/etc/systemd/system/monhubeclipse.service"
sudo bash -c "cat ./utils/monhubeclipse.service > $SERVICE_FILE"

# Reload systemd and enable service
echo -e "\nReloading systemd and enabling service...\n"
sudo systemctl daemon-reload
sudo systemctl enable --now monhubeclipse.service
sudo systemctl restart monhubeclipse.service

# Setup Nginx reverse proxy
echo -e "\nSetting up Nginx reverse proxy...\n"
# Use the hostname of the Raspberry Pi for the server_name in Nginx configuration
HNAME=`hostname`.local
sudo sed -i "s/server_name .*/server_name $HNAME;/" ./utils/monhubeclipse.nginx
NGINX_CONFIG="/etc/nginx/sites-available/monhubeclipse"
sudo bash -c "cat ./utils/monhubeclipse.nginx > $NGINX_CONFIG"
sudo ln -s $NGINX_CONFIG /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable --now nginx

# Verify installation
echo -e "\nVerifying installation...\n"
if systemctl is-active --quiet monhubeclipse.service; then
    echo "✅ Monhubeclipse service is running."
else
    echo "❌ Monhubeclipse service failed to start. Please check the logs with: sudo journalctl -u monhubeclipse.service"
    exit 1
fi
# Check Nginx status
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running."
else
    echo "❌ Nginx failed to start. Please check the logs with: sudo journalctl -u nginx"
    exit 1
fi
# check if the service is accessible via the hostname
if curl -s --head http://$HNAME:80/ | grep "200 OK" > /dev/null; then
    echo "✅ Monhubeclipse is accessible via http://$HNAME:80/"
else
    echo "❌ Monhubeclipse is not accessible via http://$HNAME:80/. Please check the Nginx configuration and service status."
    exit 1
fi

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "You can access Monhubeclipse via http://$HNAME:80/"
echo ""