"""
Helmet Detection Module - Roboflow Cloud API Version
Cloud-based helmet detection using Roboflow's pre-trained models
"""

import cv2
import numpy as np
import sys
from pathlib import Path
import os

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger('helmet_detector_roboflow')

class HelmetDetectorRoboflow:
    """Roboflow-based helmet detector using cloud API"""
    
    def __init__(self, api_key=None, project_name=None, version=1):
        """
        Initialize Roboflow detector
        
        Args:
            api_key (str): Roboflow API key
            project_name (str): Roboflow project name
            version (int): Model version number
        """
        self.api_key = api_key
        self.project_name = project_name
        self.version = version
        self.model = None
        self.confidence_threshold = 0.6
        
        try:
            from roboflow import Roboflow
            self.roboflow_available = True
            
            if api_key and project_name:
                self._initialize_model()
            else:
                logger.warning("Roboflow API key or project name not provided. Detector not initialized.")
        except ImportError:
            self.roboflow_available = False
            logger.error("Roboflow package not installed. Run: pip install roboflow")
    
    def _initialize_model(self):
        """Initialize the Roboflow model"""
        try:
            from roboflow import Roboflow
            
            logger.info(f"Initializing Roboflow model: {self.project_name}")
            rf = Roboflow(api_key=self.api_key)
            
            # Get workspace and project
            workspace = rf.workspace()
            project = workspace.project(self.project_name)
            
            # Get model version
            self.model = project.version(self.version).model
            
            logger.info(f"✓ Roboflow model loaded: {self.project_name} v{self.version}")
        except Exception as e:
            logger.error(f"Failed to initialize Roboflow model: {e}")
            self.model = None
    
    def set_confidence(self, threshold):
        """Set detection confidence threshold"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Confidence threshold set to: {self.confidence_threshold}")
    
    def process_frame(self, frame):
        """
        Process a single frame for helmet detection
        
        Args:
            frame (numpy.ndarray): Input image frame
            
        Returns:
            dict: Detection results
        """
        if not self.roboflow_available or self.model is None:
            return {
                'has_violation': False,
                'detections': [],
                'best_violation': None,
                'error': 'Roboflow model not initialized'
            }
        
        try:
            # Save frame temporarily for Roboflow
            temp_path = 'temp_frame.jpg'
            cv2.imwrite(temp_path, frame)
            
            # Run prediction
            predictions = self.model.predict(
                temp_path, 
                confidence=int(self.confidence_threshold * 100)
            ).json()
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Parse predictions
            detections = []
            violations = []
            
            for pred in predictions.get('predictions', []):
                class_name = pred['class'].lower()
                confidence = pred['confidence']
                
                # Extract bounding box
                x_center = pred['x']
                y_center = pred['y']
                width = pred['width']
                height = pred['height']
                
                # Convert to x1, y1, x2, y2
                x1 = int(x_center - width / 2)
                y1 = int(y_center - height / 2)
                x2 = int(x_center + width / 2)
                y2 = int(y_center + height / 2)
                
                detection = {
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': [x1, y1, x2, y2]
                }
                
                detections.append(detection)
                
                # Check if it's a violation
                if class_name in ['no_helmet', 'nutshell_helmet', 'no-helmet', 'nutshell']:
                    violations.append(detection)
            
            # Find best violation (highest confidence)
            best_violation = None
            if violations:
                best_violation = max(violations, key=lambda x: x['confidence'])
            
            result = {
                'has_violation': len(violations) > 0,
                'detections': detections,
                'best_violation': best_violation,
                'total_detections': len(detections),
                'violation_count': len(violations)
            }
            
            if result['has_violation']:
                logger.info(f"Violation detected: {best_violation['class_name']} "
                          f"({best_violation['confidence']:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Roboflow detection error: {e}")
            return {
                'has_violation': False,
                'detections': [],
                'best_violation': None,
                'error': str(e)
            }
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes on frame"""
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Color based on class
            if class_name in ['no_helmet', 'no-helmet']:
                color = (0, 0, 255)  # Red
            elif class_name in ['nutshell_helmet', 'nutshell']:
                color = (0, 165, 255)  # Orange
            else:
                color = (0, 255, 0)  # Green
            
            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated


# Singleton instance
_detector_instance = None

def get_detector(api_key=None, project_name=None, version=1):
    """Get singleton detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = HelmetDetectorRoboflow(api_key, project_name, version)
    return _detector_instance


# Test function
if __name__ == "__main__":
    import os
    
    print("Testing Roboflow Helmet Detector\n")
    
    # You need to set these
    API_KEY = os.getenv('ROBOFLOW_API_KEY', 'your_api_key_here')
    PROJECT = os.getenv('ROBOFLOW_PROJECT', 'helmet-detection')
    
    if API_KEY == 'your_api_key_here':
        print("⚠ Please set ROBOFLOW_API_KEY environment variable or update the code")
        print("Get your API key from: https://app.roboflow.com/")
    else:
        detector = get_detector(api_key=API_KEY, project_name=PROJECT)
        print("Detector initialized successfully!")
        print("Ready to process frames.")
