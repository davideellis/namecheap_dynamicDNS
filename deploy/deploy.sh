#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/namecheap_dynamicDNS"
VENV_DIR="$APP_DIR/.venv"
APP_USER="namecheap-ddns"
APP_GROUP="namecheap-ddns"
ENV_DIR="/etc/namecheap-dynamicdns"
ENV_FILE="$ENV_DIR/namecheap-dynamicdns.env"

if [[ ! -d "$APP_DIR/.git" ]]; then
  echo "Expected git repository at $APP_DIR" >&2
  exit 1
fi

cd "$APP_DIR"
git pull --ff-only

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

if ! id -u "$APP_USER" >/dev/null 2>&1; then
  useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
fi

install -d -m 755 "$ENV_DIR"
if [[ -f "$APP_DIR/.env" && ! -f "$ENV_FILE" ]]; then
  install -m 640 -o root -g "$APP_GROUP" "$APP_DIR/.env" "$ENV_FILE"
fi
if [[ ! -f "$ENV_FILE" ]]; then
  install -m 640 -o root -g "$APP_GROUP" .env.example "$ENV_FILE"
fi
chown root:"$APP_GROUP" "$ENV_FILE"
chmod 640 "$ENV_FILE"

install -m 644 deploy/namecheap-dynamicdns.service /etc/systemd/system/namecheap-dynamicdns.service
install -m 644 deploy/namecheap-dynamicdns.timer /etc/systemd/system/namecheap-dynamicdns.timer
systemctl daemon-reload

set -a
source "$ENV_FILE"
set +a

CACHE_FILE="${CACHE_FILE:-/var/lib/namecheap-dynamicdns/last_ip.txt}"
STATUS_FILE="${STATUS_FILE:-/var/lib/namecheap-dynamicdns/status.json}"
LOG_FILE="${LOG_FILE:-/var/log/namecheap-dynamicdns/updater.log}"

install -d -m 750 -o "$APP_USER" -g "$APP_GROUP" "$(dirname "$CACHE_FILE")"
install -d -m 750 -o "$APP_USER" -g "$APP_GROUP" "$(dirname "$STATUS_FILE")"
install -d -m 750 -o "$APP_USER" -g "$APP_GROUP" "$(dirname "$LOG_FILE")"

required_vars=(NAMECHEAP_DOMAIN NAMECHEAP_HOST NAMECHEAP_DDNS_PASSWORD)
for required_var in "${required_vars[@]}"; do
  if [[ -z "${!required_var:-}" ]]; then
    echo "Missing required setting in $ENV_FILE: $required_var" >&2
    exit 1
  fi
done

if [[ "$NAMECHEAP_DOMAIN" == replace-* || "$NAMECHEAP_DDNS_PASSWORD" == replace-* ]]; then
  echo "Update $ENV_FILE with real Namecheap values before deployment." >&2
  exit 1
fi

sudo -u "$APP_USER" --preserve-env=NAMECHEAP_DOMAIN,NAMECHEAP_HOST,NAMECHEAP_DDNS_PASSWORD,CHECK_INTERVAL_SECONDS,LOG_LEVEL,LOG_FILE,IP_DISCOVERY_TIMEOUT_SECONDS,CACHE_FILE,STATUS_FILE "$VENV_DIR/bin/namecheap-dynamicdns" --force-update
systemctl enable --now namecheap-dynamicdns.timer

echo "Deployment complete."
