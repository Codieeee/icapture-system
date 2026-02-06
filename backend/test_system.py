# System Test Script for iCapture
# Tests all components before full startup

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

print("="*60)
print("iCapture System Component Test")
print("="*60)
print()

# Test 1: Database Connection
print("[1/6] Testing Database Connection...")
try:
    from modules.database import get_database
    db = get_database()
    if db.connect():
        print("  ✓ Database connection successful")
        
        # Check tables
        result = db.execute_query("SHOW TABLES")
        print(f"  ✓ Found {len(result)} tables")
        db.disconnect()
    else:
        print("  ✗ Database connection failed")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()

# Test 2: LTO Database
print("[2/6] Testing LTO Database...")
try:
    from modules.lto_lookup import get_lto_lookup
    lto = get_lto_lookup()
    stats = lto.get_statistics()
    print(f"  ✓ Total vehicles: {stats.get('total_vehicles', 0)}")
    print(f"  ✓ Active: {stats.get('active_count', 0)}")
    
    # Test lookup
    vehicle = lto.lookup_by_plate("ABC-1234")
    if vehicle:
        print(f"  ✓ Lookup test: {vehicle['owner_name']}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()

# Test3: Helmet Detection
print("[3/6] Testing Helmet Detection...")
try:
    from config import HELMET_DETECTION_CONFIG
    mode = HELMET_DETECTION_CONFIG.get('mode', 'local')
    print(f"  ℹ Detection mode: {mode}")
    
    if mode == 'roboflow':
        api_key = HELMET_DETECTION_CONFIG['roboflow']['api_key']
        if api_key == 'your_roboflow_api_key_here':
            print("  ⚠ Roboflow API key not configured")
            print("    Update backend/config.py line 70")
        else:
            print(f"  ✓ Roboflow API key configured")
            from modules.helmet_detection_unified import get_detector
            detector = get_detector()
            print("  ✓ Detector initialized")
    else:
        # Local mode
        import torch
        print(f"  ℹ Device: {'GPU (CUDA)' if torch.cuda.is_available() else 'CPU'}")
        from modules.helmet_detection_unified import get_detector
        detector = get_detector()
        print("  ✓ Local detector initialized")
        
except Exception as e:
    print(f"  ✗ Error: {e}")

print()

# Test 4: Tesseract OCR
print("[4/6] Testing Tesseract OCR...")
try:
    import pytesseract
    from config import OCR_CONFIG
    
    if 'tesseract_cmd' in OCR_CONFIG:
        pytesseract.pytesseract.tesseract_cmd = OCR_CONFIG['tesseract_cmd']
    
    version = pytesseract.get_tesseract_version()
    print(f"  ✓ Tesseract version: {version}")
except Exception as e:
    print(f"  ⚠ Tesseract not configured: {e}")
    print("    Install from: https://github.com/UB-Mannheim/tesseract/wiki")

print()

# Test 5: Camera Configuration
print("[5/6] Testing Camera Configuration...")
try:
    from config import CAMERA_CONFIG
    print(f"  ℹ Wide-angle: {CAMERA_CONFIG['wide_angle']['stream_url']}")
    print(f"  ℹ Plate camera: {CAMERA_CONFIG['plate']['stream_url']}")
    print("  ⚠ Cameras not tested (no hardware)")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()

# Test 6: Flask Configuration
print("[6/6] Testing Flask Configuration...")
try:
    from config import FLASK_CONFIG
    print(f"  ✓ Server: {FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
    print(f"  ℹ Debug mode: {FLASK_CONFIG['debug']}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print()
print("="*60)
print("System Test Complete!")
print("="*60)
print()
print("Next Steps:")
print("1. If using Roboflow: Set API key in backend/config.py")
print("2. Run the system: python app.py")
print("3. Open dashboard: http://localhost:5000")
print()
