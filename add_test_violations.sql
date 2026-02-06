-- Add Test Violations for Dashboard Testing
-- Run this in phpMyAdmin to see violations in your dashboard

USE icapture_db;

-- Insert 5 test violations
INSERT INTO violations (
    violation_code,
    camera_id,
    plate_number,
    violation_type,
    violation_datetime,
    location,
    detection_confidence,
    ocr_confidence,
    status
) VALUES
('VIO-2024-001', 'CAM-WA-001', 'ABC1234', 'no_helmet', NOW(), 'National Road, Odiongan', 0.95, 0.88, 'pending'),
('VIO-2024-002', 'CAM-WA-001', 'XYZ5678', 'no_helmet', DATE_SUB(NOW(), INTERVAL 1 HOUR), 'National Road, Odiongan', 0.92, 0.85, 'verified'),
('VIO-2024-003', 'CAM-WA-001', 'DEF4321', 'nutshell_helmet', DATE_SUB(NOW(), INTERVAL 2 HOUR), 'National Road, Odiongan', 0.88, 0.79, 'pending'),
('VIO-2024-004', 'CAM-WA-001', 'GHI9876', 'no_helmet', DATE_SUB(NOW(), INTERVAL 3 HOUR), 'National Road, Odiongan', 0.94, 0.91, 'issued'),
('VIO-2024-005', 'CAM-WA-001', NULL, 'no_helmet', DATE_SUB(NOW(), INTERVAL 4 HOUR), 'National Road, Odiongan', 0.90, NULL, 'pending');

SELECT 'Test violations added successfully!' as status;
SELECT * FROM violations ORDER BY violation_datetime DESC;
