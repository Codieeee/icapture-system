-- Debug script to check LTO database and API connectivity
-- Run this in PowerShell: .\mysql.exe -u root icapture_db < debug_lto.sql

USE icapture_db;

-- Check if GHI9876 exists
SELECT 'Checking for GHI9876...' as Status;
SELECT * FROM lto_vehicles WHERE plate_number = 'GHI9876';

-- Check all plates in LTO database
SELECT 'All plates in LTO database:' as Status;
SELECT plate_number, owner_name, is_fully_registered FROM lto_vehicles;

-- Check lto_owner_lookup view
SELECT 'Testing lto_owner_lookup view:' as Status;
SELECT * FROM lto_owner_lookup WHERE plate_number = 'GHI9876';

-- Check violation table for this plate
SELECT 'Checking violations table:' as Status;
SELECT id, plate_number, violation_datetime FROM violations WHERE plate_number LIKE '%GHI%';
