-- Add Rider Personal Information to Violations Table
-- Run this migration to add rider tracking fields

USE icapture_db;

-- Add rider personal information columns
ALTER TABLE violations
ADD COLUMN rider_name VARCHAR(255) DEFAULT NULL COMMENT 'Full name of rider' AFTER notes,
ADD COLUMN rider_address TEXT DEFAULT NULL COMMENT 'Complete address' AFTER rider_name,
ADD COLUMN rider_contact VARCHAR(50) DEFAULT NULL COMMENT 'Phone number' AFTER rider_address,
ADD COLUMN rider_age INT DEFAULT NULL COMMENT 'Age' AFTER rider_contact,
ADD COLUMN rider_license_number VARCHAR(50) DEFAULT NULL COMMENT 'Driver license number' AFTER rider_age,
ADD COLUMN rider_id_type VARCHAR(50) DEFAULT NULL COMMENT 'ID type (e.g., Drivers License, National ID)' AFTER rider_license_number,
ADD COLUMN rider_id_number VARCHAR(100) DEFAULT NULL COMMENT 'ID number' AFTER rider_id_type,
ADD COLUMN apprehended_by VARCHAR(255) DEFAULT NULL COMMENT 'Officer who apprehended' AFTER rider_id_number,
ADD COLUMN apprehension_datetime DATETIME DEFAULT NULL COMMENT 'Date/time when rider was stopped' AFTER apprehended_by,
ADD COLUMN notes_personal TEXT DEFAULT NULL COMMENT 'Additional notes about rider' AFTER apprehension_datetime;

-- Add index for searching by rider name
ALTER TABLE violations
ADD INDEX idx_rider_name (rider_name),
ADD INDEX idx_rider_license (rider_license_number);

-- Verify columns were added
SHOW COLUMNS FROM violations LIKE 'rider%';
SHOW COLUMNS FROM violations LIKE 'appre%';

SELECT 'Rider information columns added successfully!' as Status;
