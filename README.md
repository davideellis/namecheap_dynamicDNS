# Namecheap Dynamic DNS Updater

This project updates a single Namecheap A record from a Debian VM every 5 minutes. It is intended for home networks with a dynamic public IP address.

## What it does

- Reads configuration from a local `.env` file
- Discovers the current public IPv4 address using multiple fallback providers
- Updates one Namecheap host record through the Namecheap Dynamic DNS endpoint
- Skips unnecessary Namecheap updates when the public IP has not changed
- Writes a JSON status file for health checks and troubleshooting
- Logs to both stdout and an optional file
- Ships with `systemd` service and timer units for Debian deployment

## Important note about credentials

Namecheap's Dynamic DNS endpoint does **not** use the regular Namecheap API key and API username. It uses a **Dynamic DNS password** generated for the specific host record in the Namecheap dashboard.

If you were planning to use your API key and API user, keep them out of this project. They are not needed for the Dynamic DNS flow implemented here.

## Repository layout

```text
.
|-- .env.example
|-- deploy/
|   |-- deploy.sh
|   |-- namecheap-dynamicdns.service
|   `-- namecheap-dynamicdns.timer
|-- src/namecheap_dynamicdns/
|   |-- cli.py
|   |-- config.py
|   |-- ip_lookup.py
|   |-- logging_utils.py
|   `-- namecheap.py
`-- tests/
```

## Local development

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Create your local config

```bash
cp .env.example .env
```

Fill in these values:

```dotenv
NAMECHEAP_DOMAIN=example.com
NAMECHEAP_HOST=@
NAMECHEAP_DDNS_PASSWORD=replace-with-dynamic-dns-password
CHECK_INTERVAL_SECONDS=300
LOG_LEVEL=INFO
LOG_FILE=/var/log/namecheap-dynamicdns/updater.log
IP_DISCOVERY_TIMEOUT_SECONDS=10
CACHE_FILE=/var/lib/namecheap-dynamicdns/last_ip.txt
STATUS_FILE=/var/lib/namecheap-dynamicdns/status.json
```

### 3. Run once

```bash
namecheap-dynamicdns
```

### 4. Run in a loop

```bash
namecheap-dynamicdns --loop
```

The `--loop` mode is useful for manual testing, but the Debian deployment uses `systemd` timers instead.

Print the most recent updater status:

```bash
namecheap-dynamicdns --print-status
```

## How to get the Dynamic DNS password in Namecheap

1. Open your domain in Namecheap.
2. Go to the `Advanced DNS` tab.
3. Find the host record you want to update.
4. Enable `Dynamic DNS` for that host.
5. Copy the generated Dynamic DNS password into `.env`.

For a root domain A record, use `NAMECHEAP_HOST=@`.

## Debian deployment

These steps assume the Debian VM will host the updater at `/opt/namecheap_dynamicDNS`.

### 1. Install OS packages

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

### 2. Clone the repository

```bash
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/davideellis/namecheap_dynamicDNS.git
sudo chown -R "$USER":"$USER" /opt/namecheap_dynamicDNS
cd /opt/namecheap_dynamicDNS
```

### 3. Create the runtime config

```bash
sudo mkdir -p /etc/namecheap-dynamicdns
sudo cp .env.example /etc/namecheap-dynamicdns/namecheap-dynamicdns.env
sudo nano /etc/namecheap-dynamicdns/namecheap-dynamicdns.env
```

### 4. Deploy or refresh after a push

```bash
chmod +x deploy/deploy.sh
sudo ./deploy/deploy.sh
```

This script:

- pulls the latest commit
- rebuilds the virtual environment
- installs dependencies
- creates a dedicated `namecheap-ddns` service user
- installs the `systemd` unit files
- validates the runtime config and performs one forced update test
- enables the 5-minute timer

### 5. Verify the timer

```bash
systemctl status namecheap-dynamicdns.timer
systemctl list-timers --all | grep namecheap
journalctl -u namecheap-dynamicdns.service -n 50 --no-pager
```

## Manual commands

Run the updater once through the virtual environment:

```bash
set -a
source /etc/namecheap-dynamicdns/namecheap-dynamicdns.env
set +a
/opt/namecheap_dynamicDNS/.venv/bin/namecheap-dynamicdns --force-update
```

Trigger the systemd service immediately:

```bash
sudo systemctl start namecheap-dynamicdns.service
```

Show the latest status file:

```bash
sudo cat /var/lib/namecheap-dynamicdns/status.json
```

## Security

- the live environment file should live at `/etc/namecheap-dynamicdns/namecheap-dynamicdns.env`
- only store the Dynamic DNS password required for the host record
- do not store your Namecheap API key in this repo

## Testing

```bash
pytest
```
