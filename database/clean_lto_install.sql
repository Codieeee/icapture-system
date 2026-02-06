-- LTO Database Clean Install Script
-- This will DROP old tables first, then create fresh ones
-- Safe to run multiple times

USE icapture_db;

-- ========================================
-- STEP 1: Clean up old tables and views
-- ========================================
SELECT 'Cleaning up old LTO tables...' as Status;

DROP TABLE IF EXISTS lto_transactions;
DROP TABLE IF EXISTS lto_vehicles;

DROP VIEW IF EXISTS lto_owner_lookup;
DROP VIEW IF EXISTS lto_recent_transactions;
DROP VIEW IF EXISTS lto_unpaid_violations;
DROP VIEW IF EXISTS lto_incomplete_registrations;

SELECT 'Old tables removed successfully!' as Status;

-- Now the lto_simulation.sql script will run cleanly!
-- After running this, import lto_simulation.sql again
