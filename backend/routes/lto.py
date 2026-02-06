"""
LTO Database Routes
API endpoints for LTO vehicle lookup and transaction history
"""

from flask import Blueprint, jsonify, request
from utils.logger import get_logger
from modules.database import get_database

logger = get_logger('lto_routes')
lto_bp = Blueprint('lto', __name__, url_prefix='/api/lto')

@lto_bp.route('/lookup/<plate_number>', methods=['GET'])
def lookup_vehicle(plate_number):
    """
    Look up vehicle information from LTO database
    Returns: owner info, registration status, document completeness
    """
    try:
        db = get_database()
        
        # Use the enhanced view
        query = """
            SELECT 
                plate_number,
                owner_name,
                owner_address,
                owner_contact,
                vehicle_make,
                vehicle_model,
                vehicle_color,
                registration_status,
                registration_expiry,
                is_fully_registered,
                has_or_cr,
                has_drivers_license,
                has_insurance,
                has_emission_test,
                total_violations,
                total_unpaid_fines,
                last_violation_date,
                validity_status,
                document_status
            FROM lto_owner_lookup
            WHERE plate_number = %s
        """
        
        cursor = db.execute(query, (plate_number,), commit=False)
        
        if cursor:
            result = cursor.fetchall()
        else:
            result = None
        
        if result and len(result) > 0:
            return jsonify({
                'success': True,
                'found': True,
                'data': result[0]
            })
        else:
            return jsonify({
                'success': True,
                'found': False,
                'message': f'No LTO record found for plate {plate_number}'
            })
            
    except Exception as e:
        logger.error(f"Error looking up LTO vehicle {plate_number}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lto_bp.route('/transactions/<plate_number>', methods=['GET'])
def get_transactions(plate_number):
    """
    Get transaction history for a vehicle
    """
    try:
        db = get_database()
        
        query = """
            SELECT 
                id,
                transaction_type,
                transaction_date,
                description,
                amount,
                payment_status,
                processed_by
            FROM lto_transactions
            WHERE plate_number = %s
            ORDER BY transaction_date DESC
            LIMIT 20
        """
        
        cursor = db.execute(query, (plate_number,), commit=False)
        results = cursor.fetchall() if cursor else []
        
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })
            
    except Exception as e:
        logger.error(f"Error fetching transactions for {plate_number}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lto_bp.route('/unpaid-violations', methods=['GET'])
def get_unpaid_violations():
    """
    Get all vehicles with unpaid fines
    """
    try:
        db = get_database()
        
        query = """
            SELECT 
                plate_number,
                owner_name,
                owner_contact,
                total_violations,
                total_unpaid_fines,
                last_violation_date,
                registration_status
            FROM lto_unpaid_violations
        """
        
        cursor = db.execute(query, commit=False)
        results = cursor.fetchall() if cursor else []
        
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })
            
    except Exception as e:
        logger.error(f"Error fetching unpaid violations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lto_bp.route('/incomplete-registrations', methods=['GET'])
def get_incomplete_registrations():
    """
    Get vehicles with incomplete registration documents
    """
    try:
        db = get_database()
        
        query = """
            SELECT 
                plate_number,
                owner_name,
                owner_contact,
                registration_status,
                missing_document
            FROM lto_incomplete_registrations
        """
        
        cursor = db.execute(query, commit=False)
        results = cursor.fetchall() if cursor else []
        
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results
        })
            
    except Exception as e:
        logger.error(f"Error fetching incomplete registrations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lto_bp.route('/stats', methods=['GET'])
def get_lto_stats():
    """
    Get summary statistics from LTO database
    """
    try:
        db = get_database()
        
        stats = {}
        
        # Total vehicles
        cursor = db.execute("SELECT COUNT(*) as total FROM lto_vehicles", commit=False)
        result = cursor.fetchall() if cursor else []
        stats['total_vehicles'] = result[0]['total'] if result else 0
        
        # Fully registered
        cursor = db.execute("SELECT COUNT(*) as total FROM lto_vehicles WHERE is_fully_registered = TRUE", commit=False)
        result = cursor.fetchall() if cursor else []
        stats['fully_registered'] = result[0]['total'] if result else 0
        
        # Incomplete papers
        cursor = db.execute("SELECT COUNT(*) as total FROM lto_vehicles WHERE is_fully_registered = FALSE", commit=False)
        result = cursor.fetchall() if cursor else []
        stats['incomplete_papers'] = result[0]['total'] if result else 0
        
        # With unpaid fines
        cursor = db.execute("SELECT COUNT(*) as total FROM lto_vehicles WHERE total_unpaid_fines > 0", commit=False)
        result = cursor.fetchall() if cursor else []
        stats['with_unpaid_fines'] = result[0]['total'] if result else 0
        
        # Total unpaid amount
        cursor = db.execute("SELECT SUM(total_unpaid_fines) as total FROM lto_vehicles", commit=False)
        result = cursor.fetchall() if cursor else []
        stats['total_unpaid_amount'] = float(result[0]['total']) if result and result[0]['total'] else 0.0
        
        return jsonify({
            'success': True,
            'data': stats
        })
            
    except Exception as e:
        logger.error(f"Error fetching LTO stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
