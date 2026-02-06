"""
Configuration Management for iCapture System
Centralizes all system settings and environment variables
"""

import os
from pathlib import Path

# ============================================
# Base Directories
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / 'backend'
DATA_DIR = BASE_DIR / 'data'
FRONTEND_DIR = BASE_DIR / 'frontend'

# Create data directories if they don't exist
(DATA_DIR / 'violations' / 'faces').mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'violations' / 'plates').mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'logs').mkdir(parents=True, exist_ok=True)

# ============================================
# Database Configuration
# ============================================
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),  # Set your MySQL password
    'database': os.getenv('DB_NAME', 'icapture_db'),
    'charset': 'utf8mb4',
    'autocommit': False,
    'pool_size': 10,  # Connection pool size
    'max_overflow': 20
}

# ============================================
# Camera Configuration
# ============================================
CAMERA_CONFIG = {
    'wide_angle': {
        'camera_id': 'CAM-WA-001',
        'stream_url': None,  # Disabled for testing without cameras
        'fps': 30,
        'resolution': (1280, 720),  # Width x Height
        'location': 'National Road, Odiongan'
    },
    'plate': {
        'camera_id': 'CAM-PL-001',
        'stream_url': None,  # Disabled - no second camera
        'fps': 30,
        'resolution': (1280, 720),
        'location': 'National Road, Odiongan'
    }
}

# Camera reconnection settings
CAMERA_RETRY_ATTEMPTS = 5
CAMERA_RETRY_DELAY = 2  # seconds

# ============================================
# Helmet Detection Configuration
# ============================================
HELMET_DETECTION_CONFIG = {
    # Detection mode: 'roboflow' or 'local'
    'mode': 'roboflow',  # Switch to 'local' for offline YOLOv5
    
    # Roboflow Cloud API Settings (for mode='roboflow')
    'roboflow': {
        'api_key': os.getenv('ROBOFLOW_API_KEY', 'your_roboflow_api_key_here'),
        'project_name': 'helmet-detection',  # Your Roboflow project name
        'version': 1,  # Model version
        'confidence_threshold': 0.6
    },
    
    # Local YOLOv5 Settings (for mode='local')
    'local': {
        'model_path': str(BACKEND_DIR / 'models' / 'yolov5' / 'best.pt'),
        'device': 'cpu',  # Will auto-detect GPU in detector module
        'img_size': 640,
        'confidence_threshold': 0.6,
        'iou_threshold': 0.45
    },
    
    # Common settings
    'classes': ['with_helmet', 'no_helmet', 'nutshell_helmet']
}

# Backward compatibility for modules still expecting YOLO_CONFIG
# This reconstructs the original YOLO_CONFIG structure from the new HELMET_DETECTION_CONFIG
YOLO_CONFIG = {
    'violation_classes': ['no_helmet', 'nutshell_helmet']
}

# ============================================
# OCR Configuration (Tesseract)
# ============================================
OCR_CONFIG = {
    'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows path
    # For Linux/Mac: '/usr/bin/tesseract' or just 'tesseract'
    'config': '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
    'min_confidence': 0.5,  # Minimum OCR confidence
    'philippine_plate_pattern': r'^[A-Z]{3}-?\d{3,4}$'  # XXX-#### or XXX-###
}

# ============================================
# Violation Logic Configuration
# ============================================
VIOLATION_CONFIG = {
    'duplicate_window': 60,  # seconds - ignore same plate within this time
    'consecutive_frames': 3,  # Number of consecutive detections required
    'max_violations_per_minute': 10,  # System overload protection
    'face_quality_threshold': 0.5,  # Minimum face image quality
    'plate_quality_threshold': 0.4  # Minimum plate image quality
}

# ============================================
# Image Storage Configuration
# ============================================
STORAGE_CONFIG = {
    'face_dir': str(DATA_DIR / 'violations' / 'faces'),
    'plate_dir': str(DATA_DIR / 'violations' / 'plates'),
    'image_format': 'jpg',
    'jpeg_quality': 85,  # JPEG compression quality (0-100)
    'max_image_size': (800, 600),  # Max dimensions for stored images
}

# ============================================
# Flask API Configuration
# ============================================
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,  # Set to False in production
    'threaded': True,
    'secret_key': os.getenv('SECRET_KEY', 'change-this-in-production-icapture-2024')
}

# CORS settings
CORS_CONFIG = {
    'origins': ['http://localhost:5000', 'http://127.0.0.1:5000'],
    'methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'allow_headers': ['Content-Type', 'Authorization']
}

# ============================================
# Logging Configuration
# ============================================
LOGGING_CONFIG = {
    'log_dir': str(DATA_DIR / 'logs'),
    'log_file': 'icapture.log',
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_bytes': 10 * 1024 * 1024,  # 10MB per log file
    'backup_count': 5  # Keep 5 backup log files
}

# ============================================
# Performance Configuration
# ============================================
PERFORMANCE_CONFIG = {
    'processing_fps': 15,  # Actual processing rate (lower than camera FPS)
    'frame_skip': 2,  # Process every Nth frame when under load
    'gpu_batch_size': 4,  # Batch size for GPU processing
    'enable_gpu': True,  # Use GPU acceleration if available
    'max_cpu_percent': 80,  # Reduce processing if CPU exceeds this
    'max_memory_percent': 80  # Reduce processing if memory exceeds this
}

# ============================================
# Dashboard Configuration
# ============================================
DASHBOARD_CONFIG = {
    'refresh_interval': 5,  # seconds - auto-refresh interval
    'violations_per_page': 20,  # Pagination
    'max_live_violations': 100,  # Maximum violations shown in live table
    'session_timeout': 3600,  # 1 hour in seconds
}

# ============================================
# Violation Code Generation
# ============================================
def generate_violation_code():
    """Generate unique violation code in format: VL-YYYYMMDD-####"""
    from datetime import datetime
    import random
    date_str = datetime.now().strftime('%Y%m%d')
    random_num = random.randint(1000, 9999)
    return f"VL-{date_str}-{random_num}"

# ============================================
# Environment Check
# ============================================
def check_environment():
    """Verify required directories and settings"""
    issues = []
    
    # Check directories
    required_dirs = [
        DATA_DIR / 'violations' / 'faces',
        DATA_DIR / 'violations' / 'plates',
        DATA_DIR / 'logs',
        BACKEND_DIR / 'models' / 'yolov5'
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            issues.append(f"Missing directory: {dir_path}")
    
    # Check YOLOv5 model
    model_path = Path(YOLO_CONFIG['model_path'])
    if not model_path.exists():
        issues.append(f"YOLOv5 model not found: {model_path}")
    
    # Check Tesseract (on Windows)
    tesseract_path = Path(OCR_CONFIG['tesseract_cmd'])
    if os.name == 'nt' and not tesseract_path.exists():
        issues.append(f"Tesseract not found: {tesseract_path}")
    
    return issues

if __name__ == '__main__':
    print("iCapture System Configuration")
    print("=" * 50)
    print(f"Base Directory: {BASE_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Database: {DATABASE_CONFIG['database']} @ {DATABASE_CONFIG['host']}")
    print(f"YOLOv5 Model: {YOLO_CONFIG['model_path']}")
    print(f"Processing FPS: {PERFORMANCE_CONFIG['processing_fps']}")
    print(f"\nEnvironment Check:")
    issues = check_environment()
    if issues:
        print("⚠ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ All checks passed!")
