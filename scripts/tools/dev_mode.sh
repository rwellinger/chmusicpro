#!/bin/bash
echo "💻 === DEVELOPMENT MODE ==="
echo ""

# Check sudo access (will prompt for password if needed)
echo "Checking sudo access..."
if ! sudo -v; then
    echo "❌ Sudo access required. Exiting."
    exit 1
fi
echo ""

# Restore macOS services
echo "[1/3] Enabling macOS background processes..."
sudo mdutil -a -i on
sudo tmutil enable
echo "✅ Spotlight & Time Machine enabled"

# Restore network (if disabled)
echo "[2/3] Enabling network..."
networksetup -setairportpower en0 on
blueutil -p 1 2>/dev/null
echo "✅ Network enabled"

# Start Colima
echo "[3/3] Starting Colima..."
colima start
echo "✅ Colima started"

echo ""
echo "🚀 READY FOR DEVELOPMENT!"
