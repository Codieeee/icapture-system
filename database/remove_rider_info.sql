-- Remove Rider Personal Information from Violations Table
-- This rollback script removes all rider tracking fields

USE icapture_db;

-- Drop rider information columns
ALTER TABLE violations
DROP COLUMN IF EXISTS rider_name,
DROP COLUMN IF EXISTS rider_address,
DROP COLUMN IF EXISTS rider_contact,
DROP COLUMN IF EXISTS rider_age,
DROP COLUMN IF EXISTS rider_license_number,
DROP COLUMN IF EXISTS rider_id_type,
DROP COLUMN IF EXISTS rider_id_number,
DROP COLUMN IF EXISTS apprehended_by,
DROP COLUMN IF EXISTS apprehension_datetime,
DROP COLUMN IF EXISTS notes_personal;

-- Drop indexes
ALTER TABLE violations
DROP INDEX IF EXISTS idx_rider_name,
DROP INDEX IF EXISTS idx_rider_license;

-- Verify columns were removed
SELECT 'Rider information columns removed successfully!' as Status;
SHOW COLUMNS FROM violations;
