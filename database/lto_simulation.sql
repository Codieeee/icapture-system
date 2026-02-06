-- LTO Simulation Database (Enhanced Version)
-- Mock data for Land Transportation Office vehicle registration
-- WITH Transaction History and Document Completeness Tracking
-- For academic demonstration purposes only

USE icapture_db;

-- ========================================
-- 1. LTO Vehicle Registration Table (Enhanced)
-- ========================================
CREATE TABLE IF NOT EXISTS lto_vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type VARCHAR(50) NOT NULL,
    vehicle_make VARCHAR(100),
    vehicle_model VARCHAR(100),
    vehicle_color VARCHAR(50),
    vehicle_year INT,
    owner_name VARCHAR(255) NOT NULL,
    owner_address TEXT,
    owner_contact VARCHAR(50),
    
    -- Registration Status
    registration_status ENUM('active', 'expired', 'suspended', 'unregistered') DEFAULT 'active',
    registration_expiry DATE,
    
    -- NEW: Document Completeness Tracking
    has_or_cr BOOLEAN DEFAULT TRUE COMMENT 'Official Receipt & Certificate of Registration',
    has_drivers_license BOOLEAN DEFAULT TRUE COMMENT 'Valid driver license',
    has_insurance BOOLEAN DEFAULT FALSE COMMENT 'Valid insurance',
    has_emission_test BOOLEAN DEFAULT FALSE COMMENT 'Passed emission test',
    is_fully_registered BOOLEAN GENERATED ALWAYS AS (
        has_or_cr = TRUE AND has_drivers_license = TRUE
    ) STORED COMMENT 'Fully registered with complete basic documents',
    
    -- NEW: Violation History Stats
    total_violations INT DEFAULT 0,
    total_unpaid_fines DECIMAL(10,2) DEFAULT 0.00,
    last_violation_date DATE DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_plate (plate_number),
    INDEX idx_status (registration_status),
    INDEX idx_fully_registered (is_fully_registered)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- 2. NEW: LTO Transaction History Table
-- ========================================
CREATE TABLE IF NOT EXISTS lto_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL,
    transaction_type ENUM(
        'registration', 
        'renewal', 
        'violation_issued',
        'violation_paid',
        'suspension',
        'document_update'
    ) NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    amount DECIMAL(10,2) DEFAULT 0.00,
    payment_status ENUM('paid', 'unpaid', 'waived', 'n/a') DEFAULT 'n/a',
    processed_by VARCHAR(100) DEFAULT 'LTO System',
    
    INDEX idx_plate_trans (plate_number),
    INDEX idx_type (transaction_type),
    INDEX idx_date (transaction_date),
    FOREIGN KEY (plate_number) REFERENCES lto_vehicles(plate_number) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========================================
-- 3. Insert Sample Vehicle Data (Enhanced)
-- ========================================

-- Fully Registered Vehicles (Complete Papers)
INSERT INTO lto_vehicles (
    plate_number, vehicle_type, vehicle_make, vehicle_model, vehicle_color, vehicle_year,
    owner_name, owner_address, owner_contact,
    registration_status, registration_expiry,
    has_or_cr, has_drivers_license, has_insurance, has_emission_test
) VALUES
('ABC-1234', 'Motorcycle', 'Honda', 'TMX 155', 'Red', 2022, 
 'Juan Dela Cruz', 'Brgy. San Roque, Odiongan, Romblon', '09171234567',
 'active', '2026-12-31', TRUE, TRUE, TRUE, TRUE),
 
('XYZ-5678', 'Motorcycle', 'Yamaha', 'Mio i125', 'Blue', 2021,
 'Maria Santos', 'Brgy. Poblacion, Odiongan, Romblon', '09281234567',
 'active', '2026-06-30', TRUE, TRUE, TRUE, TRUE),
 
('DEF-9012', 'Motorcycle', 'Suzuki', 'Smash 115', 'Black', 2020,
 'Pedro Garcia', 'Brgy. Canduyong, Odiongan, Romblon', '09391234567',
 'active', '2026-08-15', TRUE, TRUE, FALSE, TRUE),

-- Missing Some Documents
('GHI-3456', 'Motorcycle', 'Honda', 'Wave 110', 'White', 2023,
 'Ana Reyes', 'Brgy. Lumbang, Odiongan, Romblon', '09451234567',
 'active', '2027-01-20', TRUE, TRUE, FALSE, FALSE),
 
('JKL-7890', 'Motorcycle', 'Kawasaki', 'Barako 175', 'Green', 2019,
 'Carlos Mendoza', 'Brgy. Tabu-an, Odiongan, Romblon', '09561234567',
 'active', '2026-11-10', TRUE, TRUE, TRUE, FALSE),

-- No Driver's License (Incomplete Papers!)
('MNO-2345', 'Motorcycle', 'Yamaha', 'Sniper 150', 'Orange', 2018,
 'Rosa Valencia', 'Brgy. Gabawan, Odiongan, Romblon', '09671234567',
 'expired', '2025-03-15', TRUE, FALSE, FALSE, FALSE),

-- No OR/CR (No Proper Registration!)
('PQR-6789', 'Motorcycle', 'Honda', 'XRM 125', 'Silver', 2017,
 'Miguel Torres', 'Brgy. Tulay, Odiongan, Romblon', '09781234567',
 'expired', '2024-12-01', FALSE, TRUE, FALSE, FALSE),

-- Suspended (Has papers but suspended)
('STU-0123', 'Motorcycle', 'Suzuki', 'Raider J125', 'Black', 2019,
 'Elena Fernandez', 'Brgy. Panique, Odiongan, Romblon', '09891234567',
 'suspended', '2025-09-30', TRUE, TRUE, FALSE, FALSE),

-- More Fully Registered
('VWX-4567', 'Motorcycle', 'Honda', 'Click 160', 'Red', 2022,
 'Roberto Cruz', 'Brgy. Matutungtung, Odiongan, Romblon', '09101234567',
 'active', '2026-10-25', TRUE, TRUE, TRUE, TRUE),
 
('YZA-8901', 'Motorcycle', 'Yamaha', 'Aerox 155', 'Blue', 2023,
 'Lisa Martinez', 'Brgy. Libertad, Odiongan, Romblon', '09111234567',
 'active', '2027-02-14', TRUE, TRUE, FALSE, TRUE),

-- Missing License
('BCD-2346', 'Motorcycle', 'Suzuki', 'Skydrive 125', 'White', 2021,
 'Daniel Ramos', 'Brgy. Pawa, Odiongan, Romblon', '09121234567',
 'active', '2026-07-18', TRUE, FALSE, FALSE, FALSE),

-- Fully Registered
('EFG-6780', 'Motorcycle', 'Honda', 'Beat 110', 'Pink', 2020,
 'Sofia Aquino', 'Brgy. Anahaw, Odiongan, Romblon', '09131234567',
 'active', '2026-05-22', TRUE, TRUE, TRUE, FALSE),
 
('HIJ-0124', 'Motorcycle', 'Kawasaki', 'Rouser 135', 'Black', 2022,
 'Fernando Lopez', 'Brgy. Liwanag, Odiongan, Romblon', '09141234567',
 'active', '2026-09-08', TRUE, TRUE, FALSE, TRUE),

-- No OR/CR (Unregistered!)
('KLM-4568', 'Motorcycle', 'Yamaha', 'Sight 115', 'Red', 2021,
 'Carmen Diaz', 'Brgy. Poctoy, Odiongan, Romblon', '09151234567',
 'unregistered', NULL, FALSE, FALSE, FALSE, FALSE),

-- Fully Registered
('NOP-8902', 'Motorcycle', 'Honda', 'TMX 125', 'Blue', 2019,
 'Ricardo Santos', 'Brgy. Tuburan, Odiongan, Romblon', '09161234567',
 'active', '2026-12-12', TRUE, TRUE, TRUE, TRUE);

-- ========================================
-- 4. Insert Sample Transaction History
-- ========================================

-- Registration transactions
INSERT INTO lto_transactions (plate_number, transaction_type, transaction_date, description, amount, payment_status) VALUES
('ABC-1234', 'registration', '2022-01-15 09:30:00', 'Initial motorcycle registration', 5500.00, 'paid'),
('ABC-1234', 'renewal', '2025-12-20 10:15:00', 'Annual registration renewal', 1200.00, 'paid'),

('XYZ-5678', 'registration', '2021-03-10 14:20:00', 'Initial motorcycle registration', 5200.00, 'paid'),
('XYZ-5678', 'renewal', '2025-05-25 11:00:00', 'Annual registration renewal', 1200.00, 'paid'),

('MNO-2345', 'violation_issued', '2024-08-15 08:45:00', 'No helmet violation - RSU Gate 3', 1500.00, 'unpaid'),
('MNO-2345', 'violation_issued', '2024-11-03 16:30:00', 'Expired registration', 2000.00, 'unpaid'),

('PQR-6789', 'violation_issued', '2024-06-20 13:15:00', 'Operating without OR/CR', 3000.00, 'unpaid'),

('STU-0123', 'violation_issued', '2025-01-10 09:00:00', 'Reckless driving', 2500.00, 'paid'),
('STU-0123', 'violation_paid', '2025-01-15 10:30:00', 'Paid reckless driving fine', 2500.00, 'paid'),
('STU-0123', 'suspension', '2025-02-01 08:00:00', 'License suspended - 3 months', 0.00, 'n/a'),

('VWX-4567', 'registration', '2022-07-22 15:45:00', 'Initial motorcycle registration', 5800.00, 'paid'),
('VWX-4567', 'renewal', '2025-07-18 09:20:00', 'Annual registration renewal', 1200.00, 'paid'),

('KLM-4568', 'violation_issued', '2024-09-12 17:00:00', 'Operating unregistered vehicle', 5000.00, 'unpaid');

-- Update violation stats in vehicles table
UPDATE lto_vehicles SET total_violations = 2, total_unpaid_fines = 3500.00, last_violation_date = '2024-11-03' WHERE plate_number = 'MNO-2345';
UPDATE lto_vehicles SET total_violations = 1, total_unpaid_fines = 3000.00, last_violation_date = '2024-06-20' WHERE plate_number = 'PQR-6789';
UPDATE lto_vehicles SET total_violations = 1, total_unpaid_fines = 0.00, last_violation_date = '2025-01-10' WHERE plate_number = 'STU-0123';
UPDATE lto_vehicles SET total_violations = 1, total_unpaid_fines = 5000.00, last_violation_date = '2024-09-12' WHERE plate_number = 'KLM-4568';

-- ========================================
-- 5. Create Enhanced Views
-- ========================================

-- View: Complete Owner Lookup with Document Status
CREATE OR REPLACE VIEW lto_owner_lookup AS
SELECT 
    v.plate_number,
    v.owner_name,
    v.owner_address,
    v.owner_contact,
    v.vehicle_make,
    v.vehicle_model,
    v.vehicle_color,
    v.registration_status,
    v.registration_expiry,
    v.is_fully_registered,
    v.has_or_cr,
    v.has_drivers_license,
    v.has_insurance,
    v.has_emission_test,
    v.total_violations,
    v.total_unpaid_fines,
    v.last_violation_date,
    CASE 
        WHEN v.registration_status = 'unregistered' THEN 'Unregistered'
        WHEN v.registration_status = 'suspended' THEN 'Suspended'
        WHEN v.registration_status = 'active' AND v.registration_expiry > CURDATE() AND v.is_fully_registered = TRUE THEN 'Fully Registered'
        WHEN v.registration_status = 'active' AND v.registration_expiry > CURDATE() AND v.is_fully_registered = FALSE THEN 'Missing Documents'
        WHEN v.registration_status = 'active' AND v.registration_expiry <= CURDATE() THEN 'Expired'
        WHEN v.registration_status = 'expired' THEN 'Expired'
        ELSE 'Invalid'
    END as validity_status,
    CASE
        WHEN v.has_or_cr = FALSE THEN 'No OR/CR'
        WHEN v.has_drivers_license = FALSE THEN 'No License'
        WHEN v.has_or_cr = TRUE AND v.has_drivers_license = TRUE THEN 'Complete'
        ELSE 'Unknown'
    END as document_status
FROM lto_vehicles v;

-- View: Recent Transactions
CREATE OR REPLACE VIEW lto_recent_transactions AS
SELECT 
    t.id,
    t.plate_number,
    v.owner_name,
    t.transaction_type,
    t.transaction_date,
    t.description,
    t.amount,
    t.payment_status
FROM lto_transactions t
JOIN lto_vehicles v ON t.plate_number = v.plate_number
ORDER BY t.transaction_date DESC
LIMIT 100;

-- View: Vehicles with Unpaid Violations
CREATE OR REPLACE VIEW lto_unpaid_violations AS
SELECT 
    v.plate_number,
    v.owner_name,
    v.owner_contact,
    v.total_violations,
    v.total_unpaid_fines,
    v.last_violation_date,
    v.registration_status
FROM lto_vehicles v
WHERE v.total_unpaid_fines > 0
ORDER BY v.total_unpaid_fines DESC;

-- View: Incomplete Registrations
CREATE OR REPLACE VIEW lto_incomplete_registrations AS
SELECT 
    plate_number,
    owner_name,
    owner_contact,
    registration_status,
    CASE 
        WHEN has_or_cr = FALSE THEN 'Missing OR/CR'
        WHEN has_drivers_license = FALSE THEN 'No Driver License'
        ELSE 'Incomplete'
    END as missing_document
FROM lto_vehicles
WHERE is_fully_registered = FALSE OR registration_status = 'unregistered';

-- ========================================
-- 6. Add LTO lookup columns to violations table
-- ========================================
ALTER TABLE violations 
ADD COLUMN IF NOT EXISTS lto_owner_name VARCHAR(255) DEFAULT NULL AFTER plate_number,
ADD COLUMN IF NOT EXISTS lto_lookup_status ENUM('found', 'not_found', 'not_checked') DEFAULT 'not_checked' AFTER lto_owner_name,
ADD COLUMN IF NOT EXISTS lto_document_status VARCHAR(50) DEFAULT NULL AFTER lto_lookup_status,
ADD COLUMN IF NOT EXISTS lto_has_unpaid_fines BOOLEAN DEFAULT FALSE AFTER lto_document_status;

-- ========================================
-- 7. Summary Reports
-- ========================================
SELECT 'LTO Enhanced Database Created Successfully!' as Status;
SELECT COUNT(*) as 'Total Vehicles' FROM lto_vehicles;
SELECT COUNT(*) as 'Fully Registered' FROM lto_vehicles WHERE is_fully_registered = TRUE;
SELECT COUNT(*) as 'Incomplete Papers' FROM lto_vehicles WHERE is_fully_registered = FALSE;
SELECT COUNT(*) as 'Unregistered' FROM lto_vehicles WHERE registration_status = 'unregistered';
SELECT COUNT(*) as 'With Unpaid Fines' FROM lto_vehicles WHERE total_unpaid_fines > 0;
SELECT COUNT(*) as 'Total Transactions' FROM lto_transactions;
