#!/bin/bash

# Source in this shell
source /etc/environment

set -e

NGINX_CONF_DIR="/etc/nginx/conf.d"
CONF_FILE_NAME="redirect_to_https.conf"
TEMPLATE_SOURCE="/var/app/current/.platform/nginx/conf.d/redirect_to_https.conf.template"
TARGET_CONF_PATH="$NGINX_CONF_DIR/$CONF_FILE_NAME"

LOG_FILE="/var/log/eb-hooks.log"
echo "[FORCE_SSL Hook] Running at $(date)" >> "$LOG_FILE"

FORCE_SSL=$(printenv FORCE_SSL)
DOMAIN_NAMES=$(printenv DOMAIN_NAMES)

# Check if DOMAIN_NAMES contains at least one non-empty domain
has_domains=false
IFS=',' read -ra DOMAIN_LIST <<< "$DOMAIN_NAMES"
for domain in "${DOMAIN_LIST[@]}"; do
    if [[ -n "$domain" && "$domain" =~ [^[:space:]] ]]; then
        has_domains=true
        break
    fi
done

if [ "$FORCE_SSL" = "true" ] && [ "$has_domains" = "true" ]; then
    echo "[FORCE_SSL Hook] FORCE_SSL=true and valid DOMAIN_NAMES found, enabling redirect..." >> "$LOG_FILE"
    if [ -f "$TEMPLATE_SOURCE" ]; then
        cp "$TEMPLATE_SOURCE" "$TARGET_CONF_PATH"
        echo "[FORCE_SSL Hook] Config deployed to $TARGET_CONF_PATH" >> "$LOG_FILE"
    else
        echo "[FORCE_SSL Hook] Template not found at $TEMPLATE_SOURCE" >> "$LOG_FILE"
        exit 1
    fi
else
    echo "[FORCE_SSL Hook] Redirect not enabled (FORCE_SSL=$FORCE_SSL, DOMAIN_NAMES=$DOMAIN_NAMES)" >> "$LOG_FILE"
    if [ -f "$TARGET_CONF_PATH" ]; then
        rm -f "$TARGET_CONF_PATH"
        echo "[FORCE_SSL Hook] Removed $TARGET_CONF_PATH" >> "$LOG_FILE"
    fi
fi

# Reload NGINX if needed
nginx -t && nginx -s reload
echo "[FORCE_SSL Hook] NGINX reloaded." >> "$LOG_FILE"
