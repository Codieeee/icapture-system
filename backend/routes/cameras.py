"""
Camera API Routes for iCapture System
Camera status and live feeds
"""

from flask import Blueprint, Response, jsonify
import cv2
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from modules.database import get_database
from utils.logger import get_logger

logger = get_logger('routes_cameras')

cameras_bp = Blueprint('cameras', __name__, url_prefix='/api/cameras')

# This will be set by the main app
video_capture_manager = None

def set_video_manager(manager):
    """Set the video capture manager instance"""
    global video_capture_manager
    video_capture_manager = manager

@cameras_bp.route('/status', methods=['GET'])
def get_camera_status():
    """Get status of all cameras"""
    try:
        db = get_database()
        cameras = db.get_camera_status()
        
        # Add live status from video manager if available
        if video_capture_manager:
            live_status = video_capture_manager.get_camera_status()
            for cam in cameras:
                cam_type = 'wide_angle' if 'WA' in cam['camera_id'] else 'plate'
                if cam_type in live_status:
                    cam['is_streaming'] = live_status[cam_type]['active']
        
        # Convert datetime
        for cam in cameras:
            if cam.get('last_frame_time'):
                cam['last_frame_time'] = cam['last_frame_time'].isoformat()
            if cam.get('installed_date'):
                cam['installed_date'] = str(cam['installed_date'])
        
        return jsonify({'success': True, 'data': cameras}), 200
    except Exception as e:
        logger.error(f"Error fetching camera status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_mjpeg_stream(camera_type):
    """Generate MJPEG stream from camera"""
    while True:
        if video_capture_manager:
            frame = video_capture_manager.get_frame(camera_type)
            
            if frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Small delay to control frame rate
        import time
        time.sleep(0.033)  # ~30 FPS

@cameras_bp.route('/feed/<camera_type>', methods=['GET'])
def get_camera_feed(camera_type):
    """
    Get live MJPEG stream from camera
    camera_type: 'wide_angle' or 'plate'
    """
    if camera_type not in ['wide_angle', 'plate']:
        return jsonify({'success': False, 'error': 'Invalid camera type'}), 400
    
    if not video_capture_manager:
        return jsonify({'success': False, 'error': 'Video manager not initialized'}), 503
    
    return Response(
        generate_mjpeg_stream(camera_type),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
