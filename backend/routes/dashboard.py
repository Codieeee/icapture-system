"""
Dashboard API Routes for iCapture System
Real-time statistics and monitoring data
"""

from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from modules.database import get_database
from utils.logger import get_logger

logger = get_logger('routes_dashboard')

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        db = get_database()
        
        # Today's date range
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Get today's statistics
        today_stats = db.get_statistics(today_start, today_end)
        
        # Get all-time statistics
        all_stats = db.get_statistics()
        
        # Get camera status
        cameras = db.get_camera_status()
        active_cameras = sum(1 for cam in cameras if cam['status'] == 'active')
        
        # Get pending violations count
        pending_violations = db.get_violations({'status': 'pending'}, limit=1000)
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'total_violations': today_stats.get('total_violations', 0),
                    'no_helmet': today_stats.get('by_type', {}).get('no_helmet', 0),
                    'nutshell_helmet': today_stats.get('by_type', {}).get('nutshell_helmet', 0),
                    'pending': today_stats.get('by_status', {}).get('pending', 0),
                    'verified': today_stats.get('by_status', {}).get('verified', 0)
                },
                'all_time': {
                    'total_violations': all_stats.get('total_violations', 0)
                },
                'cameras': {
                    'total': len(cameras),
                    'active': active_cameras,
                    'inactive': len(cameras) - active_cameras
                },
                'pending_count': len(pending_violations)
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/recent', methods=['GET'])
def get_recent_violations():
    """Get most recent violations for live monitoring"""
    try:
        db = get_database()
        violations = db.get_violations(limit=20, offset=0)
        
        # Convert datetime objects
        for v in violations:
            for key in ['violation_datetime', 'created_at']:
                if key in v and v[key]:
                    v[key] = v[key].isoformat() if isinstance(v[key], datetime) else str(v[key])
        
        return jsonify({
            'success': True,
            'data': violations,
            'count': len(violations)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching recent violations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/hourly', methods=['GET'])
def get_hourly_distribution():
    """Get hourly violation distribution for today"""
    try:
        db = get_database()
        
        # Get today's violations
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        violations = db.get_violations({'date_from': today_start}, limit=1000)
        
        # Group by hour
        hourly_data = {str(i): 0 for i in range(24)}
        
        for v in violations:
            if v.get('violation_datetime'):
                hour = v['violation_datetime'].hour
                hourly_data[str(hour)] += 1
        
        return jsonify({
            'success': True,
            'data': hourly_data
        }), 200
    except Exception as e:
        logger.error(f"Error fetching hourly data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
