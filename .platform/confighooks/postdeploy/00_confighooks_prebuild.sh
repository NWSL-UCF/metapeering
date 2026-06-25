#!/bin/bash

export DOMAIN_NAMES=$(/opt/elasticbeanstalk/bin/get-config environment -k DOMAIN_NAMES)
export FORCE_SSL=$(/opt/elasticbeanstalk/bin/get-config environment -k FORCE_SSL)

bash .platform/_scripts/00_ssl_setup.sh

echo "00_confighooks_prebuild.sh was run"