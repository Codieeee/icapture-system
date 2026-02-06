"""
License Plate Recognition Module for iCapture System
OCR system optimized for Philippine license plates
"""

import cv2
import numpy as np
import pytesseract
import re
import sys
from pathlib import Path
from datetime import datetime
import os

sys.path.append(str(Path(__file__).parent.parent))

from config import OCR_CONFIG, STORAGE_CONFIG
from utils.logger import get_logger
from utils.image_processing import preprocess_for_ocr, save_image

logger = get_logger('plate_recognition')

class PlateRecognizer:
    """License plate detection and OCR for Philippine plates"""
    
    def __init__(self, tesseract_cmd=None, min_confidence=0.5):
        """
        Initialize plate recognizer
        
        Args:
            tesseract_cmd: Path to tesseract executable
            min_confidence: Minimum OCR confidence (0-1)
        """
        # Set Tesseract path
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif OCR_CONFIG['tesseract_cmd']:
            pytesseract.pytesseract.tesseract_cmd = OCR_CONFIG['tesseract_cmd']
        
        self.min_confidence = min_confidence or OCR_CONFIG['min_confidence']
        self.ocr_config = OCR_CONFIG['config']
        self.plate_pattern = re.compile(OCR_CONFIG['philippine_plate_pattern'])
        self.storage_dir = STORAGE_CONFIG['plate_dir']
        
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logger.info("PlateRecognizer initialized")
    
    def detect_plate_region(self, frame):
        """
        Detect license plate region in frame
        Uses edge detection and contour analysis
        
        Args:
            frame: numpy array (BGR)
        
        Returns:
            list: Detected plate regions [(x, y, w, h), ...]
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Bilateral filter to reduce noise while keeping edges
            filtered = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Edge detection
            edged = cv2.Canny(filtered, 30, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Sort contours by area (largest first)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
            
            plate_regions = []
            
            for contour in contours:
                # Approximate contour
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.018 * peri, True)
                
                # Look for rectangular contours (4 points)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    
                    # Check aspect ratio (Philippine plates ~3:1 to 4:1)
                    aspect_ratio = w / float(h) if h > 0 else 0
                    
                    # Check minimum size
                    if aspect_ratio > 2.0 and aspect_ratio < 5.0 and w > 80 and h > 20:
                        plate_regions.append((x, y, w, h))
            
            return plate_regions
        except Exception as e:
            logger.error(f"Plate detection error: {e}")
            return []
    
    def preprocess_plate_image(self, plate_img):
        """
        Preprocess plate image for OCR
        
        Args:
            plate_img: numpy array (BGR)
        
        Returns:
            Preprocessed image
        """
        return preprocess_for_ocr(plate_img)
    
    def recognize_text(self, plate_img):
        """
        Extract text from plate image using Tesseract OCR
        
        Args:
            plate_img: numpy array (BGR or grayscale)
        
        Returns:
            dict: {
                'text': str,
                'confidence': float,
                'raw_text': str
            }
        """
        try:
            # Preprocess
            processed = self.preprocess_plate_image(plate_img)
            
            # Get OCR data with confidence
            ocr_data = pytesseract.image_to_data(
                processed,
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and confidence
            texts = []
            confidences = []
            
            for i, text in enumerate(ocr_data['text']):
                if text.strip():  # Ignore empty strings
                    texts.append(text)
                    conf = int(ocr_data['conf'][i])
                    if conf > 0:
                        confidences.append(conf)
            
            # Combine text
            raw_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Clean and format text
            cleaned_text = self.clean_plate_text(raw_text)
            
            return {
                'text': cleaned_text,
                'confidence': avg_confidence / 100.0,  # Normalize to 0-1
                'raw_text': raw_text
            }
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'raw_text': ''
            }
    
    def clean_plate_text(self, text):
        """
        Clean and format OCR text to match Philippine plate format
        
        Args:
            text: Raw OCR text
        
        Returns:
            Cleaned plate number
        """
        # Remove spaces and special characters except hyphen
        text = re.sub(r'[^A-Z0-9-]', '', text.upper())
        
        # Correct common OCR errors
        corrections = {
            'O': '0', 'I': '1', 'L': '1',
            'S': '5', 'Z': '2', 'B': '8'
        }
        
        # Apply corrections intelligently (letters in first part, numbers in second)
        parts = text.split('-')
        if len(parts) == 2:
            # First part should be letters (3 chars)
            letter_part = parts[0][:3]
            # Second part should be numbers (3-4 chars)
            number_part = parts[1][:4]
            
            # Apply corrections to number part
            for old, new in corrections.items():
                number_part = number_part.replace(old, new)
            
            text = f"{letter_part}-{number_part}"
        
        return text
    
    def validate_philippine_format(self, plate_text):
        """
        Validate if text matches Philippine plate format
        
        Args:
            plate_text: Plate number string
        
        Returns:
            bool: True if valid format
        """
        return bool(self.plate_pattern.match(plate_text))
    
    def save_plate_image(self, plate_img, violation_code):
        """
        Save plate image to disk
        
        Args:
            plate_img: numpy array
            violation_code: Violation identifier
        
        Returns:
            str: Saved file path or None
        """
        try:
            filename = f"{violation_code}_plate.{STORAGE_CONFIG['image_format']}"
            filepath = os.path.join(self.storage_dir, filename)
            
            success = save_image(plate_img, filepath, quality=STORAGE_CONFIG['jpeg_quality'])
            
            if success:
                logger.info(f"Plate image saved: {filepath}")
                return filepath
            return None
        except Exception as e:
            logger.error(f"Save error: {e}")
            return None
    
    def recognize_plate(self, frame, violation_code=None, save_image_file=True):
        """
        Complete plate recognition workflow
        
        Args:
            frame: Input frame (from plate camera)
            violation_code: Optional violation code for saving
            save_image_file: Whether to save plate image
        
        Returns:
            dict: {
                'plate_number': str or None,
                'confidence': float,
                'is_valid': bool,
                'plate_image_path': str or None,
                'regions_found': int
            }
        """
        try:
            # Detect plate regions
            plate_regions = self.detect_plate_region(frame)
            
            if not plate_regions:
                logger.warning("No plate regions detected")
                return {
                    'plate_number': None,
                    'confidence': 0.0,
                    'is_valid': False,
                    'plate_image_path': None,
                    'regions_found': 0
                }
            
            # Try OCR on each detected region
            best_result = None
            best_confidence = 0.0
            best_plate_img = None
            
            for x, y, w, h in plate_regions:
                # Crop plate region
                plate_img = frame[y:y+h, x:x+w]
                
                # Run OCR
                result = self.recognize_text(plate_img)
                
                # Check if valid and better than previous
                is_valid = self.validate_philippine_format(result['text'])
                
                if is_valid and result['confidence'] > best_confidence:
                    best_confidence = result['confidence']
                    best_result = result
                    best_plate_img = plate_img
            
            # Save best plate image if found
            plate_image_path = None
            if best_result and best_plate_img is not None and save_image_file and violation_code:
                plate_image_path = self.save_plate_image(best_plate_img, violation_code)
            
            if best_result:
                logger.info(f"Plate recognized: {best_result['text']} (conf: {best_result['confidence']:.3f})")
                return {
                    'plate_number': best_result['text'],
                    'confidence': best_result['confidence'],
                    'is_valid': True,
                    'plate_image_path': plate_image_path,
                    'regions_found': len(plate_regions)
                }
            else:
                logger.warning("No valid plate number recognized")
                return {
                    'plate_number': None,
                    'confidence': 0.0,
                    'is_valid': False,
                    'plate_image_path': None,
                    'regions_found': len(plate_regions)
                }
        except Exception as e:
            logger.error(f"Plate recognition error: {e}")
            return {
                'plate_number': None,
                'confidence': 0.0,
                'is_valid': False,
                'plate_image_path': None,
                'regions_found': 0
            }

# Singleton instance
_recognizer = None

def get_recognizer():
    """Get or create plate recognizer singleton"""
    global _recognizer
    if _recognizer is None:
        _recognizer = PlateRecognizer()
    return _recognizer

if __name__ == '__main__':
    # Test plate recognition
    print("Testing Plate Recognition Module...")
    recognizer = PlateRecognizer()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        print("Press 'q' to quit, SPACE to capture")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Show frame
            cv2.imshow('Plate Recognition (Press SPACE)', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # Space bar
                print("\nProcessing...")
                result = recognizer.recognize_plate(frame, save_image_file=False)
                print(f"Plate: {result['plate_number']}")
                print(f"Confidence: {result['confidence']:.3f}")
                print(f"Valid: {result['is_valid']}")
        
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("Failed to open camera")
