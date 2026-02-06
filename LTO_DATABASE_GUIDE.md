# 📋 LTO Simulated Database - Gabay (Guide)

## 📍 Nasaan ang LTO Database?

**File Location:**
```
C:\Users\ASUS\IcaptureSystemV2\database\lto_simulation.sql
```

---

## 🗄️ Ano ang Laman?

Ang LTO database ay may **15 mock vehicles** (sample data) na may:

### Table: `lto_vehicles`
- **Plate Number** - Philippine format (ABC-1234)
- **Owner Name** - Pangalan ng may-ari
- **Owner Address** - Address sa Odiongan, Romblon
- **Owner Contact** - Mobile number
- **Vehicle Info** - Make, Model, Color, Year
- **Registration Status** - Active, Expired, o Suspended
- **Expiry Date** - Kailan mag-expire

---

## 📊 Paano Tignan ang Data?

### Option 1: Sa phpMyAdmin (Recommended)

1. **Buksan ang XAMPP**
2. **I-start ang MySQL**
3. **Buksan ang browser**: http://localhost/phpmyadmin
4. **Click** `icapture_db` database sa left panel
5. **Click** `lto_vehicles` table
6. **Click** "Browse" tab

**➡️ Makikita mo ang 15 sample vehicles!**

---

### Option 2: MySQL Command Line

```sql
-- Login sa MySQL
mysql -u root -p

-- Select database
USE icapture_db;

-- Tingnan lahat ng vehicles
SELECT * FROM lto_vehicles;

-- Tingnan specific plate
SELECT * FROM lto_vehicles WHERE plate_number = 'ABC-1234';

-- Tingnan owner info
SELECT plate_number, owner_name, owner_contact 
FROM lto_vehicles;
```

---

### Option 3: Quick View (Ready-made view)

```sql
-- Use the pre-built view
SELECT * FROM lto_owner_lookup;

-- Search by plate
SELECT * FROM lto_owner_lookup 
WHERE plate_number = 'ABC-1234';
```

---

## 🔍 Sample Plates Available

### ✅ Active Registrations (11 vehicles)
- `ABC-1234` - Juan Dela Cruz (Honda TMX 155)
- `XYZ-5678` - Maria Santos (Yamaha Mio i125)
- `DEF-9012` - Pedro Garcia (Suzuki Smash 115)
- `GHI-3456` - Ana Reyes (Honda Wave 110)
- `JKL-7890` - Carlos Mendoza (Kawasaki Barako 175)
- `VWX-4567` - Roberto Cruz (Honda Click 160)
- `YZA-8901` - Lisa Martinez (Yamaha Aerox 155)
- `BCD-2346` - Daniel Ramos (Suzuki Skydrive 125)
- `EFG-6780` - Sofia Aquino (Honda Beat 110)
- `HIJ-0124` - Fernando Lopez (Kawasaki Rouser 135)
- `KLM-4568` - Carmen Diaz (Yamaha Sight 115)
- `NOP-8902` - Ricardo Santos (Honda TMX 125)

### ⚠️ Expired Registrations (2 vehicles)
- `MNO-2345` - Rosa Valencia (Yamaha Sniper 150)
- `PQR-6789` - Miguel Torres (Honda XRM 125)

### 🚫 Suspended Registration (1 vehicle)
- `STU-0123` - Elena Fernandez (Suzuki Raider J125)

---

## 🔗 Paano Gamitin sa System?

Ang violations table ay may connection sa LTO database:

```sql
-- Makikita ang LTO info sa violation
SELECT 
    v.violation_code,
    v.plate_number,
    v.lto_owner_name,
    v.lto_lookup_status
FROM violations v;
```

**Kapag may bagong violation:**
1. System detects plate number (e.g., "ABC-1234")
2. System checks `lto_vehicles` table
3. Kung may match, i-save ang owner name
4. Status: `found`, `not_found`, o `not_checked`

---

## ➕ Paano Mag-add ng Bagong Vehicle?

```sql
INSERT INTO lto_vehicles 
(plate_number, vehicle_type, vehicle_make, vehicle_model, 
 vehicle_color, vehicle_year, owner_name, owner_address, 
 owner_contact, registration_status, registration_expiry)
VALUES
('NEW-1234', 'Motorcycle', 'Honda', 'TMX 155', 'Red', 2024,
 'Your Name', 'Your Address', '09171234567', 
 'active', '2027-12-31');
```

---

## 📝 Notes

- **Mock data lang ito** - For testing/academic purposes only
- **15 vehicles total** - Pwede mag-add ng more
- **All addresses** - Odiongan, Romblon area
- **Philippine plate format** - ABC-1234 style

---

## ✅ Quick Test

Subukan mo:
```sql
SELECT * FROM lto_owner_lookup WHERE plate_number = 'ABC-1234';
```

Result dapat:
```
Plate: ABC-1234
Owner: Juan Dela Cruz
Vehicle: Honda TMX 155 (Red, 2022)
Status: Valid
```

---

**Yan ang LTO simulated database mo!** 🎉
