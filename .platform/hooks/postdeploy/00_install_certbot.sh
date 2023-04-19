#!/usr/bin/env bash
#
# Author: Paola C.
#
# This script extracts domain names specified within the environment variable DOMAIN_NAMES
# and generates a certificate using Certbot for each domain in the list.
# The resulting certificates can be used for secure communication with each of the specified domains.
#

# Checks if the environment variable exists
if [[ -z ${DOMAIN_NAMES+x} ]]; then
  echo The environment variables DOMAIN_NAMES is not defined.
  exit
fi

# Extract the domain names and runs the certbot command
IFS=, a=( $DOMAIN_NAMES )
for i in ${a[@]}
do
    echo "Creating certificate for the domain ${i}"
    sudo /usr/local/bin/certbot --nginx -n -d $i --agree-tos --email quinn.barber@knights.ucf.edu
done
