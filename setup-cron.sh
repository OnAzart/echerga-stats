#!/bin/bash
set -e

echo "=== Echerga Stats - Setup Script ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if ETL .env file exists
if [ ! -f "etl/.env" ]; then
    echo "Error: etl/.env file not found!"
    echo "Please create etl/.env file with:"
    echo "  SUPABASE_URL=https://xxxxx.supabase.co"
    echo "  SUPABASE_KEY=your-key-here"
    exit 1
fi

# Check if Dashboard .env file exists
if [ ! -f "dashboard/.env" ]; then
    echo "Warning: dashboard/.env file not found. Copying from example..."
    cp dashboard/.env.example dashboard/.env
    echo "Please edit dashboard/.env with your credentials"
fi

echo "=== Building Docker Images ==="
echo ""

# Build ETL image
echo "Building ETL service..."
docker build -t echerga-etl ./etl
echo "✓ ETL Docker image built successfully"
echo ""

# Build Dashboard image
echo "Building Dashboard service..."
docker build -t echerga-dashboard ./dashboard
echo "✓ Dashboard Docker image built successfully"
echo ""

# Create log directory
LOG_FILE="/tmp/echerga-cron.log"
touch "$LOG_FILE"
echo "✓ Log file: $LOG_FILE"
echo ""

# Generate cron command for ETL
CRON_COMMAND="0 * * * * docker run --rm --env-file $SCRIPT_DIR/etl/.env --dns 8.8.8.8 echerga-etl >> $LOG_FILE 2>&1"

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
echo "=== Test ETL Docker Run ==="
read -p "Do you want to test the ETL container now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running ETL test..."
    docker run --rm --env-file "$SCRIPT_DIR/etl/.env" --dns 8.8.8.8 echerga-etl
    echo ""
    echo "✓ ETL test completed!"
fi

echo ""
echo "=== Start Dashboard Service ==="
read -p "Do you want to start the dashboard now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting dashboard..."
    docker run -d --name echerga-dashboard --env-file "$SCRIPT_DIR/dashboard/.env" -p 5000:5000 --restart unless-stopped echerga-dashboard
    echo "✓ Dashboard started!"
    echo "Access it at: http://localhost:5000"
    echo ""
    echo "To stop: docker stop echerga-dashboard"
    echo "To view logs: docker logs -f echerga-dashboard"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "ETL Cron Schedule options (edit crontab if you want to change):"
echo "  Every hour:        0 * * * *"
echo "  Every 30 minutes:  */30 * * * *"
echo "  Every 2 hours:     0 */2 * * *"
echo "  Every 15 minutes:  */15 * * * *"
echo ""
echo "Dashboard:"
echo "  URL: http://localhost:5000"
echo "  Status: docker ps | grep echerga-dashboard"