# iCapture System - Deployment Guide

## Quick Start (Development)

### 1. Install Prerequisites

**Python 3.8+**
```bash
python --version  # Should show 3.8 or higher
```

**MySQL 8.0+**
```bash
mysql --version  # Verify installation
```

**Tesseract OCR**
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

### 2. Setup Database

```bash
# Connect to MySQL
mysql -u root -p

# Create database and run schema
CREATE DATABASE icapture_db;
exit;

# Import schema
mysql -u root -p icapture_db < database/schema.sql
```

### 3. Install Python Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 4. Configure System

Edit `backend/config.py`:

```python
# Update database credentials
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'icapture_db'
}

# Update camera indices (test first)
CAMERA_CONFIG = {
    'wide_angle': {
        'stream_url': 0  # First USB camera
    },
    'plate': {
        'stream_url': 1  # Second USB camera
    }
}

# Windows: Update Tesseract path
OCR_CONFIG = {
    'tesseract_cmd': r'C:\Program Files\Tesseract-OCR\tesseract.exe'
}
```

### 5. Test Camera Setup

```bash
cd backend
python -c "import cv2; import time; cap = cv2.VideoCapture(0); print('Camera 0:', cap.isOpened()); cap = cv2.VideoCapture(1); print('Camera 1:', cap.isOpened())"
```

### 6. Run System

```bash
cd backend
python app.py
```

Navigate to: `http://localhost:5000`

---

## Production Deployment

### Hardware Requirements

**Minimum:**
- CPU: Intel i5 / AMD Ryzen 5 (4 cores)
- RAM: 8GB
- Storage: 50GB SSD
- GPU: None (CPU mode)
- Cameras: 2x USB 3.0 cameras (1080p)

**Recommended:**
- CPU: Intel i7 / AMD Ryzen 7 (6+ cores)
- RAM: 16GB
- Storage: 256GB SSD
- GPU: NVIDIA GTX 1650 or higher (4GB VRAM)
- Cameras: 2x IP cameras (1080p, 30fps)

### Software Requirements

- Windows 10/11 or Ubuntu 20.04 LTS
- Python 3.8 - 3.10
- MySQL 8.0
- CUDA 11.7+ (for GPU)
- Tesseract 4.x

### Production Configuration

**1. Security**

Change default admin password:
```sql
USE icapture_db;
UPDATE admin_users 
SET password_hash = SHA2('your_new_secure_password', 256)
WHERE username = 'admin';
```

**2. Flask Production Mode**

Edit `config.py`:
```python
FLASK_CONFIG = {
    'debug': False,  # IMPORTANT: Set to False
    'secret_key': 'generate-random-secure-key-here'
}
```

**3. Database Optimization**

```sql
# Add indexes (already in schema, but verify)
SHOW INDEX FROM violations;

# Enable query cache
SET GLOBAL query_cache_size = 67108864;  # 64MB
```

**4. Use Production Server**

Install Gunicorn:
```bash
pip install gunicorn
```

Run with Gunicorn:
```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

**5. Nginx Reverse Proxy (Optional)**

Install Nginx and configure:
```nginx
server {
    listen 80;
    server_name your_domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/cameras/feed {
        proxy_pass http://127.0.0.1:5000;
        proxy_buffering off;
    }
}
```

**6. Auto-Start on Boot (Windows)**

Create batch file `start_icapture.bat`:
```batch
@echo off
cd C:\path\to\IcaptureSystemV2\backend
call venv\Scripts\activate
python app.py
```

Add to Windows Task Scheduler:
- Trigger: At system startup
- Action: Run `start_icapture.bat`
- Run as administrator

**7. Auto-Start on Boot (Linux)**

Create systemd service `/etc/systemd/system/icapture.service`:
```ini
[Unit]
Description=iCapture System
After=network.target mysql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/IcaptureSystemV2/backend
ExecStart=/path/to/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable icapture
sudo systemctl start icapture
```

---

## Camera Setup

### USB Cameras

1. Connect cameras to USB 3.0 ports
2. Test with built-in tool:
   ```bash
   python backend/modules/video_capture.py
   ```
3. Update `config.py` with correct indices

### IP Cameras (RTSP)

Update `config.py`:
```python
CAMERA_CONFIG = {
    'wide_angle': {
        'stream_url': 'rtsp://username:password@192.168.1.100:554/stream1'
    },
    'plate': {
        'stream_url': 'rtsp://username:password@192.168.1.101:554/stream1'
    }
}
```

### Camera Positioning

**Wide-Angle Camera:**
- Height: 4-5 meters 
- Angle: 30-45° downward
- Distance: 10-15 meters from detection zone
- Lighting: Minimum 500 lux

**Plate Camera:**
- Height: 2-3 meters
- Angle: 15-30° downward
- Distance: 5-10 meters from plates
- Zoom: Adjusted to capture plates at 800x200 pixels minimum

---

## YOLOv5 Model Training

### Prepare Dataset

1. Collect images of motorcycles with:
   - Riders with helmets (compliant)
   - Riders without helmets (violation)
   - Riders with nutshell helmets (violation)

2. Annotate using [Roboflow](https://roboflow.com/) or [LabelImg](https://github.com/tzutalin/labelImg)

3. Export in YOLOv5 format

### Train Model

```bash
# Clone YOLOv5
git clone https://github.com/ultralytics/yolov5
cd yolov5
pip install -r requirements.txt

# Create data.yaml
cat > data.yaml << EOF
train: /path/to/train/images
val: /path/to/val/images

nc: 3
names: ['with_helmet', 'no_helmet', 'nutshell_helmet']
EOF

# Train
python train.py --data data.yaml --weights yolov5s.pt --epochs 100 --batch 16

# Copy trained weights
cp runs/train/exp/weights/best.pt ../IcaptureSystemV2/backend/models/yolov5/
```

### Test Model

```bash
cd ../IcaptureSystemV2/backend
python modules/helmet_detection.py
```

---

## Backup & Maintenance

### Daily Backup

```bash
# Backup database
mysqldump -u root -p icapture_db > backup_$(date +%Y%m%d).sql

# Backup violation images
tar -czf violations_$(date +%Y%m%d).tar.gz data/violations/
```

### Log Rotation

Edit `config.py`:
```python
LOGGING_CONFIG = {
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5  # Keep 5 backups
}
```

### Database Maintenance

```sql
# Monthly archiving of old violations (> 1 year)
CREATE TABLE violations_archive LIKE violations;
INSERT INTO violations_archive 
SELECT * FROM violations 
WHERE violation_datetime < DATE_SUB(NOW(), INTERVAL 1 YEAR);

DELETE FROM violations 
WHERE violation_datetime < DATE_SUB(NOW(), INTERVAL 1 YEAR);

OPTIMIZE TABLE violations;
```

---

## Monitoring

### Check System Health

```bash
curl http://localhost:5000/api/health
```

### View Logs

```bash
# Application logs
tail -f data/logs/icapture_*.log

# System logs (database)
mysql -u root -p icapture_db -e "SELECT * FROM system_logs ORDER BY created_at DESC LIMIT 20;"
```

### Performance Monitoring

```bash
# Install psutil
pip install psutil

# Monitor resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%'); print(f'RAM: {psutil.virtual_memory().percent}%')"
```

---

## Troubleshooting

See README.md Troubleshooting section for common issues.

For support: Check system logs first (`data/logs/`)

---

**Deployment Checklist:**

- [ ] Database created and schema loaded
- [ ] Python dependencies installed
- [ ] Cameras tested and positioned
- [ ] YOLOv5 model trained/loaded
- [ ] Tesseract OCR installed
- [ ] Config.py updated (database, cameras)
- [ ] Default password changed
- [ ] Production mode enabled (debug=False)
- [ ] Auto-start configured
- [ ] Backup strategy implemented
- [ ] System tested end-to-end
