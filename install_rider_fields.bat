@echo off
echo ========================================
echo Adding Rider Information Fields
echo ========================================
echo.

cd C:\xampp\mysql\bin

echo Running database migration...
mysql -u root icapture_db < C:\Users\ASUS\IcaptureSystemV2\database\add_rider_info.sql

echo.
echo Verifying columns...
mysql -u root icapture_db -e "SHOW COLUMNS FROM violations LIKE 'rider%%';"
mysql -u root icapture_db -e "SHOW COLUMNS FROM violations LIKE 'appre%%';"

echo.
echo ========================================
echo Migration Complete!
echo ========================================
pause
