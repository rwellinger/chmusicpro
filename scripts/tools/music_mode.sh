#!/bin/bash
echo "🎵 === MUSIC PRODUCTION MODE ==="
echo ""

# Check sudo access (will prompt for password if needed)
echo "Checking sudo access..."
if ! sudo -v; then
    echo "❌ Sudo access required. Exiting."
    exit 1
fi
echo ""

# 1. Stop Development
echo "[1/5] Stopping development services..."
colima stop 2>/dev/null
pkill -f "PyCharm"
pkill -f "python"
pkill -f "node"
echo "✅ Development stopped"

# 2. Disable macOS Background
echo "[2/5] Disabling macOS background processes..."
sudo mdutil -a -i off 2>&1 | grep -v "mdutil"
sudo tmutil disable
echo "✅ Spotlight indexing & Time Machine disabled"
echo "ℹ️  Note: Spotlight processes (mds*) still run but won't index"

# 3. Network (DISABLED - plugins need internet for license checks)
# Uncomment below if you don't need network during production:
# echo "[3/5] Disabling WiFi/Bluetooth..."
# networksetup -setairportpower en0 off
# blueutil -p 0 2>/dev/null
# echo "✅ Network disabled"

# 4. Kill unnecessary apps
echo "[3/5] Closing unnecessary apps..."
pkill -f "Slack"
pkill -f "Mail"
pkill -f "Messages"
echo "✅ Apps closed"

# 4. Free up memory
echo "[4/5] Clearing memory caches..."
sudo purge
echo "✅ Memory cleared"

# 5. Show stats
echo "[5/5] System status:"

# Calculate available memory (free + inactive + purgeable)
FREE_PAGES=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
INACTIVE_PAGES=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | tr -d '.')
PURGEABLE_PAGES=$(vm_stat | grep "Pages purgeable" | awk '{print $3}' | tr -d '.')
AVAILABLE_PAGES=$(echo "$FREE_PAGES + $INACTIVE_PAGES + $PURGEABLE_PAGES" | bc)
AVAILABLE_GB=$(echo "scale=2; $AVAILABLE_PAGES * 4096 / 1073741824" | bc)

echo "  Available RAM: ${AVAILABLE_GB} GB (free + inactive + purgeable)"
echo "  CPU Temp: $(osx-cpu-temp 2>/dev/null || echo 'N/A (install: brew install osx-cpu-temp)')"
echo ""
echo "🎹 READY FOR PRODUCTION!"
echo "⚠️  Don't forget:"
echo "   - Close browser tabs"
echo "   - Set DAW buffer size to 128 samples"
echo "   - Disable WiFi if recording (networksetup -setairportpower en0 off)"
echo ""
echo "Run './scripts/operation/dev_mode.sh' to restore settings."
