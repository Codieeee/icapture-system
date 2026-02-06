-- Quick Import Script for LTO Database
-- Run this in phpMyAdmin SQL tab or MySQL command line

USE icapture_db;

-- Show current status
SELECT 'Checking for existing LTO tables...' as Status;
SHOW TABLES LIKE 'lto_%';

-- This will run the full LTO simulation setup
SOURCE C:/Users/ASUS/IcaptureSystemV2/database/lto_simulation.sql;

-- Verify installation
SELECT 'Installation Complete! Summary:' as Status;
SELECT COUNT(*) as 'Total Vehicles' FROM lto_vehicles;
SELECT COUNT(*) as 'Fully Registered' FROM lto_vehicles WHERE is_fully_registered = TRUE;
SELECT COUNT(*) as 'Incomplete Papers' FROM lto_vehicles WHERE is_fully_registered = FALSE;
SELECT COUNT(*) as 'With Unpaid Fines' FROM lto_vehicles WHERE total_unpaid_fines > 0;
SELECT COUNT(*) as 'Total Transactions' FROM lto_transactions;

-- Show sample LTO lookups
SELECT 'Sample LTO Records:' as Status;
SELECT plate_number, owner_name, validity_status, document_status, total_unpaid_fines 
FROM lto_owner_lookup 
LIMIT 5;
