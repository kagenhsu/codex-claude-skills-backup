#!/bin/zsh
cd "$(dirname "$0")"
open index.html
python3 scripts/quota_guard_app.py --config quota_guard.example.json
