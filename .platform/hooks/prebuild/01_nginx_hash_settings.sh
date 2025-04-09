#!/bin/bash
set -e

# Create a custom NGINX conf file early in the load order
cat <<EOF > /etc/nginx/conf.d/00_custom_hash_settings.conf
server_names_hash_bucket_size 128;
types_hash_max_size 2048;
types_hash_bucket_size 128;
EOF
