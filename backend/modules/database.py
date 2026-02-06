"""
Database Module for iCapture System
Handles all MySQL database operations with connection pooling and error handling
"""

import pymysql
from pymysql import cursors
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import DATABASE_CONFIG, generate_violation_code
from utils.logger import get_logger

logger = get_logger('database')

class DatabaseManager:
    """MySQL database operations manager with connection pooling"""
    
    def __init__(self, config=None):
        """
        Initialize database manager
        
        Args:
            config: Database configuration dict (uses default if None)
        """
        self.config = config or DATABASE_CONFIG
        self.connection = None
        logger.info("DatabaseManager initialized")
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset=self.config['charset'],
                cursorclass=cursors.DictCursor
            )
            logger.info(f"Connected to database: {self.config['database']}")
            return True
        except pymysql.Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def execute(self, query, params=None, commit=True):
        """
        Execute SQL query with auto-retry
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            commit: Whether to commit transaction
        
        Returns:
            Cursor object or None on error
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.connection or not self.connection.open:
                    self.connect()
                
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    if commit:
                        self.connection.commit()
                    return cursor
            except pymysql.Error as e:
                logger.warning(f"Query execution failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Query failed after {max_retries} attempts: {query}")
                    return None
        return None
    
    # ============================================
    # Violation Operations
    # ============================================
    
    def insert_violation(self, violation_data):
        """
        Insert new violation record
        
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
            
            query = """
                INSERT INTO violations (
                    violation_code, plate_number, violation_type,
                    rider_image_path, plate_image_path,
                    camera_location, camera_id,
                    detection_confidence, ocr_confidence,
                    violation_datetime, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                violation_code,
                violation_data.get('plate_number'),
                violation_data['violation_type'],
                violation_data.get('rider_image_path'),
                violation_data.get('plate_image_path'),
                violation_data['camera_location'],
                violation_data['camera_id'],
                violation_data.get('detection_confidence'),
                violation_data.get('ocr_confidence'),
                datetime.now(),
                violation_data.get('notes')
            )
            
            cursor = self.execute(query, params)
            if cursor:
                violation_id = cursor.lastrowid
                logger.info(f"Violation inserted: {violation_code} (ID: {violation_id})")
                
                # Update camera violation count
                self.update_camera_stats(violation_data['camera_id'])
                
                return violation_id
            return None
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
    
    def check_recent_violation(self, plate_number, time_window=60):
        """
        Check if plate has recent violation (duplicate detection)
        
        Args:
            plate_number: License plate to check
            time_window: Time window in seconds
        
        Returns:
            bool: True if recent violation exists
        """
        try:
            query = """
                SELECT COUNT(*) as count FROM violations
                WHERE plate_number = %s
                AND violation_datetime >= DATE_SUB(NOW(), INTERVAL %s SECOND)
            """
            cursor = self.execute(query, (plate_number, time_window), commit=False)
            if cursor:
                result = cursor.fetchone()
                return result['count'] > 0
            return False
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
    
    def update_camera_stats(self, camera_id):
        """Update camera's last frame time and violation count"""
        try:
            query = """
                UPDATE cameras 
                SET last_frame_time = %s, 
                    total_violations = total_violations + 1
                WHERE camera_id = %s
            """
            self.execute(query, (datetime.now(), camera_id))
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
