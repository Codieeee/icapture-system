# 🚀 How to Run iCapture System - Quick Guide

## Pre-Requirements (One-Time Setup)
✅ XAMPP installed
✅ Python virtual environment created (`venv`)
✅ Dependencies installed (`pip install -r requirements.txt`)
✅ Database created and populated

---

## Step-by-Step: Run the System

### 1️⃣ Start MySQL Database
- Open **XAMPP Control Panel**
- Click **Start** next to **MySQL**
- Wait until it shows "Running" (green)

### 2️⃣ Open PowerShell
```powershell
# Navigate to backend folder
cd C:\Users\ASUS\IcaptureSystemV2\backend
```

### 3️⃣ Activate Virtual Environment
```powershell
# Activate venv
.\venv\Scripts\activate
```
You should see `(venv)` in your prompt.

### 4️⃣ Start Flask Server
```powershell
# Run the application
python app.py
```

**Wait for this message:**
```
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

⚠️ **IMPORTANT:** Keep this PowerShell window open! Don't close it or press Ctrl+C while using the system.

### 5️⃣ Open Browser
- Open Chrome, Edge, or Firefox
- Go to: **http://localhost:5000**
- You should see the iCapture dashboard!

---

## ✅ System is Running When You See:
- ✅ Dashboard loads with stats
- ✅ Violations table shows data
- ✅ Camera feeds visible (disconnected is OK)
- ✅ PowerShell shows no errors

---

## 🛑 How to Stop the System

### When You're Done:
1. Go to the PowerShell window
2. Press **Ctrl + C**
3. Wait for graceful shutdown
4. Close PowerShell

### In XAMPP:
- Click **Stop** next to MySQL (optional - can leave running)

---

## 🔧 Troubleshooting

### "Can't connect to localhost:5000"
- ✅ Make sure `python app.py` is still running
- ✅ Check PowerShell for errors
- ✅ Try hard refresh: Ctrl + Shift + R

### "Database connection error"
- ✅ Start MySQL in XAMPP
- ✅ Check phpMyAdmin: http://localhost/phpmyadmin
- ✅ Verify database `icapture_db` exists

### "Module not found" errors
- ✅ Make sure venv is activated (see `(venv)` in prompt)
- ✅ Run: `pip install -r requirements.txt`

### Camera warnings flooding console
- ✅ **Normal!** No cameras connected = expected warnings
- ✅ Ignore them - system still works
- ✅ Dashboard will show "Disconnected" status

---

## 📝 Quick Commands Summary

```powershell
# Full startup sequence
cd C:\Users\ASUS\IcaptureSystemV2\backend
.\venv\Scripts\activate
python app.py
# Then open: http://localhost:5000
```

---

## 🎯 Daily Usage Flow

1. **Morning:** Start XAMPP MySQL → Run `python app.py` → Open browser
2. **During Use:** Keep PowerShell running, use dashboard in browser
3. **Evening:** Ctrl+C to stop server → Close browser → Stop XAMPP (optional)

---

## 💡 Pro Tips

- **Bookmark** http://localhost:5000 for quick access
- **Keep PowerShell visible** so you can see system logs
- **Don't touch PowerShell** while system is running
- **Use Refresh button** in dashboard instead of restarting server
- **Check logs** in PowerShell if something doesn't work

---

## 🆘 Need Help?

If system doesn't start:
1. Check if port 5000 is already in use
2. Restart XAMPP MySQL
3. Delete `__pycache__` folders and try again
4. Check `backend/logs/` for error details

**System is ready when you see violations in the dashboard!** 🎉
