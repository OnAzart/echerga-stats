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
            'id, title, country_id, lng, lat, order_id'
        ).order('order_id', desc=False, nullsfirst=False).order('title', desc=True).execute()
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
        include_comparison = request.args.get('compare', 'false').lower() == 'true'

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

        result = {
            'current': response.data
        }

        # If comparison requested, get data from one week ago
        if include_comparison:
            last_week_date = target_date - timedelta(days=7)
            last_week_next = last_week_date + timedelta(days=1)

            utc_start_prev = last_week_date - timedelta(hours=tz_offset_hours)
            utc_end_prev = last_week_next - timedelta(hours=tz_offset_hours)

            response_prev = supabase.table('queue_measurements').select(
                'created_at, wait_time, vehicle_in_active_queues_counts, is_paused, cancel_after'
            ).eq('checkpoint_id', checkpoint_id).gte(
                'created_at', utc_start_prev.isoformat()
            ).lt(
                'created_at', utc_end_prev.isoformat()
            ).order('created_at').execute()

            result['previous_week'] = response_prev.data

        return jsonify(result)
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


@app.route('/api/checkpoint/<int:checkpoint_id>/heatmap')
def get_checkpoint_heatmap(checkpoint_id):
    """Get heatmap data showing average wait times by day of week and hour"""
    try:
        # Get timezone offset from request (in minutes)
        timezone_offset = request.args.get('tz_offset', '0')
        tz_offset_hours = int(timezone_offset) / -60  # Convert to hours, invert sign

        # Get data from last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)

        response = supabase.table('queue_measurements').select(
            'created_at, wait_time'
        ).eq('checkpoint_id', checkpoint_id).gte(
            'created_at', thirty_days_ago.isoformat()
        ).execute()

        # Process data into day-of-week and hour buckets
        # Structure: {day_of_week: {hour: [wait_times]}}
        data_buckets = {}
        for i in range(7):  # 0=Monday, 6=Sunday
            data_buckets[i] = {}
            for h in range(24):
                data_buckets[i][h] = []

        for measurement in response.data:
            dt = datetime.fromisoformat(measurement['created_at'].replace('Z', '+00:00'))
            # Apply timezone offset to convert from UTC to local time
            local_dt = dt + timedelta(hours=tz_offset_hours)
            day_of_week = local_dt.weekday()  # 0=Monday, 6=Sunday
            hour = local_dt.hour
            wait_time = measurement['wait_time']

            if wait_time is not None:
                data_buckets[day_of_week][hour].append(wait_time)

        # Calculate averages
        heatmap_data = []
        for day in range(7):
            for hour in range(24):
                wait_times = data_buckets[day][hour]
                if wait_times:
                    avg_wait = sum(wait_times) / len(wait_times)
                    sample_size = len(wait_times)
                else:
                    avg_wait = None
                    sample_size = 0

                heatmap_data.append({
                    'day_of_week': day,
                    'hour': hour,
                    'avg_wait_time': avg_wait,
                    'sample_size': sample_size
                })

        return jsonify(heatmap_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
