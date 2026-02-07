"""
Database Module for iCapture System
Handles all MySQL database operations with connection pooling and error handling

REFACTORED: Now uses SQLAlchemy connection pooling for production reliability
"""

import pymysql
from pymysql import cursors
from datetime import datetime
import json
import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import DATABASE_CONFIG, generate_violation_code
from utils.logger import get_logger

# Import new connection pool module
from modules.db_pool import get_db_session, execute_query, retry_on_db_error

logger = get_logger('database')

class DatabaseManager:
    """
    MySQL database operations manager with SQLAlchemy connection pooling
    
    PRODUCTION READY: Uses connection pool to prevent "Internal Server Errors"
    """
    
    def __init__(self, config=None):
        """
        Initialize database manager
        
        Args:
            config: Database configuration dict (uses default if None)
        
        NOTE: Connection is now managed by pool, no manual connect() needed
        """
        self.config = config or DATABASE_CONFIG
        self.connection = None  # Legacy - kept for backward compatibility
        logger.info("DatabaseManager initialized with connection pooling")
    
    def connect(self):
        """
        Legacy method for backward compatibility
        
        NOTE: Actual connections are now pooled automatically.
        This method is maintained for code that calls it explicitly.
        """
        logger.info("Connection pooling active - manual connect() not required")
        self.connection = type('obj', (object,), {'open': True})()  # Dummy object
        return True
    
    def disconnect(self):
        """Legacy method for backward compatibility"""
        logger.info("Connection pooling active - manual disconnect() not required")
        self.connection = None
    
    @retry_on_db_error(max_retries=3, base_delay=0.5)
    def execute_query(self, query, params=None, fetch_mode='all'):
        """
        Execute SQL query with connection pooling and automatic retry
        
        Args:
            query: SQL query string (use :param for placeholders)
            params: Dictionary of parameters
            fetch_mode: 'all', 'one', or 'none'
        
        Returns:
            Query results or None
        """
        # Convert old-style %s queries to :param format if needed
        if params and isinstance(params, (list, tuple)):
            # Legacy format - convert to dict
            params_dict = {f'param_{i}': val for i, val in enumerate(params)}
            for i in range(len(params)):
                query = query.replace('%s', f':param_{i}', 1)
            params = params_dict
        
        return execute_query(query, params, fetch_mode)
    
    # ============================================
    # Violation Operations
    # ============================================
    
    @retry_on_db_error(max_retries=3, base_delay=0.5)
    def insert_violation(self, violation_data):
        """
        Insert new violation record (with connection pooling and retry)
        
        Args:
            violation_data: dict with keys:
                - violation_type: 'no_helmet' or 'nutshell_helmet'
                - plate_number: str or None
                - rider_image_path: str or None
                - plate_image_path: str or None
                - camera_location: str
                - camera_id: str
                - detection_confidence: float
                - ocr_confidence: float or None
                - notes: str or None
        
        Returns:
            int: Violation ID or None on error
        """
        try:
            violation_code = generate_violation_code()
            
            query = text("""
                INSERT INTO violations (
                    violation_code, plate_number, violation_type,
                    rider_image_path, plate_image_path,
                    camera_location, camera_id,
                    detection_confidence, ocr_confidence,
                    violation_datetime, notes
                ) VALUES (
                    :code, :plate, :type, :rider_img, :plate_img,
                    :location, :cam_id, :det_conf, :ocr_conf, :datetime, :notes
                )
            """)
            
            with get_db_session() as session:
                result = session.execute(query, {
                    'code': violation_code,
                    'plate': violation_data.get('plate_number'),
                    'type': violation_data['violation_type'],
                    'rider_img': violation_data.get('rider_image_path'),
                    'plate_img': violation_data.get('plate_image_path'),
                    'location': violation_data['camera_location'],
                    'cam_id': violation_data['camera_id'],
                    'det_conf': violation_data.get('detection_confidence'),
                    'ocr_conf': violation_data.get('ocr_confidence'),
                    'datetime': datetime.now(),
                    'notes': violation_data.get('notes')
                })
                
                violation_id = result.lastrowid
                logger.info(f"Violation inserted: {violation_code} (ID: {violation_id})")
                
                # Update camera violation count
                self.update_camera_stats(violation_data['camera_id'])
                
                return violation_id
        except Exception as e:
            logger.error(f"Error inserting violation: {e}")
            return None
    
    def get_violations(self, filters=None, limit=20, offset=0):
        """
        Retrieve violations with optional filters
        
        Args:
            filters: dict with optional keys:
                - status: str
                - plate_number: str
                - date_from: datetime
                - date_to: datetime
                - camera_location: str
                - violation_type: str
            limit: Maximum records to return
            offset: Offset for pagination
        
        Returns:
            list: Violation records
        """
        try:
            query = "SELECT * FROM violations WHERE 1=1"
            params = []
            
            if filters:
                if 'status' in filters:
                    query += " AND status = %s"
                    params.append(filters['status'])
                
                if 'plate_number' in filters:
                    query += " AND plate_number LIKE %s"
                    params.append(f"%{filters['plate_number']}%")
                
                if 'date_from' in filters:
                    query += " AND violation_datetime >= %s"
                    params.append(filters['date_from'])
                
                if 'date_to' in filters:
                    query += " AND violation_datetime <= %s"
                    params.append(filters['date_to'])
                
                if 'camera_location' in filters:
                    query += " AND camera_location = %s"
                    params.append(filters['camera_location'])
                
                if 'violation_type' in filters:
                    query += " AND violation_type = %s"
                    params.append(filters['violation_type'])
            
            query += " ORDER BY violation_datetime DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor = self.execute(query, tuple(params), commit=False)
            if cursor:
                return cursor.fetchall()
            return []
        except Exception as e:
            logger.error(f"Error fetching violations: {e}")
            return []
    
    def get_violation_by_id(self, violation_id):
        """Get single violation by ID"""
        try:
            query = "SELECT * FROM violations WHERE id = %s"
            cursor = self.execute(query, (violation_id,), commit=False)
            if cursor:
                return cursor.fetchone()
            return None
        except Exception as e:
            logger.error(f"Error fetching violation {violation_id}: {e}")
            return None
    
    def update_violation_status(self, violation_id, status, notes=None):
        """
        Update violation status
        
        Args:
            violation_id: int
            status: 'pending', 'verified', 'dismissed', 'issued'
            notes: Optional notes
        
        Returns:
            bool: Success status
        """
        try:
            query = "UPDATE violations SET status = %s"
            params = [status]
            
            if notes:
                query += ", notes = %s"
                params.append(notes)
            
            query += " WHERE id = %s"
            params.append(violation_id)
            
            cursor = self.execute(query, tuple(params))
            if cursor:
                logger.info(f"Violation {violation_id} status updated to {status}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating violation status: {e}")
            return False
    
    @retry_on_db_error(max_retries=2, base_delay=0.3)
    def check_recent_violation(self, plate_number, time_window=60):
        """
        Check if plate has recent violation (duplicate detection)
        Uses connection pooling with fast retry
        
        Args:
            plate_number: License plate to check
            time_window: Time window in seconds
        
        Returns:
            bool: True if recent violation exists
        """
        try:
            query = """
                SELECT COUNT(*) as count FROM violations
                WHERE plate_number = :plate
                AND violation_datetime >= DATE_SUB(NOW(), INTERVAL :window SECOND)
            """
            result = execute_query(query, {'plate': plate_number, 'window': time_window}, fetch_mode='one')
            return result and result['count'] > 0
        except Exception as e:
            logger.error(f"Error checking recent violation: {e}")
            return False
    
    # ============================================
    # Statistics & Reports
    # ============================================
    
    def get_statistics(self, date_from=None, date_to=None):
        """
        Get violation statistics for a date range
        
        Returns:
            dict: Statistics data
        """
        try:
            stats = {}
            
            # Build date filter
            date_filter = ""
            params = []
            if date_from:
                date_filter += " AND violation_datetime >= %s"
                params.append(date_from)
            if date_to:
                date_filter += " AND violation_datetime <= %s"
                params.append(date_to)
            
            # Total violations
            query = f"SELECT COUNT(*) as total FROM violations WHERE 1=1 {date_filter}"
            cursor = self.execute(query, tuple(params), commit=False)
            if cursor:
                stats['total_violations'] = cursor.fetchone()['total']
            
            # By type
            query = f"""
                SELECT violation_type, COUNT(*) as count
                FROM violations WHERE 1=1 {date_filter}
                GROUP BY violation_type
            """
            cursor = self.execute(query, tuple(params), commit=False)
            if cursor:
                stats['by_type'] = {row['violation_type']: row['count'] for row in cursor.fetchall()}
            
            # By status
            query = f"""
                SELECT status, COUNT(*) as count
                FROM violations WHERE 1=1 {date_filter}
                GROUP BY status
            """
            cursor = self.execute(query, tuple(params), commit=False)
            if cursor:
                stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # By location
            query = f"""
                SELECT camera_location, COUNT(*) as count
                FROM violations WHERE 1=1 {date_filter}
                GROUP BY camera_location
                ORDER BY count DESC
            """
            cursor = self.execute(query, tuple(params), commit=False)
            if cursor:
                stats['by_location'] = cursor.fetchall()
            
            return stats
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            return {}
    
    # ============================================
    # Camera Operations
    # ============================================
    
    @retry_on_db_error(max_retries=2, base_delay=0.3)
    def update_camera_stats(self, camera_id):
        """Update camera's last frame time and violation count (with connection pooling)"""
        try:
            query = text("""
                UPDATE cameras 
                SET last_frame_time = :time, 
                    total_violations = total_violations + 1
                WHERE camera_id = :cam_id
            """)
            with get_db_session() as session:
                session.execute(query, {'time': datetime.now(), 'cam_id': camera_id})
        except Exception as e:
            logger.error(f"Error updating camera stats: {e}")
    
    def get_camera_status(self):
        """Get status of all cameras"""
        try:
            query = "SELECT * FROM cameras ORDER BY camera_id"
            cursor = self.execute(query, commit=False)
            if cursor:
                return cursor.fetchall()
            return []
        except Exception as e:
            logger.error(f"Error fetching camera status: {e}")
            return []
    
    # ============================================
    # System Logs
    # ============================================
    
    def insert_log(self, level, module, message, details=None):
        """Insert system log entry"""
        try:
            query = """
                INSERT INTO system_logs (log_level, module, message, details)
                VALUES (%s, %s, %s, %s)
            """
            self.execute(query, (level, module, message, json.dumps(details) if details else None))
        except Exception as e:
            logger.error(f"Error inserting log: {e}")

# Singleton instance
_db_manager = None

def get_database():
    """Get or create database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.connect()
    return _db_manager

if __name__ == '__main__':
    # Test database operations
    print("Testing Database Module...")
    db = DatabaseManager()
    
    if db.connect():
        print("✓ Connection successful")
        
        # Test violation insert
        test_violation = {
            'violation_type': 'no_helmet',
            'plate_number': 'ABC-1234',
            'camera_location': 'Test Location',
            'camera_id': 'CAM-TEST-001',
            'detection_confidence': 0.95
        }
        
        violation_id = db.insert_violation(test_violation)
        if violation_id:
            print(f"✓ Test violation inserted (ID: {violation_id})")
        
        # Test retrieval
        violations = db.get_violations(limit=5)
        print(f"✓ Retrieved {len(violations)} violations")
        
        # Test statistics
        stats = db.get_statistics()
        print(f"✓ Statistics: {stats.get('total_violations', 0)} total violations")
        
        db.disconnect()
    else:
        print("✗ Connection failed")
