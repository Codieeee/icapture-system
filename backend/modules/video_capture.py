"""
Video Capture Module for iCapture System
Handles dual-camera input with real-time frame processing and auto-reconnection

DEFENSE READY: Includes lighting quality checks to prevent OCR failures
"""

import cv2
import threading
import time
import numpy as np
from queue import Queue
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import CAMERA_CONFIG, CAMERA_RETRY_ATTEMPTS, CAMERA_RETRY_DELAY
from utils.logger import get_logger

logger = get_logger('video_capture')

# ============================================
# Lighting Quality Constants
# Defense Safe: Prevents OCR failures in low-light conditions
# ============================================
LOW_LIGHT_THRESHOLD = 50  # Average pixel intensity threshold
LIGHTING_CHECK_ENABLED = True  # Set to False to disable warnings

class CameraStream:
    """
    Individual camera stream handler with thread-safe frame access
    
    DEFENSE READY: Includes real-time lighting quality monitoring
    """
    
    def __init__(self, camera_id, stream_url, fps=30):
        """
        Initialize camera stream
        
        Args:
            camera_id: Camera identifier (e.g., 'CAM-WA-001')
            stream_url: Camera source (0, 1 for USB, or RTSP URL)
            fps: Target frames per second
        """
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.target_fps = fps
        self.frame_delay = 1.0 / fps
        
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.frame_lock = threading.Lock()
        
        # Defense Safe: Track lighting warnings to avoid spam
        self.last_lighting_warning = 0
        self.lighting_warning_interval = 5  # seconds between warnings
        
        logger.info(f"CameraStream initialized: {camera_id} @ {stream_url}")
    
    def connect(self):
        """Connect to camera with retry logic"""
        for attempt in range(CAMERA_RETRY_ATTEMPTS):
            try:
                logger.info(f"Connecting to camera {self.camera_id} (attempt {attempt + 1})...")
                self.cap = cv2.VideoCapture(self.stream_url)
                
                if self.cap.isOpened():
                    # Set camera properties
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
                    logger.info(f"Camera {self.camera_id} connected successfully")
                    return True
                else:
                    logger.warning(f"Camera {self.camera_id} failed to open")
            except Exception as e:
                logger.error(f"Camera connection error: {e}")
            
            if attempt < CAMERA_RETRY_ATTEMPTS - 1:
                time.sleep(CAMERA_RETRY_DELAY * (attempt + 1))  # Exponential backoff
        
        logger.error(f"Camera {self.camera_id} connection failed after {CAMERA_RETRY_ATTEMPTS} attempts")
        return False
    
    def _check_lighting(self, frame):
        """
        Check frame brightness and warn if lighting is insufficient
        
        DEFENSE FEATURE: Prevents silent OCR failures during demo
        
        Args:
            frame: BGR image frame
        
        Returns:
            float: Average brightness (0-255)
        """
        if not LIGHTING_CHECK_ENABLED or frame is None:
            return 255  # Skip check
        
        # Convert to grayscale and calculate average intensity
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        
        # Defense Safe: Warn about low light (throttled to avoid console spam)
        current_time = time.time()
        if avg_brightness < LOW_LIGHT_THRESHOLD:
            if current_time - self.last_lighting_warning > self.lighting_warning_interval:
                print(f"⚠️  WARNING: LOW LIGHT DETECTED on {self.camera_id}. OCR MAY FAIL.")
                print(f"    Brightness: {avg_brightness:.1f}/255 (Threshold: {LOW_LIGHT_THRESHOLD})")
                logger.warning(f"Low light on {self.camera_id}: {avg_brightness:.1f}/255")
                self.last_lighting_warning = current_time
        
        return avg_brightness
    
    def start(self):
        """Start frame capture thread"""
        if not self.connect():
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info(f"Camera {self.camera_id} capture thread started")
        return True
    
    def _capture_loop(self):
        """
        Continuous frame capture loop (runs in separate thread)
        
        DEFENSE READY: Includes lighting quality monitoring
        """
        consecutive_failures = 0
        max_failures = 10
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if ret:
                    # Defense Feature: Check lighting quality
                    self._check_lighting(frame)
                    
                    with self.frame_lock:
                        self.frame = frame
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    logger.warning(f"Camera {self.camera_id}: Frame read failed ({consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        logger.error(f"Camera {self.camera_id}: Too many failures, attempting reconnection...")
                        self.cap.release()
                        if not self.connect():
                            logger.critical(f"Camera {self.camera_id}: Reconnection failed, stopping stream")
                            break
                        consecutive_failures = 0
                
                time.sleep(self.frame_delay)
            except Exception as e:
                logger.error(f"Camera {self.camera_id} capture error: {e}")
                time.sleep(1)
    
    def get_frame(self):
        """
        Get latest frame (thread-safe)
        
        Returns:
            numpy array or None if no frame available
        """
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
    
    def get_frame_with_brightness(self):
        """
        Get latest frame with brightness information
        
        DEFENSE FEATURE: Allows external modules to check lighting
        
        Returns:
            tuple: (frame, brightness) or (None, 0)
        """
        frame = self.get_frame()
        if frame is None:
            return None, 0
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        return frame, brightness
    
    def is_active(self):
        """Check if camera is actively capturing"""
        return self.running and self.cap is not None and self.cap.isOpened()
    
    def stop(self):
        """Stop capture thread and release camera"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
        logger.info(f"Camera {self.camera_id} stopped")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop()

class VideoCaptureManager:
    """
    Manages multiple camera streams for the iCapture system
    
    DEFENSE READY: Includes system-wide lighting quality monitoring
    """
    
    def __init__(self, config=None):
        """
        Initialize video capture manager with dual cameras
        
        Args:
            config: Camera configuration dict (uses default if None)
        """
        self.config = config or CAMERA_CONFIG
        self.cameras = {}
        logger.info("VideoCaptureManager initialized with lighting checks enabled")
    
    def start_cameras(self):
        """Start all configured cameras"""
        success_count = 0
        
        for cam_type, cam_config in self.config.items():
            camera = CameraStream(
                camera_id=cam_config['camera_id'],
                stream_url=cam_config['stream_url'],
                fps=cam_config['fps']
            )
            
            if camera.start():
                self.cameras[cam_type] = camera
                success_count += 1
                logger.info(f"Camera {cam_type} started successfully")
            else:
                logger.error(f"Failed to start camera {cam_type}")
        
        logger.info(f"{success_count}/{len(self.config)} cameras started")
        return success_count > 0
    
    def get_frame(self, camera_type):
        """
        Get frame from specific camera
        
        Args:
            camera_type: 'wide_angle' or 'plate'
        
        Returns:
            numpy array (BGR image) or None
        """
        camera = self.cameras.get(camera_type)
        if camera:
            return camera.get_frame()
        return None
    
    def get_frame_with_quality_check(self, camera_type):
        """
        Get frame with lighting quality information
        
        DEFENSE FEATURE: Returns brightness data for advanced processing
        
        Args:
            camera_type: 'wide_angle' or 'plate'
        
        Returns:
            tuple: (frame, brightness, is_adequate)
        """
        camera = self.cameras.get(camera_type)
        if camera:
            frame, brightness = camera.get_frame_with_brightness()
            is_adequate = brightness >= LOW_LIGHT_THRESHOLD
            return frame, brightness, is_adequate
        return None, 0, False
    
    def is_camera_active(self, camera_type):
        """Check if specific camera is active"""
        camera = self.cameras.get(camera_type)
        return camera.is_active() if camera else False
    
    def get_all_frames(self):
        """
        Get frames from all cameras
        
        Returns:
            dict: {camera_type: frame}
        """
        frames = {}
        for cam_type, camera in self.cameras.items():
            frame = camera.get_frame()
            if frame is not None:
                frames[cam_type] = frame
        return frames
    
    def get_camera_status(self):
        """
        Get status of all cameras including lighting quality
        
        DEFENSE READY: Includes brightness monitoring
        """
        status = {}
        for cam_type, camera in self.cameras.items():
            frame, brightness = camera.get_frame_with_brightness()
            status[cam_type] = {
                'camera_id': camera.camera_id,
                'active': camera.is_active(),
                'stream_url': camera.stream_url,
                'brightness': round(brightness, 1),
                'lighting_adequate': brightness >= LOW_LIGHT_THRESHOLD
            }
        return status
    
    def stop_all(self):
        """Stop all cameras and cleanup"""
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()
        logger.info("All cameras stopped")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop_all()

# Test function
def test_cameras(duration=10):
    """
    Test camera capture for specified duration
    
    DEFENSE READY: Displays lighting quality warnings
    
    Args:
        duration: Test duration in seconds
    """
    print("Starting camera test with lighting quality monitoring...")
    print(f"Low light threshold: {LOW_LIGHT_THRESHOLD}/255\n")
    
    manager = VideoCaptureManager()
    
    if not manager.start_cameras():
        print("Failed to start cameras")
        return
    
    print(f"Cameras started. Testing for {duration} seconds...")
    print("Watch for lighting warnings if environment is too dark.\n")
    
    start_time = time.time()
    frame_count = {'wide_angle': 0, 'plate': 0}
    
    try:
        while time.time() - start_time < duration:
            frames = manager.get_all_frames()
            
            for cam_type, frame in frames.items():
                if frame is not None:
                    frame_count[cam_type] += 1
                    
                    # Defense Feature: Display brightness on frame
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    brightness = np.mean(gray)
                    color = (0, 255, 0) if brightness >= LOW_LIGHT_THRESHOLD else (0, 0, 255)
                    
                    cv2.putText(frame, f"Brightness: {brightness:.1f}/255", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    # Display frame
                    cv2.imshow(f'{cam_type.replace("_", " ").title()}', frame)
            
            # Check for 'q' key to quit early
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Test interrupted by user")
                break
    finally:
        manager.stop_all()
        cv2.destroyAllWindows()
    
    elapsed = time.time() - start_time
    print("\nTest Results:")
    for cam_type, count in frame_count.items():
        fps = count / elapsed
        print(f"  {cam_type}: {count} frames ({fps:.2f} FPS)")
    
    # Defense Summary
    print("\nLighting Quality Summary:")
    status = manager.get_camera_status()
    for cam_type, info in status.items():
        quality = "✓ ADEQUATE" if info['lighting_adequate'] else "⚠ LOW LIGHT"
        print(f"  {cam_type}: {info['brightness']}/255 - {quality}")

if __name__ == '__main__':
    # Run camera test with lighting monitoring
    test_cameras(duration=10)
