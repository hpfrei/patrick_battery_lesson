#!/usr/bin/env bash
# Starts the battery web server. A browser tab opens automatically.
# On first run, the SQLite DB is seeded with sample data.
set -e
cd "$(dirname "$0")"
python3 server.py
