"""
Violations API Routes for iCapture System
CRUD operations for violation records
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from modules.database import get_database
from utils.logger import get_logger

logger = get_logger('routes_violations')

violations_bp = Blueprint('violations', __name__, url_prefix='/api/violations')

@violations_bp.route('/', methods=['GET'])
def get_violations():
    """
    Get list of violations with optional filters
    Query params:
        - status: pending|verified|dismissed|issued
        - plate_number: partial match
        - date_from: YYYY-MM-DD
        - date_to: YYYY-MM-DD
        - location: camera location
        - type: no_helmet|nutshell_helmet
        - limit: max records (default 20)
        - offset: pagination offset (default 0)
    """
    try:
        db = get_database()
        
        # Build filters
        filters = {}
        
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('plate_number'):
            filters['plate_number'] = request.args.get('plate_number')
        
        if request.args.get('date_from'):
            filters['date_from'] = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        
        if request.args.get('date_to'):
            filters['date_to'] = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        
        if request.args.get('location'):
            filters['camera_location'] = request.args.get('location')
        
        if request.args.get('type'):
            filters['violation_type'] = request.args.get('type')
        
        # Pagination
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Fetch violations
        violations = db.get_violations(filters, limit, offset)
        
        # Convert datetime objects to strings for JSON serialization
        for v in violations:
            for key in ['violation_datetime', 'created_at', 'updated_at']:
                if key in v and v[key]:
                    v[key] = v[key].isoformat() if isinstance(v[key], datetime) else str(v[key])
        
        return jsonify({
            'success': True,
            'data': violations,
            'count': len(violations),
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        logger.error(f"Error fetching violations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@violations_bp.route('/<int:violation_id>', methods=['GET'])
def get_violation(violation_id):
    """Get single violation by ID"""
    try:
        db = get_database()
        violation = db.get_violation_by_id(violation_id)
        
        if not violation:
            return jsonify({'success': False, 'error': 'Violation not found'}), 404
        
        # Convert datetime objects
        for key in ['violation_datetime', 'created_at', 'updated_at']:
            if key in violation and violation[key]:
                violation[key] = violation[key].isoformat() if isinstance(violation[key], datetime) else str(violation[key])
        
        return jsonify({'success': True, 'data': violation}), 200
    except Exception as e:
        logger.error(f"Error fetching violation {violation_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@violations_bp.route('/<int:violation_id>', methods=['PUT'])
def update_violation(violation_id):
    """
    Update violation status and notes
    Body: {
        "status": "pending|verified|dismissed|issued",
        "notes": "optional notes"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'success': False, 'error': 'Status is required'}), 400
        
        db = get_database()
        success = db.update_violation_status(
            violation_id,
            data['status'],
            data.get('notes')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Violation updated'}), 200
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 500
    except Exception as e:
        logger.error(f"Error updating violation {violation_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@violations_bp.route('/search', methods=['GET'])
def search_violations():
    """
    Search violations by plate number
    Query param: q (search query)
    """
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query required'}), 400
        
        db = get_database()
        violations = db.get_violations({'plate_number': query}, limit=50)
        
        # Convert datetime objects
        for v in violations:
            for key in ['violation_datetime', 'created_at', 'updated_at']:
                if key in v and v[key]:
                    v[key] = v[key].isoformat() if isinstance(v[key], datetime) else str(v[key])
        
        return jsonify({
            'success': True,
            'data': violations,
            'count': len(violations),
            'query': query
        }), 200
    except Exception as e:
        logger.error(f"Error searching violations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@violations_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get violation statistics
    Query params:
        - date_from: YYYY-MM-DD
        - date_to: YYYY-MM-DD
    """
    try:
        db = get_database()
        
        date_from = None
        date_to = None
        
        if request.args.get('date_from'):
            date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        
        if request.args.get('date_to'):
            date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        
        stats = db.get_statistics(date_from, date_to)
        
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
