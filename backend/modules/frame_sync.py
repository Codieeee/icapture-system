"""
Frame Synchronization Module for iCapture System
Ensures wide-angle and plate camera frames are temporally matched

PRODUCTION READY: Guarantees helmet + plate det detection pair are from the same moment
"""

import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger('frame_sync')

# Synchronization tolerance (frames within 100ms are considered synchronized)
SYNC_TOLERANCE_MS = 100
BUFFER_MAX_AGE_SECONDS = 2.0  # Drop frames older than 2 seconds

@dataclass
class TimestampedFrame:
    """Frame with timestamp and metadata"""
    frame: np.ndarray
    timestamp: float
    camera_type: str
    brightness: float = 0.0
    
    def age(self) -> float:
        """Get frame age in seconds"""
        return time.time() - self.timestamp

@dataclass
class FramePair:
    """
    Atomically paired frames from both cameras
    
    Guarantees that wide_frame and plate_frame are from the same moment (±100ms)
    """
    wide_frame: np.ndarray
    plate_frame: Optional[np.ndarray]
    timestamp: float
    camera_info: Dict[str, str] = field(default_factory=dict)
    wide_brightness: float = 0.0
    plate_brightness: float = 0.0
    is_synchronized: bool = True  # False if only one camera has frame
    
    @property
    def has_both_cameras(self) -> bool:
        """Check if both cameras contributed frames"""
        return self.plate_frame is not None
    
    @property
    def age(self) -> float:
        """Get pair age in seconds"""
        return time.time() - self.timestamp


class FrameSynchronizer:
    """
    Buffers frames and produces synchronized pairs
    
    PRODUCTION READY: Handles missing frames, camera failures, and FPS differences
    """
    
    def __init__(self, sync_tolerance_ms=SYNC_TOLERANCE_MS, buffer_size=30):
        """
        Initialize frame synchronizer
        
        Args:
            sync_tolerance_ms: Maximum time difference for synchronization (milliseconds)
            buffer_size: Maximum frames to buffer per camera
        """
        self.sync_tolerance = sync_tolerance_ms / 1000.0  # Convert to seconds
        self.buffer_size = buffer_size
        
        # Rolling buffers for each camera (newest first)
        self.wide_buffer = deque(maxlen=buffer_size)
        self.plate_buffer = deque(maxlen=buffer_size)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'pairs_created': 0,
            'wide_only': 0,  # Pairs with only wide-angle frame
            'sync_failures': 0,  # Failed to find matching frames
            'dropped_old_frames': 0
        }
        
        logger.info(f"FrameSynchronizer initialized (tolerance: {sync_tolerance_ms}ms, buffer: {buffer_size})")
    
    def add_frame(self, frame: np.ndarray, camera_type: str, brightness: float = 0.0):
        """
        Add frame to buffer
        
        Args:
            frame: BGR image
            camera_type: 'wide_angle' or 'plate'
            brightness: Optional brightness value
        """
        if frame is None:
            return
        
        timestamped = TimestampedFrame(
            frame=frame,
            timestamp=time.time(),
            camera_type=camera_type,
            brightness=brightness
        )
        
        with self.lock:
            if camera_type == 'wide_angle':
                self.wide_buffer.append(timestamped)
            elif camera_type == 'plate':
                self.plate_buffer.append(timestamped)
            else:
                logger.warning(f"Unknown camera type: {camera_type}")
    
    def _cleanup_old_frames(self):
        """Remove frames older than max age (called with lock held)"""
        current_time = time.time()
        
        # Clean wide buffer
        while self.wide_buffer and (current_time - self.wide_buffer[0].timestamp) > BUFFER_MAX_AGE_SECONDS:
            self.wide_buffer.popleft()
            self.stats['dropped_old_frames'] += 1
        
        # Clean plate buffer
        while self.plate_buffer and (current_time - self.plate_buffer[0].timestamp) > BUFFER_MAX_AGE_SECONDS:
            self.plate_buffer.popleft()
            self.stats['dropped_old_frames'] += 1
    
    def get_synchronized_pair(self, timeout: float = 0.1) -> Optional[FramePair]:
        """
        Get next synchronized frame pair
        
        Args:
            timeout: How long to wait for synchronized frames (seconds)
        
        Returns:
            FramePair if frames are available, None otherwise
            
        Note:
            Returns pair with only wide_frame if plate camera fails (graceful degradation)
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            with self.lock:
                self._cleanup_old_frames()
                
                # Need at least one wide-angle frame
                if not self.wide_buffer:
                    time.sleep(0.01)
                    continue
                
                # Get newest wide-angle frame
                wide_frame = self.wide_buffer[-1]
                
                # Try to find matching plate frame
                plate_frame = self._find_matching_frame(wide_frame.timestamp, self.plate_buffer)
                
                if plate_frame:
                    # Perfect synchronization
                    pair = FramePair(
                        wide_frame=wide_frame.frame.copy(),
                        plate_frame=plate_frame.frame.copy(),
                        timestamp=wide_frame.timestamp,
                        wide_brightness=wide_frame.brightness,
                        plate_brightness=plate_frame.brightness,
                        is_synchronized=True
                    )
                    
                    # Remove used frames from buffers
                    self.wide_buffer.pop()
                    try:
                        self.plate_buffer.remove(plate_frame)
                    except ValueError:
                        pass  # Already removed
                    
                    self.stats['pairs_created'] += 1
                    logger.debug(f"Synchronized pair created (diff: {abs(wide_frame.timestamp - plate_frame.timestamp)*1000:.1f}ms)")
                    return pair
                
                else:
                    # No matching plate frame - graceful degradation
                    # Continue with wide-angle only if plate is unavailable
                    if len(self.plate_buffer) == 0 or wide_frame.age() > self.sync_tolerance:
                        pair = FramePair(
                            wide_frame=wide_frame.frame.copy(),
                            plate_frame=None,
                            timestamp=wide_frame.timestamp,
                            wide_brightness=wide_frame.brightness,
                            is_synchronized=False
                        )
                        
                        self.wide_buffer.pop()
                        self.stats['wide_only'] += 1
                        logger.warning(f"Frame pair with wide-angle only (plate camera unavailable)")
                        return pair
            
            time.sleep(0.01)  # Small delay before retry
        
        # Timeout - no synchronized frames available
        self.stats['sync_failures'] += 1
        return None
    
    def _find_matching_frame(self, target_timestamp: float, buffer: deque) -> Optional[TimestampedFrame]:
        """
        Find frame in buffer closest to target timestamp (within tolerance)
        
        Args:
            target_timestamp: Timestamp to match
            buffer: Buffer to search
        
        Returns:
            Matching frame or None
        """
        if not buffer:
            return None
        
        best_match = None
        best_diff = float('inf')
        
        for frame in buffer:
            time_diff = abs(frame.timestamp - target_timestamp)
            
            if time_diff <= self.sync_tolerance and time_diff < best_diff:
                best_match = frame
                best_diff = time_diff
        
        return best_match
    
    def get_stats(self) -> Dict:
        """Get synchronization statistics"""
        with self.lock:
            return {
                **self.stats,
                'wide_buffer_size': len(self.wide_buffer),
                'plate_buffer_size': len(self.plate_buffer),
                'sync_rate': self.stats['pairs_created'] / max(1, self.stats['pairs_created'] + self.stats['wide_only'] + self.stats['sync_failures'])
            }
    
    def reset_stats(self):
        """Reset statistics"""
        with self.lock:
            self.stats = {
                'pairs_created': 0,
                'wide_only': 0,
                'sync_failures': 0,
                'dropped_old_frames': 0
            }


# Singleton instance
_synchronizer = None

def get_synchronizer() -> FrameSynchronizer:
    """Get singleton frame synchronizer"""
    global _synchronizer
    if _synchronizer is None:
        _synchronizer = FrameSynchronizer()
    return _synchronizer


# Testing
if __name__ == '__main__':
    print("Testing Frame Synchronization Module...")
    print("=" * 60)
    
    sync = FrameSynchronizer(sync_tolerance_ms=100)
    
    # Simulate frames from both cameras
    import cv2
    
    # Test 1: Perfect synchronization
    print("\nTest 1: Perfect synchronization (same timestamp)")
    wide = np.zeros((480, 640, 3), dtype=np.uint8)
    plate = np.zeros((480, 640, 3), dtype=np.uint8)
    
    sync.add_frame(wide, 'wide_angle', brightness=120.0)
    sync.add_frame(plate, 'plate', brightness=100.0)
    
    pair = sync.get_synchronized_pair(timeout=0.5)
    if pair and pair.has_both_cameras:
        print("  ✓ Synchronized pair created")
        print(f"    Wide brightness: {pair.wide_brightness}")
        print(f"    Plate brightness: {pair.plate_brightness}")
    else:
        print("  ✗ Failed to create pair")
    
    # Test 2: Graceful degradation (plate camera missing)
    print("\nTest 2: Graceful degradation (no plate camera)")
    sync.add_frame(wide, 'wide_angle', brightness=125.0)
    time.sleep(0.15)  # Wait longer than tolerance
    
    pair = sync.get_synchronized_pair(timeout=0.5)
    if pair and not pair.has_both_cameras:
        print("  ✓ Wide-angle only pair created (graceful degradation)")
    else:
        print("  ✗ Unexpected result")
    
    # Test 3: Statistics
    print("\nTest 3: Statistics")
    stats = sync.get_stats()
    print(f"  Pairs created: {stats['pairs_created']}")
    print(f"  Wide-only: {stats['wide_only']}")
    print(f"  Sync rate: {stats['sync_rate']:.2%}")
    
    print("\n" + "=" * 60)
    print("Frame synchronization test complete!")
