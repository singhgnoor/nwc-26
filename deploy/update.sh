#!/bin/sh
# Pull the latest content and rebuild site/. Run it as the nwc user:
#
#     sudo -u nwc sh /srv/nwc-26/deploy/update.sh
#
# The build is atomic: if it fails, the live site/ stays exactly as it was.
# The running server picks up the new site/ immediately; no restart is needed,
# unless server.py itself changed (this script tells you when).
set -eu

cd "$(dirname "$0")/.."

if [ "$(id -un)" != "nwc" ] && [ "${NWC_ALLOW_ANY_USER:-}" != "1" ]; then
    echo "Run this as the nwc user:  sudo -u nwc sh $(pwd)/deploy/update.sh" >&2
    exit 1
fi

before=$(git rev-parse HEAD)
git pull --ff-only
after=$(git rev-parse HEAD)

# Never --include-unconfirmed here: that is for local previews only.
python3 build_site.py

if [ "$before" != "$after" ] && git diff --name-only "$before" "$after" | grep -qx "server.py"; then
    echo ""
    echo "server.py changed. Restart the server:  sudo systemctl restart nwc"
fi
echo "Update done ($(git rev-parse --short HEAD))."
