@echo off
echo ========================================
echo LTO Database Installer
echo ========================================
echo.

cd C:\xampp\mysql\bin

echo Dropping old tables...
mysql -u root icapture_db -e "DROP TABLE IF EXISTS lto_transactions; DROP TABLE IF EXISTS lto_vehicles; DROP VIEW IF EXISTS lto_owner_lookup; DROP VIEW IF EXISTS lto_recent_transactions; DROP VIEW IF EXISTS lto_unpaid_violations; DROP VIEW IF EXISTS lto_incomplete_registrations;"

echo.
echo Importing LTO database...
mysql -u root icapture_db < C:\Users\ASUS\IcaptureSystemV2\database\lto_simulation.sql

echo.
echo Verifying installation...
mysql -u root icapture_db -e "SELECT COUNT(*) as 'Total Vehicles' FROM lto_vehicles;"
mysql -u root icapture_db -e "SELECT COUNT(*) as 'Total Transactions' FROM lto_transactions;"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Press any key to view sample data...
pause > nul

mysql -u root icapture_db -e "SELECT plate_number, owner_name, validity_status FROM lto_owner_lookup LIMIT 5;"

echo.
echo Done! You can close this window.
pause
