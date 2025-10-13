#!/usr/bin/env python3
"""
Echerga Stats Dashboard - Beautiful UI for viewing border crossing statistics
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(supabase_url, supabase_key)


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/checkpoints')
def get_checkpoints():
    """Get all checkpoints"""
    try:
        response = supabase.table('checkpoints').select(
            'id, title, country_id, lng, lat'
        ).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/checkpoint/<int:checkpoint_id>/day/<date>')
def get_checkpoint_day_data(checkpoint_id, date):
    """Get hourly data for a specific checkpoint on a specific day"""
    try:
        # Parse date (YYYY-MM-DD format) and get timezone offset from request
        timezone_offset = request.args.get('tz_offset', '0')  # minutes
        tz_offset_hours = int(timezone_offset) / -60  # Convert to hours, invert sign

        target_date = datetime.strptime(date, '%Y-%m-%d')
        next_day = target_date + timedelta(days=1)

        # Adjust for timezone - convert local date to UTC range
        utc_start = target_date - timedelta(hours=tz_offset_hours)
        utc_end = next_day - timedelta(hours=tz_offset_hours)

        # Query measurements for the day in UTC
        response = supabase.table('queue_measurements').select(
            'created_at, wait_time, vehicle_in_active_queues_counts, is_paused, cancel_after'
        ).eq('checkpoint_id', checkpoint_id).gte(
            'created_at', utc_start.isoformat()
        ).lt(
            'created_at', utc_end.isoformat()
        ).order('created_at').execute()

        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/latest')
def get_latest_status():
    """Get latest status for all checkpoints"""
    try:
        response = supabase.table('latest_queue_status').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/countries')
def get_countries():
    """Get all countries"""
    try:
        response = supabase.table('countries').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
