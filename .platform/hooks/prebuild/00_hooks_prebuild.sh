#!/bin/bash
set -e

# Install system-level geospatial libraries required by pyproj and Shapely
# Note: GDAL is not available in AL2023 default repos. Fiona will use its
# bundled GDAL via pip wheel. geos and proj are available natively.
dnf install -y geos geos-devel proj proj-devel

echo "00_hooks_prebuild.sh completed successfully"
