#!/usr/bin/env python3
"""
Ingest echerga border crossing data into Supabase database.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed. Run: pip install supabase")
    sys.exit(1)


def check_file_freshness(file_path: str, max_age_seconds: int = 60) -> bool:
    """Check if file was modified within the last max_age_seconds."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return False

    file_mtime = os.path.getmtime(file_path)
    current_time = time.time()
    age_seconds = current_time - file_mtime

    if age_seconds > max_age_seconds:
        print(f"Warning: File is {age_seconds:.0f} seconds old (max: {max_age_seconds})")
        return False

    print(f"✓ File is fresh ({age_seconds:.0f} seconds old)")
    return True


def load_json_data(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)


def get_supabase_client() -> Client:
    """Initialize Supabase client from environment variables."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        print("Example:")
        print("  export SUPABASE_URL='https://xxxxx.supabase.co'")
        print("  export SUPABASE_KEY='your-anon-key'")
        sys.exit(1)

    print(f"Debug: Connecting to {supabase_url[:30]}...")

    return create_client(supabase_url, supabase_key)



def upsert_checkpoints(supabase: Client, data: List[Dict[str, Any]], max_retries: int = 3) -> int:
    """Upsert checkpoint data (static fields) with retry logic."""
    checkpoints = []

    for item in data:
        checkpoint = {
            "id": item["id"],
            "title": item["title"],
            "tooltip": item.get("tooltip"),
            "country_id": item["country_id"],
            "for_vehicle_type": item["for_vehicle_type"],
            "queue_flow": item["queue_flow"],
            "lng": item["lng"],
            "lat": item["lat"]
        }
        checkpoints.append(checkpoint)

    for attempt in range(max_retries):
        try:
            response = supabase.table("checkpoints").upsert(
                checkpoints,
                on_conflict="id"
            ).execute()
            print(f"✓ Upserted {len(checkpoints)} checkpoints")
            return len(checkpoints)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s due to: {e}")
                time.sleep(wait_time)
            else:
                print(f"Error upserting checkpoints after {max_retries} attempts: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)


def insert_queue_measurements(supabase: Client, data: List[Dict[str, Any]], measured_at: datetime) -> int:
    """Insert queue measurement data (dynamic fields)."""
    measurements = []

    for item in data:
        measurement = {
            "checkpoint_id": item["id"],
            "is_paused": item["is_paused"],
            "cancel_after": item["cancel_after"],
            "wait_time": item["wait_time"],
            "vehicle_in_active_queues_counts": item["vehicle_in_active_queues_counts"]
        }
        measurements.append(measurement)

    try:
        response = supabase.table("queue_measurements").insert(measurements).execute()
        print(f"✓ Inserted {len(measurements)} queue measurements")
        return len(measurements)
    except Exception as e:
        print(f"Error inserting queue measurements: {e}")
        sys.exit(1)


def main():
    """Main ingestion workflow."""
    # Configuration
    snapshot_file = "echerga-snapshot.json"
    max_age_seconds = 900

    print(f"=== Echerga Data Ingestion Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    # Check file freshness
    if not check_file_freshness(snapshot_file, max_age_seconds):
        print("Aborting: File is too old or doesn't exist")
        sys.exit(1)

    # Load data
    print(f"Loading data from {snapshot_file}...")
    json_data = load_json_data(snapshot_file)

    if "data" not in json_data:
        print("Error: JSON file does not contain 'data' field")
        sys.exit(1)

    data_items = json_data["data"]
    print(f"✓ Loaded {len(data_items)} border crossing entries")

    # Initialize Supabase client
    print("Connecting to Supabase...")
    supabase = get_supabase_client()
    print("✓ Connected to Supabase")

    # Get measurement timestamp from file modification time
    file_mtime = os.path.getmtime(snapshot_file)
    measured_at = datetime.fromtimestamp(file_mtime, tz=timezone.utc)
    print(f"Measurement timestamp: {measured_at.isoformat()}")

    # Upsert checkpoints (static data)
    print("\nUpserting checkpoint data...")
    upsert_checkpoints(supabase, data_items)

    # Insert queue measurements (dynamic data)
    print("\nInserting queue measurements...")
    insert_queue_measurements(supabase, data_items, measured_at)

    print(f"\n=== Ingestion Completed Successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")


if __name__ == "__main__":
    main()

    # supabase = get_supabase_client()
    # print(supabase.table("countries").select('*').execute())
