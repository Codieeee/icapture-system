-- iCapture System Database Schema
-- No-Contact Helmet Violation Detection System
-- Municipality of Odiongan

CREATE DATABASE IF NOT EXISTS icapture_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE icapture_db;

-- ============================================
-- Main violations table
-- ============================================
CREATE TABLE violations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    violation_code VARCHAR(20) UNIQUE NOT NULL COMMENT 'Format: VL-YYYYMMDD-####',
    plate_number VARCHAR(20) DEFAULT NULL COMMENT 'License plate (null if not detected)',
    violation_type ENUM('no_helmet', 'nutshell_helmet') NOT NULL,
    
    -- Image paths
    rider_image_path VARCHAR(255) DEFAULT NULL COMMENT 'Path to rider face image',
    plate_image_path VARCHAR(255) DEFAULT NULL COMMENT 'Path to plate image',
    
    -- Camera information
    camera_location VARCHAR(100) NOT NULL COMMENT 'Camera deployment location',
    camera_id VARCHAR(50) NOT NULL COMMENT 'Camera identifier',
    
    -- Detection metrics
    detection_confidence DECIMAL(5,4) DEFAULT NULL COMMENT 'YOLO confidence (0-1)',
    ocr_confidence DECIMAL(5,4) DEFAULT NULL COMMENT 'OCR confidence (0-1)',
    
    -- Timestamp and status
    violation_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'verified', 'dismissed', 'issued') DEFAULT 'pending',
    
    -- Additional information
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_plate_number (plate_number),
    INDEX idx_violation_datetime (violation_datetime),
    INDEX idx_status (status),
    INDEX idx_camera_location (camera_location),
    INDEX idx_violation_code (violation_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Camera configuration table
-- ============================================
CREATE TABLE cameras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    camera_type ENUM('wide_angle', 'plate') NOT NULL,
    location VARCHAR(100) NOT NULL,
    
    -- Stream configuration
    stream_url VARCHAR(255) NOT NULL COMMENT 'RTSP/USB path or device index',
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    
    -- Monitoring metrics
    last_frame_time DATETIME DEFAULT NULL,
    total_violations INT DEFAULT 0,
    
    -- Installation info
    installed_date DATE NOT NULL,
    notes TEXT DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_status (status),
    INDEX idx_location (location)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- System logs table
-- ============================================
CREATE TABLE system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    log_level ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    module VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSON DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_log_level (log_level),
    INDEX idx_created_at (created_at),
    INDEX idx_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Admin users table (for dashboard access)
-- ============================================
CREATE TABLE admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'operator', 'viewer') DEFAULT 'operator',
    
    last_login DATETIME DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Insert default data
-- ============================================

-- Default admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO admin_users (username, password_hash, full_name, role)
VALUES ('admin', SHA2('admin123', 256), 'System Administrator', 'admin');

-- Sample camera configurations (adjust stream_url for your setup)
INSERT INTO cameras (camera_id, camera_type, location, stream_url, installed_date)
VALUES 
    ('CAM-WA-001', 'wide_angle', 'National Road, Odiongan', '0', CURDATE()),
    ('CAM-PL-001', 'plate', 'National Road, Odiongan', '1', CURDATE());

-- ============================================
-- Useful queries for monitoring
-- ============================================

-- View recent violations
-- SELECT * FROM violations ORDER BY violation_datetime DESC LIMIT 20;

-- Daily violation statistics
-- SELECT DATE(violation_datetime) as date, 
--        COUNT(*) as total,
--        SUM(CASE WHEN violation_type = 'no_helmet' THEN 1 ELSE 0 END) as no_helmet,
--        SUM(CASE WHEN violation_type = 'nutshell_helmet' THEN 1 ELSE 0 END) as nutshell
-- FROM violations
-- GROUP BY DATE(violation_datetime)
-- ORDER BY date DESC;

-- Camera performance
-- SELECT camera_id, location, total_violations, last_frame_time, status
-- FROM cameras
-- ORDER BY total_violations DESC;
