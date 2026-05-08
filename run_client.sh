#!/usr/bin/env bash
# Starts the GUI client. Run setup.sh once, and run_server.sh first.
set -e
cd "$(dirname "$0")"
python3 client.py
