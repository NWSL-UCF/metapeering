#!/bin/bash

# Print commands and their arguments as they are executed
set -x

# Define DOMAIN_NAMES as global environment variable
"DOMAINS_NAMES=\"$DOMAIN_NAMES\"" | sudo tee /etc/environment