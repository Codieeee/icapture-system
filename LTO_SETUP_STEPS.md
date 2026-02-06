# LTO Database Quick Setup Guide

## ✅ Step-by-Step: Gawin Mo Ito

### Step 1: Start XAMPP
1. Open **XAMPP Control Panel**
2. Click **Start** sa MySQL
3. Wait for green indicator

### Step 2: Import LTO Database

#### Option A: phpMyAdmin (Recommended - Easiest!)
1. Open browser: **http://localhost/phpmyadmin**
2. Click **`icapture_db`** sa left panel
3. Click **"Import"** tab sa top
4. Click **"Choose File"** button
5. Navigate to: `C:\Users\ASUS\IcaptureSystemV2\database\lto_simulation.sql`
6. Click **"Go"** button at bottom
7. Wait for success message: "Import has been successfully finished"

**✅ DONE! Tables created:**
- `lto_vehicles` (15 vehicles)
- `lto_transactions` (14 transactions)
- 4 views (lto_owner_lookup, etc.)

#### Option B: MySQL Command Line
```powershell
# Open PowerShell
mysql -u root -p icapture_db < C:\Users\ASUS\IcaptureSystemV2\database\lto_simulation.sql
# Press Enter (no password)
```

### Step 3: Verify Installation

Sa phpMyAdmin:
1. Click **`icapture_db`**
2. Click **`lto_vehicles`** table
3. Click **"Browse"** tab
4. **You should see 15 vehicles!** ✅

Quick test query:
```sql
SELECT * FROM lto_owner_lookup WHERE plate_number = 'ABC-1234';
```

Expected result:
```
Owner: Juan Dela Cruz
Status: Fully Registered
```

### Step 4: Start iCapture Server

```powershell
cd C:\Users\ASUS\IcaptureSystemV2\backend
.\venv\Scripts\activate
python app.py
```

Look for this in console:
```
 * Running on http://127.0.0.1:5000
INFO:lto_routes:LTO routes registered successfully
```

### Step 5: Test LTO Integration!

1. **Open browser**: http://localhost:5000
2. **Click "Violations"** sa sidebar
3. **Click "View Details"** on any violation
4. **MAKIKITA MO NA ANG:**

```
📋 LTO Registration Info
━━━━━━━━━━━━━━━━━━━━━
Owner: Juan Dela Cruz
Status: Fully Registered ✅
```

**OR kung walang complete papers:**
```
📋 LTO Registration Info
━━━━━━━━━━━━━━━━━━━━━
Owner: Carmen Diaz
Status: Unregistered ⚠️
Missing: No OR/CR ❌
Unpaid Fines: ₱5,000 🚨
```

### Step 6: Test API Directly (Optional)

Open browser:
```
http://localhost:5000/api/lto/lookup/ABC-1234
http://localhost:5000/api/lto/stats
http://localhost:5000/api/lto/unpaid-violations
```

You should see JSON responses! ✅

---

## 🎯 Summary Checklist

- [ ] XAMPP MySQL started
- [ ] Imported `lto_simulation.sql` via phpMyAdmin
- [ ] Verified 15 vehicles in `lto_vehicles` table
- [ ] Started iCapture server (`python app.py`)
- [ ] Opened dashboard (http://localhost:5000)
- [ ] Clicked Violations → View Details
- [ ] **SAW LTO INFO IN MODAL!** 🎉

---

## 🆘 Troubleshooting

**Error: "Table already exists"**
- Solution: Drop existing tables first, then import

**No LTO info showing in modal**
- Check browser console (F12) for errors
- Verify API endpoint: http://localhost:5000/api/lto/stats
- Hard refresh browser: Ctrl + Shift + R

**Import hangs**
- Close other database connections
- Refresh phpMyAdmin
- Try command line method

---

**Yan lang! Simple steps lang!** 🚀
