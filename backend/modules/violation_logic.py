"""
Violation Logic Module for iCapture System
Manages violation triggering, duplicate prevention, and multi-frame verification
"""

import time
from datetime import datetime, timedelta
from collections import deque
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import VIOLATION_CONFIG, generate_violation_code
from utils.logger import get_logger

logger = get_logger('violation_logic')

class ViolationManager:
    """
    Violation state machine with duplicate prevention and multi-frame verification
    """
    
    def __init__(self, db_manager, duplicate_window=60, consecutive_frames=3):
        """
        Initialize violation manager
        
        Args:
            db_manager: DatabaseManager instance
            duplicate_window: Time window in seconds for duplicate detection
            consecutive_frames: Number of consecutive detections required
        """
        self.db = db_manager
        self.duplicate_window = duplicate_window or VIOLATION_CONFIG['duplicate_window']
        self.consecutive_frames = consecutive_frames or VIOLATION_CONFIG['consecutive_frames']
        
        # Tracking for multi-frame verification
        self.detection_buffer = {}  # {plate_number: deque of timestamps}
        
        # Recent violations cache (plate_number: timestamp)
        self.recent_violations = {}
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'violations_logged': 0,
            'duplicates_prevented': 0
        }
        
        logger.info(f"ViolationManager initialized (duplicate_window: {duplicate_window}s, consecutive_frames: {consecutive_frames})")
    
    def _cleanup_old_records(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        cutoff_time = current_time - self.duplicate_window
        
        # Cleanup recent violations
        expired_plates = [
            plate for plate, timestamp in self.recent_violations.items()
            if timestamp < cutoff_time
        ]
        for plate in expired_plates:
            del self.recent_violations[plate]
        
        # Cleanup detection buffer
        for plate in list(self.detection_buffer.keys()):
            # Remove old timestamps
            timestamps = self.detection_buffer[plate]
            while timestamps and timestamps[0] < cutoff_time:
                timestamps.popleft()
            
            # Remove empty buffers
            if not timestamps:
                del self.detection_buffer[plate]
    
    def is_duplicate(self, plate_number):
        """
        Check if plate has recent violation
        
        Args:
            plate_number: License plate to check
        
        Returns:
            bool: True if duplicate
        """
        if not plate_number:
            return False
        
        # Check in-memory cache first (faster)
        if plate_number in self.recent_violations:
            timestamp = self.recent_violations[plate_number]
            if time.time() - timestamp < self.duplicate_window:
                return True
        
        # Check database for accuracy
        if self.db:
            is_dup = self.db.check_recent_violation(plate_number, self.duplicate_window)
            return is_dup
        
        return False
    
    def add_detection(self, plate_number):
        """
        Add detection to buffer for multi-frame verification
        
        Args:
            plate_number: Detected plate number
        
        Returns:
            bool: True if consecutive_frames threshold met
        """
        if not plate_number:
            return False
        
        current_time = time.time()
        
        # Initialize buffer if not exists
        if plate_number not in self.detection_buffer:
            self.detection_buffer[plate_number] = deque(maxlen=self.consecutive_frames)
        
        # Add detection
        self.detection_buffer[plate_number].append(current_time)
        
        # Check if we have enough consecutive detections
        if len(self.detection_buffer[plate_number]) >= self.consecutive_frames:
            # Verify they're actually consecutive (within reasonable time)
            timestamps = list(self.detection_buffer[plate_number])
            time_span = timestamps[-1] - timestamps[0]
            
            # Should be within 2-3 seconds for 3 consecutive frames at ~1 FPS processing
            if time_span < 5.0:
                return True
        
        return False
    
    def process_detection(self, detection_result, plate_result, camera_info):
        """
        Evaluate detection and decide whether to create violation
        
        Args:
            detection_result: dict from helmet detector with 'best_violation'
            plate_result: dict from plate recognizer with 'plate_number', 'confidence'
            camera_info: dict with 'camera_id', 'location'
        
        Returns:
            dict: {
                'should_log': bool,
                'reason': str,
                'violation_id': int or None,
                'violation_code': str or None
            }
        """
        self.stats['total_detections'] += 1
        
        # Cleanup old records periodically
        if self.stats['total_detections'] % 100 == 0:
            self._cleanup_old_records()
        
        # Check if there's a violation
        if not detection_result or not detection_result.get('has_violation'):
            return {
                'should_log': False,
                'reason': 'No violation detected',
                'violation_id': None,
                'violation_code': None
            }
        
        best_violation = detection_result.get('best_violation')
        plate_number = plate_result.get('plate_number')
        
        # For violations without plate, use a placeholder for tracking
        tracking_plate = plate_number or f"NO_PLATE_{camera_info['camera_id']}"
        
        # Multi-frame verification
        if not self.add_detection(tracking_plate):
            return {
                'should_log': False,
                'reason': f'Waiting for {self.consecutive_frames} consecutive detections',
                'violation_id': None,
                'violation_code': None
            }
        
        # Check for duplicate
        if plate_number and self.is_duplicate(plate_number):
            self.stats['duplicates_prevented'] += 1
            logger.info(f"Duplicate violation prevented: {plate_number}")
            return {
                'should_log': False,
                'reason': f'Duplicate (same plate within {self.duplicate_window}s)',
                'violation_id': None,
                'violation_code': None
            }
        
        # Log violation
        violation_code = generate_violation_code()
        
        # This will be populated by the main processing loop
        # Here we just return the decision
        return {
            'should_log': True,
            'reason': 'Valid violation detected',
            'violation_id': None,  # Will be set after DB insert
            'violation_code': violation_code,
            'detection_data': best_violation,
            'plate_data': plate_result,
            'camera_data': camera_info
        }
    
    def log_violation(self, violation_data):
        """
        Log violation to database and update cache
        
        Args:
            violation_data: dict with complete violation information
        
        Returns:
            int: Violation ID or None
        """
        try:
            # Insert to database
            violation_id = self.db.insert_violation(violation_data)
            
            if violation_id:
                # Update cache
                plate_number = violation_data.get('plate_number')
                if plate_number:
                    self.recent_violations[plate_number] = time.time()
                
                # Update stats
                self.stats['violations_logged'] += 1
                
                logger.info(f"Violation logged: {violation_data.get('violation_code')} (ID: {violation_id})")
                return violation_id
            else:
                logger.error("Failed to log violation to database")
                return None
        except Exception as e:
            logger.error(f"Error logging violation: {e}")
            return None
    
    def get_statistics(self):
        """Get violation manager statistics"""
        return {
            **self.stats,
            'active_detections': len(self.detection_buffer),
            'cached_violations': len(self.recent_violations)
        }
    
    def reset_statistics(self):
        """Reset statistics counters"""
        self.stats = {
            'total_detections': 0,
            'violations_logged': 0,
            'duplicates_prevented': 0
        }
        logger.info("Statistics reset")

# Singleton instance
_violation_manager = None

def get_violation_manager(db_manager):
    """Get or create violation manager singleton"""
    global _violation_manager
    if _violation_manager is None:
        _violation_manager = ViolationManager(db_manager)
    return _violation_manager

if __name__ == '__main__':
    # Test violation logic
    print("Testing Violation Logic Module...")
    
    from modules.database import DatabaseManager
    
    db = DatabaseManager()
    db.connect()
    
    vm = ViolationManager(db, duplicate_window=10, consecutive_frames=3)
    
    # Simulate detections
    test_plate = "ABC-1234"
    test_detection = {
        'has_violation': True,
        'best_violation': {
            'class_name': 'no_helmet',
            'confidence': 0.95,
            'bbox': [100, 100, 300, 300]
        }
    }
    test_plate_result = {
        'plate_number': test_plate,
        'confidence': 0.85
    }
    test_camera = {
        'camera_id': 'CAM-TEST-001',
        'location': 'Test Location'
    }
    
    # First detection
    result1 = vm.process_detection(test_detection, test_plate_result, test_camera)
    print(f"Detection 1: {result1['reason']}")
    
    # Second detection (same plate, should wait for consecutive)
    time.sleep(0.5)
    result2 = vm.process_detection(test_detection, test_plate_result, test_camera)
    print(f"Detection 2: {result2['reason']}")
    
    # Third detection (should trigger)
    time.sleep(0.5)
    result3 = vm.process_detection(test_detection, test_plate_result, test_camera)
    print(f"Detection 3: {result3['reason']}")
    print(f"Should log: {result3['should_log']}")
    
    # Fourth detection (should be duplicate)
    time.sleep(1)
    result4 = vm.process_detection(test_detection, test_plate_result, test_camera)
    print(f"Detection 4: {result4['reason']}")
    
    print(f"\nStatistics: {vm.get_statistics()}")
    
    db.disconnect()
