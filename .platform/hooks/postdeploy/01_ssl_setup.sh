#!/bin/bash

# Source in this shell
source /etc/environment

# Print name of this script
echo $0

# Print env vars
echo "ENV variables:"
printenv

# Execute SSL script
bash /opt/ssl_manager/certbot_setup.sh