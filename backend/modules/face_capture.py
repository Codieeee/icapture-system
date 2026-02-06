"""
Face Capture Module for iCapture System
Extracts and stores rider face images upon violation detection
"""

import cv2
import numpy as np
from datetime import datetime
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config import STORAGE_CONFIG, VIOLATION_CONFIG
from utils.logger import get_logger
from utils.image_processing import (
    is_blurry, assess_quality, enhance_image,
    crop_with_margin, resize_image, save_image
)

logger = get_logger('face_capture')

class FaceCapture:
    """Rider face extraction and quality assessment"""
    
    def __init__(self, storage_dir=None, quality_threshold=0.5):
        """
        Initialize face capture module
        
        Args:
            storage_dir: Directory to save face images
            quality_threshold: Minimum quality score (0-1)
        """
        self.storage_dir = storage_dir or STORAGE_CONFIG['face_dir']
        self.quality_threshold = quality_threshold or VIOLATION_CONFIG['face_quality_threshold']
        self.image_format = STORAGE_CONFIG['image_format']
        self.jpeg_quality = STORAGE_CONFIG['jpeg_quality']
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logger.info(f"FaceCapture initialized (storage: {self.storage_dir})")
    
    def extract_face(self, frame, bbox, margin=0.15):
        """
        Extract face region from frame using bounding box
        
        Args:
            frame: numpy array (BGR)
            bbox: [x1, y1, x2, y2] bounding box coordinates
            margin: Margin percentage to add around bbox
        
        Returns:
            Extracted face image or None
        """
        try:
            # Crop with margin
            face_img = crop_with_margin(frame, bbox, margin_percent=margin)
            
            if face_img is None or face_img.size == 0:
                logger.warning("Failed to crop face region")
                return None
            
            return face_img
        except Exception as e:
            logger.error(f"Face extraction error: {e}")
            return None
    
    def assess_face_quality(self, face_img):
        """
        Assess quality of extracted face image
        
        Args:
            face_img: numpy array (BGR)
        
        Returns:
            dict: {
                'quality_score': float (0-1),
                'is_blurry': bool,
                'blur_variance': float,
                'meets_threshold': bool
            }
        """
        try:
            # Overall quality assessment
            quality_score = assess_quality(face_img)
            
            # Blur detection
            blurry, blur_var = is_blurry(face_img, threshold=100.0)
            
            return {
                'quality_score': quality_score,
                'is_blurry': blurry,
                'blur_variance': blur_var,
                'meets_threshold': quality_score >= self.quality_threshold
            }
        except Exception as e:
            logger.error(f"Quality assessment error: {e}")
            return {
                'quality_score': 0.0,
                'is_blurry': True,
                'blur_variance': 0.0,
                'meets_threshold': False
            }
    
    def enhance_face(self, face_img):
        """
        Enhance face image for better visibility
        
        Args:
            face_img: numpy array (BGR)
        
        Returns:
            Enhanced image
        """
        try:
            # Auto-enhance brightness and contrast
            enhanced = enhance_image(face_img, brightness=1.1, contrast=1.2)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
            
            return denoised
        except Exception as e:
            logger.warning(f"Enhancement failed: {e}")
            return face_img  # Return original on error
    
    def save_face_image(self, face_img, violation_code):
        """
        Save face image to disk
        
        Args:
            face_img: numpy array (BGR)
            violation_code: Violation code for filename
        
        Returns:
            str: Saved file path or None on error
        """
        try:
            # Generate filename
            filename = f"{violation_code}_face.{self.image_format}"
            filepath = os.path.join(self.storage_dir, filename)
            
            # Resize if too large
            resized = resize_image(face_img, max_size=(800, 600))
            
            # Save
            success = save_image(resized, filepath, quality=self.jpeg_quality)
            
            if success:
                logger.info(f"Face image saved: {filepath}")
                return filepath
            else:
                logger.error(f"Failed to save face image: {filepath}")
                return None
        except Exception as e:
            logger.error(f"Save error: {e}")
            return None
    
    def capture_and_save(self, frame, bbox, violation_code, enhance=True):
        """
        Complete workflow: extract, enhance, assess, save
        
        Args:
            frame: Input frame
            bbox: Bounding box [x1, y1, x2, y2]
            violation_code: Violation identifier
            enhance: Whether to enhance image
        
        Returns:
            dict: {
                'success': bool,
                'filepath': str or None,
                'quality_info': dict
            }
        """
        # Extract face
        face_img = self.extract_face(frame, bbox)
        
        if face_img is None:
            return {'success': False, 'filepath': None, 'quality_info': {}}
        
        # Enhance if requested
        if enhance:
            face_img = self.enhance_face(face_img)
        
        # Assess quality
        quality_info = self.assess_face_quality(face_img)
        
        # Check if meets threshold
        if not quality_info['meets_threshold']:
            logger.warning(f"Face quality below threshold: {quality_info['quality_score']:.3f}")
        
        # Save (even if below threshold, for manual review)
        filepath = self.save_face_image(face_img, violation_code)
        
        return {
            'success': filepath is not None,
            'filepath': filepath,
            'quality_info': quality_info
        }
    
    def capture_best_of_multiple(self, frames_with_bboxes, violation_code, max_attempts=5):
        """
        Capture multiple frames and save the best quality one
        
        Args:
            frames_with_bboxes: List of (frame, bbox) tuples
            violation_code: Violation identifier
            max_attempts: Maximum frames to try
        
        Returns:
            dict: Result from best capture
        """
        best_result = None
        best_quality = 0.0
        
        for i, (frame, bbox) in enumerate(frames_with_bboxes[:max_attempts]):
            result = self.capture_and_save(
                frame, bbox, 
                f"{violation_code}_attempt{i}", 
                enhance=True
            )
            
            if result['success']:
                quality = result['quality_info'].get('quality_score', 0.0)
                
                if quality > best_quality:
                    best_quality = quality
                    best_result = result
        
        # Rename best file to final name
        if best_result and best_result['filepath']:
            final_path = os.path.join(
                self.storage_dir,
                f"{violation_code}_face.{self.image_format}"
            )
            try:
                os.rename(best_result['filepath'], final_path)
                best_result['filepath'] = final_path
                logger.info(f"Best face selected (quality: {best_quality:.3f})")
            except Exception as e:
                logger.error(f"Failed to rename best face: {e}")
        
        return best_result or {'success': False, 'filepath': None, 'quality_info': {}}

# Singleton instance
_face_capture = None

def get_face_capture():
    """Get or create face capture singleton"""
    global _face_capture
    if _face_capture is None:
        _face_capture = FaceCapture()
    return _face_capture

if __name__ == '__main__':
    # Test face capture
    print("Testing Face Capture Module...")
    fc = FaceCapture()
    
    # Create test image
    test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    test_bbox = [400, 200, 600, 400]
    
    result = fc.capture_and_save(test_frame, test_bbox, "TEST-001")
    
    if result['success']:
        print(f"✓ Test face saved: {result['filepath']}")
        print(f"  Quality: {result['quality_info']['quality_score']:.3f}")
    else:
        print("✗ Test failed")
