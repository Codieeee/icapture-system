# iCapture System - Performance Optimization Guide

## Overview

This guide provides strategies to optimize iCapture system performance for various scenarios including lighting conditions, motion blur, and false positive reduction.

---

## 🎥 Camera Optimization

### Lighting Requirements

**Daylight Operation:**
- **Minimum:** 500 lux (overcast day)
- **Optimal:** 1000-2000 lux (clear day)
- **Position:** Avoid direct sunlight on cameras (lens flare)

**Night Operation:**
- **IR Illuminators:** 850nm wavelength (invisible to human eye)
- **Power:** 50W minimum per camera
- **Distance:** Effective up to 20 meters
- **Alternative:** High-sensitivity cameras (0.01 lux minimum)

**Mixed Conditions:**
- Use cameras with WDR (Wide Dynamic Range)
- Enable auto-exposure with fast response
- Set exposure limits: 1/500s min, 1/60s max

### Motion Blur Reduction

**Camera Settings:**
- **Shutter Speed:** 1/500s minimum (1/1000s ideal)
- **Frame Rate:** 30 FPS minimum
- **Resolution:** 1080p (1920x1280)
- **Codec:** H.264 or MJPEG (lower latency)

**Detection Zone:**
- **Optimal Distance:** 5-15 meters from camera
- **Speed Limit:** Best accuracy below 40 km/h
- **Approach Angle:** Head-on (0-30° angle)

**Software Mitigation:**
```python
# In face_capture.py - already implemented
# Multi-frame capture: Takes 5 frames, selects sharpest
best_result = capture_best_of_multiple(frames_list, violation_code, max_attempts=5)
```

---

## 🤖 AI Model Optimization

### YOLOv5 Tuning

**Confidence Threshold:**
```python
# In config.py
YOLO_CONFIG = {
    'confidence_threshold': 0.6,  # Increase to 0.7 for fewer false positives
    'iou_threshold': 0.45,        # Lower to 0.35 for better separation
}
```

**GPU Acceleration:**
```python
# Enable CUDA if available
YOLO_CONFIG = {
    'device': 'cuda',  # 10-20x faster than CPU
    'img_size': 640,   # Reduce to 480 for speed, increase to 800 for accuracy
}

# Install CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu117
```

**Batch Processing:**
```python
# In helmet_detection.py
# Process multiple frames simultaneously (if using GPU)
PERFORMANCE_CONFIG = {
    'gpu_batch_size': 4  # Process 4 frames at once
}
```

### False Positive Mitigation

**Multi-Frame Verification:**
```python
# In violation_logic.py - already implemented
VIOLATION_CONFIG = {
    'consecutive_frames': 3  # Require 3 consecutive detections
}
```

**Temporal Filtering:**
```python
# Ignore detections too close together
VIOLATION_CONFIG = {
    'duplicate_window': 60  # Same plate can't trigger twice in 60 seconds
}
```

**Contextual Validation:**
- Check motorcycle presence before flagging helmet violation
- Verify rider is on moving vehicle (not pedestrian carrying helmet)
- Use plate detection as confirmation (motorcycle should have plate)

---

## 🔍 OCR Optimization

### Plate Image Preprocessing

**Already Implemented in `plate_recognition.py`:**
```python
def preprocess_plate_image(plate_img):
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(denoised, 255, ...)
    return processed
```

**Additional Enhancements:**
```python
# Increase plate region size before OCR
plate_enlarged = cv2.resize(plate_img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

# Enhance contrast
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(gray)
```

### Tesseract Configuration

**Custom Training for Philippine Plates:**
```python
OCR_CONFIG = {
    'config': '--psm 7 --oem 3',  # PSM 7 = single line
    # Add custom character whitelist (Philippine plates use specific patterns)
    'philippine_plate_pattern': r'^[A-Z]{3}-?\d{3,4}$'
}
```

**Confidence Filtering:**
```python
# In plate_recognition.py
OCR_CONFIG = {
    'min_confidence': 0.5  # Increase to 0.6-0.7 for higher accuracy
}
```

---

## 💾 Database Optimization

### Indexing Strategy

**Already in `schema.sql`:**
```sql
CREATE INDEX idx_plate_number ON violations(plate_number);
CREATE INDEX idx_violation_datetime ON violations(violation_datetime);
CREATE INDEX idx_status ON violations(status);
```

**Query Optimization:**
```sql
# Use EXPLAIN to analyze slow queries
EXPLAIN SELECT * FROM violations WHERE plate_number = 'ABC-1234';

# Add composite indexes for common filters
CREATE INDEX idx_status_date ON violations(status, violation_datetime);
```

### Connection Pooling

**Already Implemented:**
```python
# In database.py
DATABASE_CONFIG = {
    'pool_size': 10,      # Maintain 10 active connections
    'max_overflow': 20    # Allow 20 additional connections under load
}
```

### Data Archiving

**Monthly Maintenance:**
```sql
# Archive violations older than 1 year
CREATE TABLE violations_archive LIKE violations;

INSERT INTO violations_archive 
SELECT * FROM violations 
WHERE violation_datetime < DATE_SUB(NOW(), INTERVAL 1 YEAR);

DELETE FROM violations 
WHERE violation_datetime < DATE_SUB(NOW(), INTERVAL 1 YEAR);

# Reclaim space
OPTIMIZE TABLE violations;
```

---

## ⚡ System Performance

### Processing Rate Control

**Adaptive FPS:**
```python
# In config.py
PERFORMANCE_CONFIG = {
    'processing_fps': 15,  # Lower = less CPU, higher = more responsive
    'frame_skip': 2,       # Process every 2nd frame under load
    'max_cpu_percent': 80, # Throttle if CPU exceeds 80%
}
```

**Load Balancing:**
```python
import psutil

def should_process_frame():
    cpu_percent = psutil.cpu_percent()
    if cpu_percent > 80:
        return False  # Skip frame
    return True
```

### Memory Management

**Image Storage:**
```python
# In config.py
STORAGE_CONFIG = {
    'max_image_size': (800, 600),  # Resize large images
    'jpeg_quality': 85,             # Reduce to 70-75 to save space
}
```

**Cleanup Old Data:**
```python
# Delete violation images older than 6 months
import os
from datetime import datetime, timedelta

old_date = datetime.now() - timedelta(days=180)
for file in os.listdir('data/violations/faces/'):
    if os.path.getmtime(file) < old_date.timestamp():
        os.remove(file)
```

### Threading Optimization

**Already Implemented:**
```python
# Separate threads for:
# 1. Video capture (video_capture.py)
# 2. Violation processing (app.py)
# 3. Flask API server (app.py)

# This prevents camera lag from blocking API responses
```

---

## 📊 Monitoring & Benchmarking

### FPS Measurement

```python
import time

frame_count = 0
start_time = time.time()

while True:
    # Process frame
    process_frame()
    frame_count += 1
    
    # Calculate FPS every 30 frames
    if frame_count % 30 == 0:
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        print(f"Processing FPS: {fps:.2f}")
```

### Latency Tracking

```python
# In violation_logic.py
import time

start = time.time()
# Detection
end_detection = time.time()
# OCR
end_ocr = time.time()
# Database
end_db = time.time()

logger.info(f"Timing: Detection={end_detection-start:.3f}s, OCR={end_ocr-end_detection:.3f}s, DB={end_db-end_ocr:.3f}s")
```

### Resource Monitoring

```python
import psutil

def log_system_stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    logger.info(f"System: CPU={cpu}%, RAM={ram}%, Disk={disk}%")
```

---

## 🎯 Recommended Settings by Environment

### Urban Road (High Traffic)
```python
YOLO_CONFIG['confidence_threshold'] = 0.7  # Higher threshold
VIOLATION_CONFIG['consecutive_frames'] = 3  # Multi-frame verification
VIOLATION_CONFIG['duplicate_window'] = 60   # Avoid spam
PERFORMANCE_CONFIG['processing_fps'] = 10   # Lower FPS for high load
```

### Rural Road (Low Traffic)
```python
YOLO_CONFIG['confidence_threshold'] = 0.6  # Standard threshold
VIOLATION_CONFIG['consecutive_frames'] = 2  # Faster response
VIOLATION_CONFIG['duplicate_window'] = 30   # Shorter window
PERFORMANCE_CONFIG['processing_fps'] = 20   # Higher FPS
```

### Night Operation
```python
YOLO_CONFIG['confidence_threshold'] = 0.65  # Slightly higher (noise compensation)
VIOLATION_CONFIG['consecutive_frames'] = 4  # More verification
# Enable image enhancement
face_capture.enhance_face(brightness=1.2, contrast=1.3)
```

---

## 🔧 Troubleshooting Performance

### High CPU Usage
- Reduce `processing_fps` to 10-12
- Enable `frame_skip` to 2 or 3
- Use GPU acceleration (CUDA)
- Close other applications

### High Memory Usage
- Reduce `max_image_size` to (640, 480)
- Lower `jpeg_quality` to 70
- Archive old violations
- Reduce `pool_size` in database

### Slow Detection
- Use GPU (10-20x speedup)
- Reduce `img_size` to 480
- Disable unnecessary logging
- Process every 2nd frame

### High False Positives
- Increase `confidence_threshold` to 0.7
- Increase `consecutive_frames` to 4
- Improve camera lighting
- Retrain model with better data

### High False Negatives
- Lower `confidence_threshold` to 0.55
- Reduce `consecutive_frames` to 2
- Improve camera positioning
- Add more training data

---

## ✅ Performance Checklist

- [ ] GPU acceleration enabled (if available)
- [ ] Camera shutter speed ≥ 1/500s
- [ ] Lighting ≥ 500 lux minimum
- [ ] Processing FPS tuned for load (10-20)
- [ ] Confidence threshold optimized (0.6-0.7)
- [ ] Multi-frame verification enabled (3 frames)
- [ ] Duplicate prevention active (60s window)
- [ ] Database indexes verified
- [ ] Image compression optimized (JPEG 85%)
- [ ] Old data archived monthly
- [ ] System monitoring active

---

**Expected Performance Targets:**

| Metric | Target | Notes |
|--------|--------|-------|
| Detection Accuracy | > 90% | With proper lighting |
| Processing Time | < 500ms | Per violation |
| False Positive Rate | < 5% | Multi-frame verification |
| OCR Accuracy | > 85% | Clean plates |
| System FPS | 10-20 | Real-time processing |
| Uptime | > 95% | With auto-reconnect |

---

For specific optimization scenarios, consult the source code comments in each module.
