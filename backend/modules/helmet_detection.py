"""
Helmet Detection Module for iCapture System
Supports both Roboflow Cloud API and Local YOLOv5
"""

import cv2
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import HELMET_DETECTION_CONFIG
from utils.logger import get_logger

logger = get_logger('helmet_detector')

class HelmetDetector:
    """YOLOv5 helmet detection and classification"""
    
    def __init__(self, model_path=None, confidence=0.6, device='cuda'):
        """
        Initialize helmet detector
        
        Args:
            model_path: Path to YOLOv5 model weights (.pt file)
            confidence: Minimum detection confidence (0-1)
            device: 'cuda' for GPU or 'cpu'
        """
        self.model_path = model_path or YOLO_CONFIG['model_path']
        self.confidence_threshold = confidence or YOLO_CONFIG['confidence_threshold']
        self.device = device if torch.cuda.is_available() else 'cpu'
        
        self.model = None
        self.classes = YOLO_CONFIG['classes']
        self.violation_classes = YOLO_CONFIG['violation_classes']
        
        self.load_model()
        logger.info(f"HelmetDetector initialized (device: {self.device})")
    
    def load_model(self):
        """Load YOLOv5 model"""
        try:
            model_file = Path(self.model_path)
            
            if not model_file.exists():
                logger.warning(f"Model not found: {self.model_path}")
                logger.info("Using YOLOv5 pretrained model (placeholder)")
                # Load pretrained YOLOv5s as fallback
                self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            else:
                # Load custom trained model
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
            
            self.model.to(self.device)
            self.model.conf = self.confidence_threshold
            self.model.iou = YOLO_CONFIG['iou_threshold']
            
            logger.info(f"YOLOv5 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def detect_helmets(self, frame):
        """
        Detect motorcycles and helmet violations in frame
        
        Args:
            frame: numpy array (BGR image)
        
        Returns:
            list: Detection results, each with:
                - bbox: [x1, y1, x2, y2]
                - class_name: 'with_helmet', 'no_helmet', or 'nutshell_helmet'
                - confidence: float (0-1)
                - is_violation: bool
        """
        if self.model is None:
            logger.error("Model not loaded, cannot detect")
            return []
        
        try:
            # Run inference
            results = self.model(frame, size=YOLO_CONFIG['img_size'])
            
            # Parse results
            detections = []
            for det in results.xyxy[0]:  # xyxy format: [x1, y1, x2, y2, conf, class]
                x1, y1, x2, y2, conf, cls = det.cpu().numpy()
                
                # Map class ID to name (this assumes your custom model outputs 0, 1, 2)
                # Adjust if your model has different class mapping
                class_id = int(cls)
                class_name = self.classes.get(class_id, 'unknown')
                
                detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'class_name': class_name,
                    'confidence': float(conf),
                    'is_violation': class_name in self.violation_classes
                }
                
                detections.append(detection)
            
            return detections
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def extract_rider_bbox(self, detections):
        """
        Extract bounding box for rider with violation
        
        Args:
            detections: List of detection dicts
        
        Returns:
            dict: Best violation detection or None
        """
        violations = [d for d in detections if d['is_violation']]
        
        if not violations:
            return None
        
        # Return highest confidence violation
        best_violation = max(violations, key=lambda x: x['confidence'])
        return best_violation
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on frame
        
        Args:
            frame: numpy array (BGR)
            detections: List of detection dicts
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Color coding
            if det['is_violation']:
                color = (0, 0, 255)  # Red for violations
            else:
                color = (0, 255, 0)  # Green for compliant
            
            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated
    
    def process_frame(self, frame, return_annotated=False):
        """
        Complete frame processing: detect and optionally annotate
        
        Args:
            frame: Input frame
            return_annotated: Whether to return annotated frame
        
        Returns:
            dict: {
                'detections': list of detections,
                'has_violation': bool,
                'best_violation': dict or None,
                'annotated_frame': numpy array (if requested)
            }
        """
        detections = self.detect_helmets(frame)
        best_violation = self.extract_rider_bbox(detections)
        
        result = {
            'detections': detections,
            'has_violation': best_violation is not None,
            'best_violation': best_violation
        }
        
        if return_annotated:
            result['annotated_frame'] = self.draw_detections(frame, detections)
        
        return result

# Singleton instance
_detector = None

def get_detector():
    """Get or create helmet detector singleton"""
    global _detector
    if _detector is None:
        _detector = HelmetDetector()
    return _detector

if __name__ == '__main__':
    # Test helmet detection with webcam
    print("Testing Helmet Detection Module...")
    detector = HelmetDetector()
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Failed to open camera")
    else:
        print("Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            result = detector.process_frame(frame, return_annotated=True)
            
            # Display results
            if 'annotated_frame' in result:
                cv2.putText(result['annotated_frame'], 
                           f"Violations: {len([d for d in result['detections'] if d['is_violation']])}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                cv2.imshow('Helmet Detection', result['annotated_frame'])
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
