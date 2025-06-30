#!/bin/bash

export DOMAIN_NAMES=${DOMAIN_NAMES}
export FORCE_SSL=${FORCE_SSL}

bash .platform/_scripts/00_ssl_setup.sh

echo "00_confighooks_prebuild.sh was run"