#!/bin/bash
set -e

# Install system-level geospatial libraries required by Fiona, geopandas, pyproj, Shapely
dnf install -y gdal gdal-libs gdal-devel geos geos-devel proj proj-devel

echo "00_hooks_prebuild.sh was run"
