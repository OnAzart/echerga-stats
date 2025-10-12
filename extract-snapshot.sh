
#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Extracting echerga snapshot at $(date) ==="

# Extract snapshot from API
curl 'https://back.echerha.gov.ua/api/v4/workload/1' \
  -H 'accept: application/json' \
  -H 'accept-language: en-US,en;q=0.9,ru;q=0.8,uk;q=0.7' \
  -H 'content-type: application/json' \
  -H 'dnt: 1' \
  -H 'origin: https://echerha.gov.ua' \
  -H 'priority: u=1, i' \
  -H 'referer: https://echerha.gov.ua/' \
  -H 'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36' \
  -H 'x-client-locale: uk' \
  -H 'x-user-agent: UABorder/3.4.4 Web/1.1.0 User/guest' | jq '.' > echerga-snapshot.json

echo "✓ Snapshot saved to echerga-snapshot.json"

# Run Python ingestion script
echo ""
echo "=== Running ingestion script ==="
python3 ingest.py

echo ""
echo "=== Process completed at $(date) ==="


