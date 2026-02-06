"""
Unified Helmet Detection Module
Automatically uses Roboflow or Local YOLOv5 based on config
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import HELMET_DETECTION_CONFIG
from utils.logger import get_logger

logger = get_logger('helmet_detector_unified')

# Global detector instance
_detector = None

def get_detector():
    """
    Get helmet detector based on configuration mode
    Automatically initializes Roboflow or Local YOLOv5
    """
    global _detector
    
    if _detector is not None:
        return _detector
    
    mode = HELMET_DETECTION_CONFIG.get('mode', 'local').lower()
    
    logger.info(f"Initializing helmet detector in '{mode}' mode...")
    
    if mode == 'roboflow':
        # Use Roboflow cloud API
        try:
            from modules.helmet_detection_roboflow import get_detector as get_roboflow_detector
            
            config = HELMET_DETECTION_CONFIG['roboflow']
            _detector = get_roboflow_detector(
                api_key=config['api_key'],
                project_name=config['project_name'],
                version=config['version']
            )
            _detector.set_confidence(config['confidence_threshold'])
            
            logger.info("✓ Roboflow detector initialized (cloud mode)")
            
        except Exception as e:
            logger.error(f"Failed to initialize Roboflow detector: {e}")
            logger.warning("Falling back to local YOLOv5...")
            mode = 'local'
    
    if mode == 'local':
        # Use local YOLOv5
        try:
            from modules.helmet_detection import get_detector as get_local_detector
            
            _detector = get_local_detector()
            logger.info("✓ Local YOLOv5 detector initialized (offline mode)")
            
        except Exception as e:
            logger.error(f"Failed to initialize local detector: {e}")
            raise RuntimeError("No helmet detection backend available!")
    
    return _detector


def process_frame(frame):
    """
    Process frame using active detector
    
    Args:
        frame: Input image frame
        
    Returns:
        dict: Detection results
    """
    detector = get_detector()
    return detector.process_frame(frame)


def draw_detections(frame, detections):
    """
    Draw detection bounding boxes
    
    Args:
        frame: Input image
        detections: List of detections
        
    Returns:
        Annotated frame
    """
    detector = get_detector()
    return detector.draw_detections(frame, detections)


# Test function
if __name__ == "__main__":
    print("Testing Unified Helmet Detector\n")
    
    detector = get_detector()
    
    mode = HELMET_DETECTION_CONFIG.get('mode', 'local')
    print(f"Active mode: {mode}")
    print(f"Detector type: {type(detector).__name__}")
    
    if hasattr(detector, 'model'):
        print("✓ Detector ready to process frames")
    else:
        print("⚠ Detector initialization incomplete")
