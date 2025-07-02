#!/bin/bash

set -e

ENV_FILE="/etc/environment"
RELOAD_NGINX=false

# Read current environment values
CURRENT_DOMAIN_NAMES="${DOMAIN_NAMES}"

# Read stored values from /etc/environment
OLD_DOMAIN_NAMES=$(grep '^DOMAIN_NAMES=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"')

# Utility functions
generate_cert() {
  domain=$1
  if certbot --nginx -d "$domain" --non-interactive --agree-tos -m "admin@$domain"; then
    echo "Generated cert for $domain"
    RELOAD_NGINX=true
  fi
}

remove_cert() {
  domain=$1
  certbot delete --cert-name "$domain" --non-interactive || true
  echo "Removed cert for $domain"
  RELOAD_NGINX=true
}

check_cert_exists() {
  domain=$1
  [[ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]]
}

# --- EARLY EXIT IF NO DOMAINS ---
if [[ -z "$CURRENT_DOMAIN_NAMES" ]]; then
  echo "No domain names provided. Cleaning up SSL certs..."

  # Remove all certs via certbot
  find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d | while read -r certdir; do
    certname=$(basename "$certdir")
    certbot delete --cert-name "$certname" --non-interactive || true
  done

  # Remove DOMAIN_NAMES from /etc/environment
  sed -i '/^DOMAIN_NAMES=/d' "$ENV_FILE"

  echo "Exiting because no domain names are configured."
  exit 0
fi

# Proceed as before
IFS=',' read -ra CURRENT_DOMAINS <<< "$CURRENT_DOMAIN_NAMES"
IFS=',' read -ra OLD_DOMAINS <<< "$OLD_DOMAIN_NAMES"

if [[ "$CURRENT_DOMAIN_NAMES" != "$OLD_DOMAIN_NAMES" ]]; then
  echo "DOMAIN_NAMES changed. Cleaning up old certs..."
  for old_domain in "${OLD_DOMAINS[@]}"; do
    remove_cert "$old_domain"
  done

  for new_domain in "${CURRENT_DOMAINS[@]}"; do
    generate_cert "$new_domain"
  done

  sed -i '/^DOMAIN_NAMES=/d' "$ENV_FILE"
  echo "DOMAIN_NAMES=$CURRENT_DOMAIN_NAMES" >> "$ENV_FILE"
else
  echo "DOMAIN_NAMES unchanged. Checking certs..."
  for domain in "${CURRENT_DOMAINS[@]}"; do
    if check_cert_exists "$domain"; then
      echo "Attempting renewal for $domain"
      if certbot renew --cert-name "$domain" --quiet --deploy-hook "true"; then
        echo "Renewed cert for $domain"
        RELOAD_NGINX=true
      fi
    else
      echo "Generating missing cert for $domain"
      generate_cert "$domain"
    fi
  done
fi

# Conditionally reload NGINX
if [[ "$RELOAD_NGINX" == "true" ]]; then
  echo "Changes detected. Reloading NGINX..."
  systemctl reload nginx
else
  echo "No changes. NGINX reload not required."
fi

echo "SSL automation completed."
