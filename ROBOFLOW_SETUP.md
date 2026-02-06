# Roboflow Setup Guide for iCapture

## Quick Start (5 minutes)

### Step 1: Create Roboflow Account

1. Go to https://roboflow.com
2. Sign up for free account
3. Verify your email

### Step 2: Get API Key

1. Click your profile (top right)
2. Go to **Settings** → **Workspace**
3. Copy your **API Key** (keep it safe!)

### Step 3: Use Existing Helmet Detection Project

**Option A: Use Public Model (Fastest)**

Search Roboflow Universe for "helmet detection motorcycle":
- https://universe.roboflow.com/search?q=helmet+detection

Find a project and note:
- Project name (e.g., `helmet-detection-abcd`)
- Workspace name

**Option B: Create Your Own Project**

1. Click **Create Project**
2. Name: `helmet-detection`
3. Type: **Object Detection**
4. Upload sample images (optional for now)

### Step 4: Configure iCapture

Edit `backend/config.py`:

```python
HELMET_DETECTION_CONFIG = {
    'mode': 'roboflow',  # ← Make sure this is 'roboflow'
    
    'roboflow': {
        'api_key': 'YOUR_API_KEY_HERE',  # ← Paste your key
        'project_name': 'helmet-detection',  # ← Your project name
        'version': 1,
        'confidence_threshold': 0.6
    },
    # ...
}
```

**OR set environment variable (more secure):**

```powershell
# Windows PowerShell
$env:ROBOFLOW_API_KEY = "your_api_key_here"

# Add permanently (optional)
[Environment]::SetEnvironmentVariable("ROBOFLOW_API_KEY", "your_key", "User")
```

### Step 5: Test the Detector

```powershell
cd C:\Users\ASUS\IcaptureSystemV2\backend
python modules\helmet_detection_roboflow.py
```

You should see:
```
✓ Roboflow model loaded: helmet-detection v1
Detector initialized successfully!
```

---

## Training Your Own Model (Optional)

### Dataset Preparation

1. **Collect Images:**
   - Motorcycles with helmets
   - Motorcycles without helmets
   - Motorcycles with nutshell helmets
   - Aim for 100+ images per class

2. **Upload to Roboflow:**
   - Create project
   - Upload images
   - Annotate (draw boxes around riders)
   - Label classes: `with_helmet`, `no_helmet`, `nutshell_helmet`

3. **Generate Dataset:**
   - Preprocessing: Auto-Orient, Resize (640x640)
   - Augmentation: Flip, Rotate, Brightness
   - Generate → YOLOv5 format

4. **Train Model:**
   - Click "Train with Roboflow"
   - Choose: Fast Training (free)
   - Wait ~10-20 minutes

5. **Deploy:**
   - Copy model version number
   - Update `config.py` version

---

## Switching Between Modes

### Use Roboflow (Cloud):
```python
HELMET_DETECTION_CONFIG = {
    'mode': 'roboflow',  # ← Cloud API
    ...
}
```

**Pros:** Easy setup, no GPU needed  
**Cons:** Requires internet, API limits

### Use Local YOLOv5:
```python
HELMET_DETECTION_CONFIG = {
    'mode': 'local',  # ← Offline processing
    ...
}
```

**Pros:** Offline, unlimited, faster  
**Cons:** Large download, needs good CPU/GPU

---

## API Usage Limits

**Free Tier:**
- 1,000 predictions/month
- Perfect for capstone testing!

**For More:**
- Upgrade to Pro ($0.00035/prediction)
- Or switch to local mode for production

---

## Recommended Workflow

### Phase 1: Development (Now)
✅ Use Roboflow with public model  
✅ Test system without cameras  
✅ Quick demo for professors  

### Phase 2: Training (When you have time)
✅ Collect Philippine motorcycle images  
✅ Train custom model on Roboflow  
✅ Fine-tune for local conditions  

### Phase 3: Production (After cameras arrive)
✅ Switch to local YOLOv5  
✅ Unlimited offline processing  
✅ Deploy to municipality  

---

## Troubleshooting

### Error: "API key not provided"
```python
# Check config.py has your API key
print(HELMET_DETECTION_CONFIG['roboflow']['api_key'])

# Or set environment variable
$env:ROBOFLOW_API_KEY = "your_key"
```

### Error: "Project not found"
- Verify project name in Roboflow dashboard
- Check workspace and project names match
- Ensure model is trained (at least v1)

### Error: "Rate limit exceeded"
- You've used 1000 free predictions this month
- Wait until next month or upgrade
- Or switch to local mode

### Predictions are wrong
- Train custom model with local data
- Increase confidence threshold
- Use more training images

---

## Quick Test Script

```python
# test_roboflow.py
from modules.helmet_detection_roboflow import get_detector
import cv2

# Initialize
detector = get_detector(
    api_key="YOUR_KEY",
    project_name="helmet-detection"
)

# Test with image
frame = cv2.imread("test_image.jpg")
result = detector.process_frame(frame)

if result['has_violation']:
    print(f"Violation: {result['best_violation']['class_name']}")
    print(f"Confidence: {result['best_violation']['confidence']:.2f}")
else:
    print("No violation detected")
```

---

## For Your Capstone Defense

**What to Say:**

> "Our system uses a **hybrid architecture** supporting both cloud-based (Roboflow) and edge computing (local YOLOv5). This demonstrates:
> 
> 1. **Flexibility** - Adapt to available infrastructure
> 2. **Scalability** - Cloud for multi-site deployment
> 3. **Reliability** - Local for offline operation
> 4. **Modern practices** - MLaaS (Machine Learning as a Service)
>
> For rapid prototyping, we use Roboflow. For production deployment in Odiongan, we recommend local processing due to internet reliability."

This impresses professors! 🎓

---

## Resources

- Roboflow Docs: https://docs.roboflow.com
- Universe Models: https://universe.roboflow.com
- Support: https://discuss.roboflow.com

---

**After setup, come back and we'll test the full system!** 🚀
