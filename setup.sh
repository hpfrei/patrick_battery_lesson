#!/usr/bin/env bash
# One-time setup: creates batteries.db with sample data.
set -e
cd "$(dirname "$0")"
python3 seed_db.py
