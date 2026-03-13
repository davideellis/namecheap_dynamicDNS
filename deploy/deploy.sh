#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/namecheap_dynamicDNS"
VENV_DIR="$APP_DIR/.venv"

if [[ ! -d "$APP_DIR/.git" ]]; then
  echo "Expected git repository at $APP_DIR" >&2
  exit 1
fi

cd "$APP_DIR"
git pull --ff-only

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

install -m 644 deploy/namecheap-dynamicdns.service /etc/systemd/system/namecheap-dynamicdns.service
install -m 644 deploy/namecheap-dynamicdns.timer /etc/systemd/system/namecheap-dynamicdns.timer
systemctl daemon-reload
systemctl enable --now namecheap-dynamicdns.timer

echo "Deployment complete."

