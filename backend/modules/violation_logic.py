"""
Violation Logic Module - Clean Architecture with SOLID Principles
Implements Strategy Pattern for extensible violation detection

PRODUCTION READY: Easy to add new violation types (e.g., double riders, speeding)
"""

import time
from abc import ABC, abstractmethod
from collections import deque
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import VIOLATION_CONFIG, generate_violation_code
from utils.logger import get_logger

logger = get_logger('violation_logic')

# ============================================
# Domain Models
# ============================================

@dataclass
class Detection:
    """Value object representing a detection event"""
    violation_type: str
    confidence: float
    bbox: tuple
    timestamp: float
    plate_number: Optional[str] = None
    ocr_confidence: float = 0.0
    
    @property
    def has_plate(self) -> bool:
        return self.plate_number is not None


# ============================================
# Abstract Rules (Strategy Pattern)
# ============================================

class ViolationRule(ABC):
    """
    Abstract base class for violation rules
    
    SOLID: Open/Closed Principle - Open for extension, closed for modification
    """
    
    @abstractmethod
    def evaluate(self, detection: Detection) -> bool:
        """
        Evaluate if detection violates this rule
        
        Args:
            detection: Detection event
        
        Returns:
            True if violation detected
        """
        pass
    
    @abstractmethod
    def get_violation_type(self) -> str:
        """Get the violation type name"""
        pass


class NoHelmetRule(ViolationRule):
    """Rule for detecting riders without helmets"""
    
    def __init__(self, min_confidence: float = 0.6):
        self.min_confidence = min_confidence
    
    def evaluate(self, detection: Detection) -> bool:
        return (
            detection.violation_type == 'no_helmet' and
            detection.confidence >= self.min_confidence
        )
    
    def get_violation_type(self) -> str:
        return 'no_helmet'


class NutshellHelmetRule(ViolationRule):
    """Rule for detecting riders with inadequate (nutshell) helmets"""
    
    def __init__(self, min_confidence: float = 0.6):
        self.min_confidence = min_confidence
    
    def evaluate(self, detection: Detection) -> bool:
        return (
            detection.violation_type == 'nutshell_helmet' and
            detection.confidence >= self.min_confidence
        )
    
    def get_violation_type(self) -> str:
        return 'nutshell_helmet'


# FUTURE: Easy to add new rules!
class DoubleRiderRule(ViolationRule):
    """
    Rule for detecting more than one rider on a motorcycle
    
    NOTE: Not yet implemented in detector, but architecture supports it
    """
    
    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
    
    def evaluate(self, detection: Detection) -> bool:
        return (
            detection.violation_type == 'double_rider' and
            detection.confidence >= self.min_confidence
        )
    
    def get_violation_type(self) -> str:
        return 'double_rider'


# ============================================
# Verification Components
# ============================================

class ConsecutiveFrameVerifier:
    """
    Verifies detections across consecutive frames to reduce false positives
    
    SOLID: Single Responsibility - Only handles frame-based verification
    """
    
    def __init__(self, required_frames: int = 3, time_window: float = 5.0):
        """
        Args:
            required_frames: Number of consecutive detections required
            time_window: Maximum time window for consecutive detections (seconds)
        """
        self.required_frames = required_frames
        self.time_window = time_window
        self.detection_buffer: Dict[str, deque] = {}
        
        logger.info(f"ConsecutiveFrameVerifier initialized ({required_frames} frames, {time_window}s window)")
    
    def add_detection(self, tracking_key: str) -> bool:
        """
        Add detection and check if verification threshold met
        
        Args:
            tracking_key: Unique identifier (e.g., plate number or camera_id)
        
        Returns:
            True if detection is verified (enough consecutive frames)
        """
        if tracking_key not in self.detection_buffer:
            self.detection_buffer[tracking_key] = deque(maxlen=self.required_frames)
        
        self.detection_buffer[tracking_key].append(time.time())
        
        # Check if we have enough frames
        if len(self.detection_buffer[tracking_key]) >= self.required_frames:
            timestamps = list(self.detection_buffer[tracking_key])
            time_span = timestamps[-1] - timestamps[0]
            
            # Verify within time window
            if time_span < self.time_window:
                logger.debug(f"Detection verified for {tracking_key} ({len(timestamps)} frames in {time_span:.1f}s)")
                return True
        
        return False
    
    def reset(self, tracking_key: str):
        """Clear detection buffer for specific key"""
        if tracking_key in self.detection_buffer:
            del self.detection_buffer[tracking_key]


class DuplicationChecker:
    """
    Prevents duplicate violations within time window
    
    SOLID: Single Responsibility - Only handles duplication logic
    """
    
    def __init__(self, time_window: int = 60, db_repository=None):
        """
        Args:
            time_window: Duplicate prevention window (seconds)
            db_repository: Database repository for persistent duplicate checking
        """
        self.time_window = time_window
        self.db_repository = db_repository
        self.recent_violations: Dict[str, float] = {}  # In-memory cache
        
        logger.info(f"DuplicationChecker initialized ({time_window}s window)")
    
    def is_duplicate(self, plate_number: Optional[str]) -> bool:
        """
        Check if violation is duplicate
        
        Args:
            plate_number: License plate number
        
        Returns:
            True if duplicate within time window
        """
        if not plate_number:
            return False
        
        # Check in-memory cache first (fast)
        current_time = time.time()
        if plate_number in self.recent_violations:
            last_time = self.recent_violations[plate_number]
            if (current_time - last_time) < self.time_window:
                logger.debug(f"Duplicate violation prevented: {plate_number}")
                return True
        
        # Check database (slower but persistent)
        if self.db_repository:
            db_duplicate = self.db_repository.check_recent_violation(
                plate_number, 
                self.time_window
            )
            if db_duplicate:
                self.recent_violations[plate_number] = current_time
                return True
        
        return False
    
    def mark_logged(self, plate_number: Optional[str]):
        """Mark violation as logged"""
        if plate_number:
            self.recent_violations[plate_number] = time.time()
    
    def cleanup(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired = [
            plate for plate, timestamp in self.recent_violations.items()
            if (current_time - timestamp) > self.time_window
        ]
        for plate in expired:
            del self.recent_violations[plate]


# ============================================
# Abstract Repository (Dependency Inversion)
# ============================================

class ViolationRepository(ABC):
    """
    Abstract interface for violation persistence
    
    SOLID: Dependency Inversion - Depend on abstraction, not concrete database
    """
    
    @abstractmethod
    def save(self, violation_data: Dict[str, Any]) -> Optional[int]:
        """Save violation and return ID"""
        pass
    
    @abstractmethod
    def check_recent_violation(self, plate_number: str, time_window: int) -> bool:
        """Check if recent violation exists"""
        pass


class DatabaseViolationRepository(ViolationRepository):
    """Concrete implementation using database"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def save(self, violation_data: Dict[str, Any]) -> Optional[int]:
        return self.db.insert_violation(violation_data)
    
    def check_recent_violation(self, plate_number: str, time_window: int) -> bool:
        return self.db.check_recent_violation(plate_number, time_window)


# ============================================
# Violation Manager (Orchestrator)
# ============================================

class ViolationManager:
    """
    Orchestrates violation detection pipeline
    
    SOLID Principles Applied:
    - Single Responsibility: Coordinates components, doesn't implement logic
    - Open/Closed: New rules added without modifying this class
    - Liskov Substitution: All rules implement ViolationRule interface
    - Interface Segregation: Separate interfaces for verification, deduplication, storage
    - Dependency Inversion: Depends on abstractions (ViolationRepository, ViolationRule)
    """
    
    def __init__(
        self,
        rules: List[ViolationRule],
        verifier: ConsecutiveFrameVerifier,
        deduplicator: DuplicationChecker,
        repository: ViolationRepository
    ):
        """
        Initialize with dependency injection
        
        Args:
            rules: List of violation rules to evaluate
            verifier: Frame verification component
            deduplicator: Duplicate prevention component
            repository: Storage abstraction
        
        SOLID: Dependency Injection for testability and flexibility
        """
        self.rules = rules
        self.verifier = verifier
        self.deduplicator = deduplicator
        self.repository = repository
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'violations_logged': 0,
            'duplicates_prevented': 0,
            'verification_pending': 0
        }
        
        logger.info(f"ViolationManager initialized with {len(rules)} rules")
    
    def process_detection(
        self,
        detection: Detection,
        camera_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process detection through violation pipeline
        
        Pipeline: Rule Evaluation → Frame Verification → Duplicate Check → Log
        
        Args:
            detection: Detection event
            camera_info: Camera metadata
        
        Returns:
            Decision dict with should_log, reason, violation_code
        """
        self.stats['total_detections'] += 1
        
        # Step 1: Evaluate rules
        matching_rule = self._evaluate_rules(detection)
        if not matching_rule:
            return {
                'should_log': False,
                'reason': 'No rule matched',
                'violation_code': None
            }
        
        # Step 2: Frame verification
        tracking_key = detection.plate_number or f"NO_PLATE_{camera_info['camera_id']}"
        if not self.verifier.add_detection(tracking_key):
            self.stats['verification_pending'] += 1
            return {
                'should_log': False,
                'reason': 'Verification pending (consecutive frames)',
                'violation_code': None
            }
        
        # Step 3: Duplicate check
        if detection.has_plate and self.deduplicator.is_duplicate(detection.plate_number):
            self.stats['duplicates_prevented'] += 1
            self.verifier.reset(tracking_key)  # Reset for next detection
            return {
                'should_log': False,
                'reason': f'Duplicate within {self.deduplicator.time_window}s',
                'violation_code': None
            }
        
        # Passed all checks - authorize logging
        violation_code = generate_violation_code()
        return {
            'should_log': True,
            'reason': f'Violation confirmed: {matching_rule.get_violation_type()}',
            'violation_code': violation_code,
            'violation_type': matching_rule.get_violation_type()
        }
    
    def _evaluate_rules(self, detection: Detection) -> Optional[ViolationRule]:
        """
        Evaluate all rules against detection
        
        Returns:
            First matching rule or None
        """
        for rule in self.rules:
            if rule.evaluate(detection):
                return rule
        return None
    
    def log_violation(self, violation_data: Dict[str, Any]) -> Optional[int]:
        """
        Persist violation to repository
        
        Args:
            violation_data: Violation details
        
        Returns:
            Violation ID or None
        """
        violation_id = self.repository.save(violation_data)
        
        if violation_id:
            self.stats['violations_logged'] += 1
            plate = violation_data.get('plate_number')
            if plate:
                self.deduplicator.mark_logged(plate)
            logger.info(f"Violation logged: {violation_data.get('violation_type')} (ID: {violation_id})")
        
        return violation_id
    
    def get_stats(self) -> Dict[str, int]:
        """Get violation statistics"""
        return self.stats.copy()


# ============================================
# Factory Function (Convenience)
# ============================================

def get_violation_manager(db_manager, config=None) -> ViolationManager:
    """
    Create ViolationManager with default configuration
    
    Args:
        db_manager: Database manager instance
        config: Optional configuration overrides
    
    Returns:
        Configured ViolationManager
    """
    config = config or VIOLATION_CONFIG
    
    # Define active rules
    rules = [
        NoHelmetRule(min_confidence=0.6),
        NutshellHelmetRule(min_confidence=0.6),
        # DoubleRiderRule(min_confidence=0.7),  # Enable when detector supports it
    ]
    
    # Create components
    verifier = ConsecutiveFrameVerifier(
        required_frames=config.get('consecutive_frames', 3),
        time_window=5.0
    )
    
    repository = DatabaseViolationRepository(db_manager)
    
    deduplicator = DuplicationChecker(
        time_window=config.get('duplicate_window', 60),
        db_repository=repository
    )
    
    # Assemble manager (dependency injection)
    manager = ViolationManager(
        rules=rules,
        verifier=verifier,
        deduplicator=deduplicator,
        repository=repository
    )
    
    return manager


# Testing
if __name__ == '__main__':
    print("Testing Violation Logic Module (Clean Architecture)...")
    print("=" * 60)
    
    # Mock repository
    class MockRepository(ViolationRepository):
        def __init__(self):
            self.violations = []
        
        def save(self, violation_data):
            self.violations.append(violation_data)
            return len(self.violations)
        
        def check_recent_violation(self, plate_number, time_window):
            return False
    
    # Create components
    rules = [NoHelmetRule(), NutshellHelmetRule()]
    verifier = ConsecutiveFrameVerifier(required_frames=2)
    deduplicator = DuplicationChecker(time_window=60, db_repository=None)
    repository = MockRepository()
    
    manager = ViolationManager(rules, verifier, deduplicator, repository)
    
    # Test 1: Rule evaluation
    print("\nTest 1: Rule Evaluation")
    detection = Detection(
        violation_type='no_helmet',
        confidence=0.85,
        bbox=(100, 100, 200, 200),
        timestamp=time.time(),
        plate_number='ABC-1234'
    )
    
    decision = manager.process_detection(detection, {'camera_id': 'CAM-WA-001'})
    print(f"  First detection: {decision['reason']}")
    
    # Test 2: Frame verification
    print("\nTest 2: Frame Verification (requires 2 consecutive)")
    decision = manager.process_detection(detection, {'camera_id': 'CAM-WA-001'})
    print(f"  Second detection: {decision['should_log']}")
    if decision['should_log']:
        print(f"  ✓ Violation verified: {decision['violation_code']}")
    
    # Test 3: Statistics
    print("\nTest 3: Statistics")
    stats = manager.get_stats()
    print(f"  Total detections: {stats['total_detections']}")
    print(f"  Violations logged: {stats['violations_logged']}")
    
    # Test 4: Extensibility (add new rule)
    print("\nTest 4: Extensibility - Adding DoubleRiderRule")
    double_rider_rule = DoubleRiderRule()
    manager.rules.append(double_rider_rule)
    print(f"  ✓ New rule added (total rules: {len(manager.rules)})")
    print("  Architecture supports new violation types without modifying core logic!")
    
    print("\n" + "=" * 60)
    print("Clean architecture test complete!")
