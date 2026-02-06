"""
iCapture System - Flask Application Entry Point
Main backend server integrating all modules
"""

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import threading
import time
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import FLASK_CONFIG, CORS_CONFIG
from utils.logger import get_logger
from modules.database import get_database
from modules.video_capture import VideoCaptureManager
from modules.helmet_detection_unified import get_detector  # Unified detector (Roboflow or Local)
from modules.face_capture import get_face_capture
from modules.plate_recognition import get_recognizer
from modules.violation_logic import get_violation_manager

# Import route blueprints
from routes.violations import violations_bp
from routes.dashboard import dashboard_bp
from routes.cameras import cameras_bp, set_video_manager
from routes.lto import lto_bp

logger = get_logger('app')

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = FLASK_CONFIG['secret_key']

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_CONFIG['origins'],
        "methods": CORS_CONFIG['methods'],
        "allow_headers": CORS_CONFIG['allow_headers']
    }
})

# Register blueprints
app.register_blueprint(violations_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(cameras_bp)
app.register_blueprint(lto_bp)


# Global instances
video_manager = None
helmet_detector = None
face_capture = None
plate_recognizer = None
violation_manager = None
processing_thread = None
processing_active = False

def initialize_system():
    """Initialize all system components"""
    global video_manager, helmet_detector, face_capture, plate_recognizer, violation_manager
    
    logger.info("Initializing iCapture System...")
    
    try:
        # Initialize database
        db = get_database()
        if not db.connection or not db.connection.open:
            db.connect()
        logger.info("✓ Database connected")
        
        # Initialize video capture
        video_manager = VideoCaptureManager()
        set_video_manager(video_manager)  # Set for camera routes
        if video_manager.start_cameras():
            logger.info("✓ Cameras started")
        else:
            logger.warning("⚠ Some cameras failed to start")
        
        # Initialize AI modules
        helmet_detector = get_detector()
        logger.info("✓ Helmet detector loaded")
        
        face_capture = get_face_capture()
        logger.info("✓ Face capture initialized")
        
        plate_recognizer = get_recognizer()
        logger.info("✓ Plate recognizer initialized")
        
        # Initialize violation logic
        violation_manager = get_violation_manager(db)
        logger.info("✓ Violation manager initialized")
        
        logger.info("System initialization complete!")
        return True
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        return False

def process_violations():
    """Main violation processing loop (runs in background thread)"""
    global processing_active
    
    logger.info("Starting violation processing thread...")
    
    frame_count = 0
    processing_fps = 2  # Process 2 frames per second
    frame_delay = 1.0 / processing_fps
    
    while processing_active:
        try:
            # Get frames from both cameras
            wide_frame = video_manager.get_frame('wide_angle')
            plate_frame = video_manager.get_frame('plate')
            
            if wide_frame is None:
                time.sleep(frame_delay)
                continue
            
            # Run helmet detection
            detection_result = helmet_detector.process_frame(wide_frame)
            
            if detection_result['has_violation']:
                best_violation = detection_result['best_violation']
                logger.info(f"Violation detected: {best_violation['class_name']} ({best_violation['confidence']:.2f})")
                
                # Recognize plate (if plate camera available)
                plate_result = {'plate_number': None, 'confidence': 0.0}
                if plate_frame is not None:
                    violation_code_temp = f"TEMP-{int(time.time())}"
                    plate_result = plate_recognizer.recognize_plate(
                        plate_frame,
                        violation_code=violation_code_temp,
                        save_image_file=False
                    )
                
                # Get camera info
                camera_info = {
                    'camera_id': 'CAM-WA-001',
                    'location': 'National Road, Odiongan'
                }
                
                # Process through violation logic
                decision = violation_manager.process_detection(
                    detection_result,
                    plate_result,
                    camera_info
                )
                
                if decision['should_log']:
                    violation_code = decision['violation_code']
                    
                    # Capture rider face
                    face_result = face_capture.capture_and_save(
                        wide_frame,
                        best_violation['bbox'],
                        violation_code
                    )
                    
                    # Save plate image if detected
                    plate_image_path = None
                    if plate_result['plate_number'] and plate_frame is not None:
                        plate_result_final = plate_recognizer.recognize_plate(
                            plate_frame,
                            violation_code=violation_code,
                            save_image_file=True
                        )
                        plate_image_path = plate_result_final.get('plate_image_path')
                    
                    # Build violation data
                    violation_data = {
                        'violation_type': best_violation['class_name'],
                        'plate_number': plate_result.get('plate_number'),
                        'rider_image_path': face_result.get('filepath'),
                        'plate_image_path': plate_image_path,
                        'camera_location': camera_info['location'],
                        'camera_id': camera_info['camera_id'],
                        'detection_confidence': best_violation['confidence'],
                        'ocr_confidence': plate_result.get('confidence'),
                        'notes': f"Auto-detected violation. Face quality: {face_result.get('quality_info', {}).get('quality_score', 0):.2f}"
                    }
                    
                    # Log to database
                    violation_id = violation_manager.log_violation(violation_data)
                    
                    if violation_id:
                        logger.info(f"✓ Violation logged: {violation_code} (ID: {violation_id})")
                    else:
                        logger.error(f"✗ Failed to log violation: {violation_code}")
                else:
                    logger.debug(f"Violation not logged: {decision['reason']}")
            
            frame_count += 1
            
            # Log statistics periodically
            if frame_count % 100 == 0:
                stats = violation_manager.get_statistics()
                logger.info(f"Stats: {stats['violations_logged']} logged, {stats['duplicates_prevented']} duplicates prevented")
            
            time.sleep(frame_delay)
        except Exception as e:
            logger.error(f"Processing error: {e}")
            time.sleep(1)
    
    logger.info("Violation processing thread stopped")

# Frontend routes
@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory(app.static_folder, path)

# API health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """System health status"""
    return jsonify({
        'status': 'ok',
        'processing_active': processing_active,
        'cameras_active': video_manager.get_camera_status() if video_manager else {},
        'statistics': violation_manager.get_statistics() if violation_manager else {}
    }), 200

@app.route('/api/control/start', methods=['POST'])
def start_processing():
    """Start violation processing"""
    global processing_thread, processing_active
    
    if processing_active:
        return jsonify({'success': False, 'message': 'Processing already active'}), 400
    
    processing_active = True
    processing_thread = threading.Thread(target=process_violations, daemon=True)
    processing_thread.start()
    
    logger.info("Violation processing started via API")
    return jsonify({'success': True, 'message': 'Processing started'}), 200

@app.route('/api/control/stop', methods=['POST'])
def stop_processing():
    """Stop violation processing"""
    global processing_active
    
    if not processing_active:
        return jsonify({'success': False, 'message': 'Processing not active'}), 400
    
    processing_active = False
    logger.info("Violation processing stopped via API")
    return jsonify({'success': True, 'message': 'Processing stopped'}), 200

def cleanup():
    """Cleanup on shutdown"""
    global processing_active, video_manager
    
    logger.info("Shutting down iCapture System...")
    
    processing_active = False
    
    if video_manager:
        video_manager.stop_all()
    
    db = get_database()
    if db:
        db.disconnect()
    
    logger.info("Shutdown complete")

if __name__ == '__main__':
    try:
        # Initialize system
        if not initialize_system():
            logger.error("System initialization failed, exiting")
            sys.exit(1)
        
        # Start processing thread
        processing_active = True
        processing_thread = threading.Thread(target=process_violations, daemon=True)
        processing_thread.start()
        
        # Run Flask app
        logger.info(f"Starting Flask server on {FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
        app.run(
            host=FLASK_CONFIG['host'],
            port=FLASK_CONFIG['port'],
            debug=False,  # Disable debug to prevent auto-reload flickering
            threaded=FLASK_CONFIG['threaded']
        )
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        cleanup()
