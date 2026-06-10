#!/bin/bash

echo "=== POSTDEPLOY HOOK START ==="
echo "Working directory: $(pwd)"

DOMAIN_NAMES=$(/opt/elasticbeanstalk/bin/get-config environment -k DOMAIN_NAMES)
echo "DOMAIN_NAMES from get-config: '$DOMAIN_NAMES'"

export DOMAIN_NAMES
export FORCE_SSL=$(/opt/elasticbeanstalk/bin/get-config environment -k FORCE_SSL)
echo "FORCE_SSL: '$FORCE_SSL'"

echo "Running ssl_setup script..."
bash .platform/_scripts/00_ssl_setup.sh 2>&1

echo "=== POSTDEPLOY HOOK END ==="
