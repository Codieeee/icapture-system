"""
Image Processing Utilities for iCapture System
Common image operations: enhancement, quality assessment, blur detection
"""

import cv2
import numpy as np
from PIL import Image
import os

def enhance_image(image, brightness=1.0, contrast=1.0):
    """
    Enhance image brightness and contrast
    
    Args:
        image: numpy array (BGR)
        brightness: Multiplier for brightness (1.0 = no change)
        contrast: Multiplier for contrast (1.0 = no change)
    
    Returns:
        Enhanced image
    """
    enhanced = cv2.convertScaleAbs(image, alpha=contrast, beta=int((brightness - 1) * 255))
    return enhanced

def is_blurry(image, threshold=100.0):
    """
    Detect motion blur using Laplacian variance
    
    Args:
        image: numpy array (BGR or grayscale)
        threshold: Variance threshold (lower = more blurry)
    
    Returns:
        tuple: (is_blurry: bool, variance: float)
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold, laplacian_var

def assess_quality(image):
    """
    Assess overall image quality (0-1 score)
    Combines sharpness, brightness, and contrast
    
    Args:
        image: numpy array (BGR)
    
    Returns:
        float: Quality score (0-1, higher is better)
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Sharpness (Laplacian variance)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_score = min(sharpness / 500.0, 1.0)  # Normalize
    
    # Brightness (mean pixel value)
    brightness = np.mean(gray)
    brightness_score = 1.0 - abs(brightness - 127.5) / 127.5  # Ideal is mid-gray
    
    # Contrast (standard deviation)
    contrast = np.std(gray)
    contrast_score = min(contrast / 75.0, 1.0)  # Normalize
    
    # Weighted average
    quality = (sharpness_score * 0.5 + brightness_score * 0.25 + contrast_score * 0.25)
    return quality

def preprocess_for_ocr(image):
    """
    Preprocess plate image for better OCR accuracy
    
    Args:
        image: numpy array (BGR)
    
    Returns:
        Preprocessed grayscale image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter (edge-preserving denoising)
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        11, 2
    )
    
    # Morphological operations to clean up
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return processed

def crop_with_margin(image, bbox, margin_percent=0.1):
    """
    Crop image with bounding box and add margin
    
    Args:
        image: numpy array (BGR)
        bbox: tuple (x1, y1, x2, y2) in pixels
        margin_percent: Margin as percentage of bbox size
    
    Returns:
        Cropped image with margin
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox
    
    # Calculate margins
    width = x2 - x1
    height = y2 - y1
    margin_x = int(width * margin_percent)
    margin_y = int(height * margin_percent)
    
    # Apply margins with boundary checks
    x1 = max(0, x1 - margin_x)
    y1 = max(0, y1 - margin_y)
    x2 = min(w, x2 + margin_x)
    y2 = min(h, y2 + margin_y)
    
    return image[y1:y2, x1:x2]

def resize_image(image, max_size=(800, 600), maintain_aspect=True):
    """
    Resize image to fit within max dimensions
    
    Args:
        image: numpy array (BGR)
        max_size: tuple (max_width, max_height)
        maintain_aspect: Keep aspect ratio
    
    Returns:
        Resized image
    """
    h, w = image.shape[:2]
    max_w, max_h = max_size
    
    if not maintain_aspect:
        return cv2.resize(image, max_size)
    
    # Calculate scaling factor
    scale = min(max_w / w, max_h / h)
    
    if scale >= 1.0:
        return image  # No need to resize
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

def save_image(image, filepath, quality=85):
    """
    Save image with JPEG compression
    
    Args:
        image: numpy array (BGR)
        filepath: Output file path
        quality: JPEG quality (0-100)
    
    Returns:
        bool: Success status
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save with compression
        cv2.imwrite(filepath, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

def draw_bbox(image, bbox, label='', color=(0, 255, 0), thickness=2):
    """
    Draw bounding box with label on image
    
    Args:
        image: numpy array (BGR)
        bbox: tuple (x1, y1, x2, y2)
        label: Text label to display
        color: BGR color tuple
        thickness: Line thickness
    
    Returns:
        Image with drawn bbox
    """
    x1, y1, x2, y2 = [int(v) for v in bbox]
    
    # Draw rectangle
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # Draw label if provided
    if label:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        # Get text size for background
        (text_w, text_h), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        
        # Draw background rectangle
        cv2.rectangle(image, (x1, y1 - text_h - 10), (x1 + text_w, y1), color, -1)
        
        # Draw text
        cv2.putText(image, label, (x1, y1 - 5), font, font_scale, (255, 255, 255), font_thickness)
    
    return image

if __name__ == '__main__':
    # Test image processing functions
    print("Image Processing Utilities - Test")
    test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    print(f"Quality Score: {assess_quality(test_img):.3f}")
    is_blur, variance = is_blurry(test_img)
    print(f"Blurry: {is_blur}, Variance: {variance:.2f}")
