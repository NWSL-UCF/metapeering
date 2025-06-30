#!/bin/bash

set -e

ENV_FILE="/etc/environment"
RELOAD_NGINX=false
CRON_CMD="/usr/bin/certbot renew --quiet && /usr/sbin/nginx -s reload"
CRON_ENTRY="0 * * * * $CRON_CMD"

# Read current environment values
CURRENT_DOMAIN_NAMES="${DOMAIN_NAMES}"
CURRENT_FORCE_SSL="${FORCE_SSL}"

# Read stored values from /etc/environment
OLD_DOMAIN_NAMES=$(grep '^DOMAIN_NAMES=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"')
OLD_FORCE_SSL=$(grep '^FORCE_SSL=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"')

# Utility functions
generate_cert_and_conf() {
  domain=$1
  if certbot certonly --nginx -d "$domain" --non-interactive --agree-tos -m "admin@$domain"; then
    echo "Generated cert for $domain"
    RELOAD_NGINX=true
  fi
  create_ssl_conf "$domain"
}

create_ssl_conf() {
  domain=$1
  CONF_FILE="/etc/nginx/conf.d/${domain}.conf"
  cat <<EOF > "$CONF_FILE"
server {
    listen 443 ssl;
    server_name $domain;

    ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;

    location / {
        proxy_pass http://localhost:80;
    }
}
EOF
  echo "Created conf for $domain"
  RELOAD_NGINX=true
}

remove_cert_and_conf() {
  domain=$1
  certbot delete --cert-name "$domain" --non-interactive || true
  rm -f "/etc/nginx/conf.d/${domain}.conf"
  echo "Removed cert/conf for $domain"
  RELOAD_NGINX=true
}

check_cert_exists() {
  domain=$1
  [[ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]]
}

check_conf_exists() {
  domain=$1
  [[ -f "/etc/nginx/conf.d/${domain}.conf" ]]
}

remove_cert_cron() {
  crontab -l 2>/dev/null | grep -vF "$CRON_CMD" | crontab -
  echo "Removed certbot cron job"
}

add_cert_cron_if_missing() {
  crontab -l 2>/dev/null | grep -F "$CRON_CMD" >/dev/null || (
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "Added certbot cron job"
  )
}

# --- EARLY EXIT IF NO DOMAINS ---
if [[ -z "$CURRENT_DOMAIN_NAMES" ]]; then
  echo "No domain names provided. Cleaning up SSL certs, confs, and cron."

  # Remove all NGINX confs and certs that look like ours
  find /etc/nginx/conf.d -type f -name "*.conf" -exec rm -f {} \;
  find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d | while read -r certdir; do
    certname=$(basename "$certdir")
    certbot delete --cert-name "$certname" --non-interactive || true
  done

  remove_cert_cron

  # Remove DOMAIN_NAMES and FORCE_SSL from /etc/environment
  sed -i '/^DOMAIN_NAMES=/d' "$ENV_FILE"
  sed -i '/^FORCE_SSL=/d' "$ENV_FILE"

  echo "Exiting because no domain names are configured."
  exit 0
fi

# Proceed as before
IFS=',' read -ra CURRENT_DOMAINS <<< "$CURRENT_DOMAIN_NAMES"
IFS=',' read -ra OLD_DOMAINS <<< "$OLD_DOMAIN_NAMES"

if [[ "$CURRENT_DOMAIN_NAMES" != "$OLD_DOMAIN_NAMES" ]]; then
  echo "DOMAIN_NAMES changed. Cleaning up old certs and confs..."
  for old_domain in "${OLD_DOMAINS[@]}"; do
    remove_cert_and_conf "$old_domain"
  done

  for new_domain in "${CURRENT_DOMAINS[@]}"; do
    generate_cert_and_conf "$new_domain"
  done

  sed -i '/^DOMAIN_NAMES=/d' "$ENV_FILE"
  echo "DOMAIN_NAMES=$CURRENT_DOMAIN_NAMES" >> "$ENV_FILE"
else
  echo "DOMAIN_NAMES unchanged. Checking certs and confs..."
  for domain in "${CURRENT_DOMAINS[@]}"; do
    if check_cert_exists "$domain" && check_conf_exists "$domain"; then
      echo "Attempting renewal for $domain"
      if certbot renew --cert-name "$domain" --quiet --deploy-hook "true"; then
        echo "Renewed cert for $domain"
        RELOAD_NGINX=true
      fi
    else
      echo "Generating missing cert or conf for $domain"
      generate_cert_and_conf "$domain"
    fi
  done
fi

# Manage FORCE_SSL
FORCE_SSL_CONF="/etc/nginx/conf.d/force-ssl.conf"
if [[ "$CURRENT_FORCE_SSL" == "true" ]]; then
  if [[ ! -f "$FORCE_SSL_CONF" ]]; then
    echo "Creating force-ssl.conf"
    cat <<EOF > "$FORCE_SSL_CONF"
server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}
EOF
    RELOAD_NGINX=true
  fi
else
  if [[ -f "$FORCE_SSL_CONF" ]]; then
    echo "Removing force-ssl.conf"
    rm -f "$FORCE_SSL_CONF"
    RELOAD_NGINX=true
  fi
fi

# Update FORCE_SSL in /etc/environment if changed
if [[ "$CURRENT_FORCE_SSL" != "$OLD_FORCE_SSL" ]]; then
  sed -i '/^FORCE_SSL=/d' "$ENV_FILE"
  echo "FORCE_SSL=$CURRENT_FORCE_SSL" >> "$ENV_FILE"
fi

# Conditionally reload NGINX
if [[ "$RELOAD_NGINX" == "true" ]]; then
  echo "Changes detected. Reloading NGINX..."
  systemctl reload nginx
else
  echo "No changes. NGINX reload not required."
fi

# Only add cron job if domains exist
if [[ ${#CURRENT_DOMAINS[@]} -gt 0 ]]; then
  add_cert_cron_if_missing
fi

echo "SSL automation completed."
