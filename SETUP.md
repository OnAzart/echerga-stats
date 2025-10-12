# Echerga Border Crossing Statistics - Setup Guide

This project collects hourly statistics from the Ukrainian border crossing queue system (echerha.gov.ua).

## Architecture

- **extract-snapshot.sh**: Shell script that fetches data from the API and calls the ingestion script
- **ingest.py**: Python script that validates and inserts data into Supabase (uses `uv`)
- **schema.sql**: Database schema (two tables: static checkpoints + time-series measurements)
- **Dockerfile**: Containerized deployment with all dependencies
- **setup-cron.sh**: Automated script to build Docker image and configure cron

## Prerequisites

**Option A: Docker (Recommended)**
1. **Docker** installed
2. **Supabase account** with a project created

**Option B: Local Python**
1. **Python 3.7+** with pip and `uv`
2. **jq** (JSON processor)
3. **Supabase account** with a project created

## Setup Steps

---

## 🐳 Option A: Docker Setup (Recommended)

### 1. Set Up Supabase Database

1. Go to your Supabase project: https://supabase.com/dashboard
2. Navigate to SQL Editor
3. Copy and execute the SQL from `schema.sql`

### 2. Configure Environment Variables

Create a `.env` file in the project directory:

```bash
cp .env.example .env
# Edit .env with your credentials:
# SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
# SUPABASE_KEY=your-anon-or-service-role-key
```

Get credentials from: Supabase Dashboard → Settings → API

### 3. Run Setup Script

```bash
./setup-cron.sh
```

This will:
- Build the Docker image
- Test the container
- Optionally install the cron job automatically

**That's it!** The script handles everything.

### Manual Docker Commands

```bash
# Build image
docker build -t echerga-stats .

# Test run
docker run --rm --env-file .env echerga-stats

# Manual cron setup
crontab -e
# Add: 0 * * * * docker run --rm --env-file /full/path/to/.env echerga-stats >> /tmp/echerga-cron.log 2>&1
```

### Monitor Logs

```bash
tail -f /tmp/echerga-cron.log
```

---

## 🐍 Option B: Local Python Setup

### 1. Install Dependencies

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv pip install -r requirements.txt

# Install jq (if not already installed)
# macOS:
brew install jq
# Linux:
sudo apt-get install jq
```

### 2. Set Up Supabase Database

Same as Docker option - run `schema.sql` in Supabase SQL Editor.

### 3. Configure Environment Variables

```bash
# Add to ~/.zshrc or ~/.bashrc
export SUPABASE_URL='https://xxxxxxxxxxxxx.supabase.co'
export SUPABASE_KEY='your-anon-or-service-role-key'
source ~/.zshrc
```

### 4. Test Manual Execution

```bash
./extract-snapshot.sh
```

### 5. Set Up Cron Job

```bash
crontab -e
# Add:
0 * * * * cd /full/path/to/echerga-stats && ./extract-snapshot.sh >> /tmp/echerga-cron.log 2>&1
```

---

## Cron Schedule Options

```bash
0 * * * *      # Every hour at minute 0
*/30 * * * *   # Every 30 minutes
*/15 * * * *   # Every 15 minutes
0 */2 * * *    # Every 2 hours
5 * * * *      # Every hour at minute 5
```

## Database Schema

### Table: `checkpoints` (Static Data)

Stores border checkpoint metadata:
- `id` - Checkpoint ID
- `title` - Checkpoint name (e.g., "Ужгород – Вишнє Нємецьке")
- `country_id` - Country ID
- `lng`, `lat` - GPS coordinates
- `for_vehicle_type`, `queue_flow`, `cancel_after` - Queue parameters

### Table: `queue_measurements` (Time-Series Data)

Stores hourly measurements:
- `checkpoint_id` - Reference to checkpoint
- `is_paused` - Queue status
- `wait_time` - Waiting time in seconds
- `vehicle_in_active_queues_counts` - Number of vehicles
- `measured_at` - Timestamp of measurement

### View: `latest_queue_status`

Convenient view showing the most recent status for each checkpoint.

## Usage Examples

### Query Latest Status

```sql
SELECT * FROM latest_queue_status
WHERE vehicle_in_active_queues_counts > 50
ORDER BY wait_time DESC;
```

### Historical Trends for a Checkpoint

```sql
SELECT
    DATE_TRUNC('hour', measured_at) as hour,
    AVG(wait_time) as avg_wait_time,
    AVG(vehicle_in_active_queues_counts) as avg_vehicles
FROM queue_measurements
WHERE checkpoint_id = 14  -- Ужгород – Вишнє Нємецьке
    AND measured_at >= NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;
```

### Busiest Checkpoints (Last 24 Hours)

```sql
SELECT
    c.title,
    AVG(qm.wait_time) as avg_wait_time,
    AVG(qm.vehicle_in_active_queues_counts) as avg_vehicles
FROM checkpoints c
JOIN queue_measurements qm ON c.id = qm.checkpoint_id
WHERE qm.measured_at >= NOW() - INTERVAL '24 hours'
GROUP BY c.id, c.title
ORDER BY avg_wait_time DESC
LIMIT 10;
```

## Troubleshooting

### Python Script Fails

```bash
# Check Python version
python3 --version

# Reinstall dependencies
pip install --upgrade supabase
```

### Environment Variables Not Found

```bash
# Test in current shell
echo $SUPABASE_URL

# For cron, explicitly set in crontab:
0 * * * * export SUPABASE_URL='https://xxx.supabase.co' && export SUPABASE_KEY='xxx' && cd /Users/nazartutyn/Desktop/mine/echerga-stats && /bin/bash extract-snapshot.sh >> /tmp/echerga-cron.log 2>&1
```

### File Freshness Check Fails

The script checks if the snapshot file is less than 60 seconds old. If the API call fails, the ingestion won't run. Check:

```bash
# Test API manually
curl 'https://back.echerha.gov.ua/api/v4/workload/1'
```

## Monitoring

```bash
# View recent logs
tail -50 /tmp/echerga-cron.log

# Count measurements collected
echo "SELECT COUNT(*) FROM queue_measurements;" | psql $DATABASE_URL

# Check latest measurement time
echo "SELECT MAX(measured_at) FROM queue_measurements;" | psql $DATABASE_URL
```

## License

Data is sourced from the official Ukrainian government border queue system (echerha.gov.ua).
