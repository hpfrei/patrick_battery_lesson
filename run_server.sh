#!/usr/bin/env bash
# Starts the battery server. Leave this running while you use the client.
set -e
cd "$(dirname "$0")"
python3 server.py
