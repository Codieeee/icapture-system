# iCapture System - Quick Start Guide

## 🚀 Current Status

Your system now supports **TWO detection modes**:

1. ✅ **Roboflow** (Cloud API) - Quick setup, test NOW
2. ✅ **Local YOLOv5** - Full offline system (after pip install completes)

---

## Option 1: Start with Roboflow (5 minutes)

### Step 1: Get Roboflow API Key

1. Go to https://roboflow.com and sign up (free)
2. Settings → Workspace → Copy your **API Key**

### Step 2: Configure iCapture

Edit `backend/config.py` line 70:

```python
'api_key': 'YOUR_ACTUAL_KEY_HERE',  # Replace this!
```

### Step 3: Import LTO Database

```powershell
cd C:\Users\ASUS\IcaptureSystemV2
Get-Content database\lto_simulation.sql | C:\xampp\mysql\bin\mysql.exe -u root icapture_db
```

### Step 4: Run System

```powershell
cd backend
python app.py
```

Open: http://localhost:5000

**You're DONE!** System is running with Roboflow. 🎉

---

## Option 2: Wait for Local YOLOv5 (After pip install)

### When pip install finishes:

```powershell
# Check if it finished
pip list | findstr torch

# If installed, switch to local mode
# Edit backend/config.py line 67:
'mode': 'local',  # Changed from 'roboflow'

# Run system
python app.py
```

---

## Switching Modes

**To use Roboflow (cloud):**
```python
# backend/config.py
'mode': 'roboflow',
```

**To use Local YOLOv5 (offline):**
```python
# backend/config.py
'mode': 'local',
```

No other code changes needed!

---

## Testing Without Cameras

Since you don't have cameras yet, the system will show:
- ✅ Dashboard loads
- ✅ Database works
- ✅ API responds
- ⚠️ Camera feeds show "disconnected" (normal - no hardware)

**You can manually test detection:**

```powershell
cd backend
python modules\helmet_detection_unified.py
```

---

## For Your Capstone Demo

**Presentation Flow:**

1. **Show Dashboard** - "This is our admin interface"
2. **Show Database** - phpMyAdmin with violations + LTO data
3. **Explain Dual-Mode** - "Cloud for development, local for production"
4. **Live Demo** - When cameras arrive, plug and play!

---

## Next Steps

**Right Now:**
1. ✅ Set up Roboflow API key (5 min)
2. ✅ Import LTO database
3. ✅ Test system with Roboflow

**Before Defense:**
1. Get cameras (or use phone as webcam)
2. Record test videos showing detection
3. Practice presentation

**After Approval:**
1. Deploy to municipality
2. Switch to local mode
3. Production ready!

---

## Important Files

| File | Purpose |
|------|---------|
| `backend/config.py` | **Change detection mode here** |
| `ROBOFLOW_SETUP.md` | Detailed Roboflow instructions |
| `backend/app.py` | Main application (run this) |
| `database/lto_simulation.sql` | Mock LTO data |

---

## Troubleshooting

**"Roboflow API key not provided"**
→ Edit `config.py`, replace `your_roboflow_api_key_here`

**"pip install still running"**
→ Let it finish, or use Roboflow mode (doesn't need PyTorch)

**"No cameras detected"**
→ Normal if no hardware. Test with images instead.

**"MySQL connection error"**
→ Start MySQL in XAMPP Control Panel

---

## Quick Commands Reference

```powershell
# Start XAMPP MySQL
C:\xampp\xampp-control.exe

# Import LTO data
Get-Content database\lto_simulation.sql | C:\xampp\mysql\bin\mysql.exe -u root icapture_db

# Run system
cd backend
python app.py

# Open dashboard
start http://localhost:5000

# Test detector
python modules\helmet_detection_unified.py
```

---

**You're ready to go! Set up Roboflow and test the system! 🚀**

See `ROBOFLOW_SETUP.md` for detailed instructions.
