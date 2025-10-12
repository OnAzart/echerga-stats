#!/bin/bash
set -e

echo "=== Echerga Stats - Docker Cron Setup ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with:"
    echo "  SUPABASE_URL=https://xxxxx.supabase.co"
    echo "  SUPABASE_KEY=your-key-here"
    exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -t echerga-stats .
echo "✓ Docker image built successfully"
echo ""

# Create log directory
LOG_FILE="/tmp/echerga-cron.log"
touch "$LOG_FILE"
echo "✓ Log file: $LOG_FILE"
echo ""

# Generate cron command
CRON_COMMAND="0 * * * * docker run --rm --env-file $SCRIPT_DIR/.env echerga-stats >> $LOG_FILE 2>&1"

echo "=== Cron Job Configuration ==="
echo ""
echo "Add this line to your crontab to run every hour:"
echo ""
echo "$CRON_COMMAND"
echo ""
echo "To install it automatically, run:"
echo "  (crontab -l 2>/dev/null; echo \"$CRON_COMMAND\") | crontab -"
echo ""
echo "Or edit crontab manually:"
echo "  crontab -e"
echo ""

# Ask if user wants to install now
read -p "Do you want to install this cron job now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup existing crontab
    if crontab -l &> /dev/null; then
        echo "Backing up existing crontab..."
        crontab -l > "$SCRIPT_DIR/crontab.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Add new cron job (avoiding duplicates)
    (crontab -l 2>/dev/null | grep -v "echerga-stats"; echo "$CRON_COMMAND") | crontab -

    echo "✓ Cron job installed successfully!"
    echo ""
    echo "To view installed cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To view logs:"
    echo "  tail -f $LOG_FILE"
else
    echo "Cron job not installed. You can install it manually later."
fi

echo ""
echo "=== Test Docker Run ==="
read -p "Do you want to test the Docker container now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running test..."
    docker run --rm --env-file "$SCRIPT_DIR/.env" echerga-stats
    echo ""
    echo "✓ Test completed!"
fi

echo ""
echo "=== Setup Complete ==="
echo "Schedule options (edit crontab if you want to change):"
echo "  Every hour:        0 * * * *"
echo "  Every 30 minutes:  */30 * * * *"
echo "  Every 2 hours:     0 */2 * * *"
echo "  Every 15 minutes:  */15 * * * *"