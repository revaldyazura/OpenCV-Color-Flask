from util import get_limits, get_black_limits, get_white_limits
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
import cv2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

camera = None
camera_active = False

def initialize_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(1)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

colors = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_color', methods=['POST'])
def add_color():
    data = request.json
    bgr_values = tuple(data['bgrValues'])
    colors[bgr_values] = bgr_values
    return jsonify({'message': 'Color added successfully'})

@app.route('/reset_colors', methods=['DELETE'])
def reset_colors():
    global colors
    colors = {}
    return jsonify({'message': 'Color values reset successfully'})

def generate_frames():
    while True:
        if not camera_active:
            # Gambar pengganti ketika kamera tidak aktif
            replacement_image = cv2.imread('https://firebasestorage.googleapis.com/v0/b/obras-7eb0b.appspot.com/o/there-is-no-connected-camera.jpg?alt=media&token=e512eeb6-d19d-4826-abca-bc54169aa2ee')
            ret, buffer = cv2.imencode('.jpg', replacement_image)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            continue
        
        success, frame = camera.read()
        if not success:
            break
        else:
            hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            for bgr_values in colors.values():
                if bgr_values == (0, 0, 0):
                    lower_limit, upper_limit = get_black_limits()
                elif bgr_values == (255, 255, 255):
                    lower_limit, upper_limit = get_white_limits()
                else:
                    lower_limit, upper_limit = get_limits(color=bgr_values)
                mask = cv2.inRange(hsvImage, lower_limit, upper_limit)

                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > 1000:
                        x, y, w, h = cv2.boundingRect(contour)
                        frame = cv2.rectangle(frame, (x, y), (x + w, y + h), bgr_values, 5)
                        cv2.putText(frame, str(bgr_values), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr_values, 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    initialize_camera()
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/activate_camera', methods=['POST'])
def activate_camera():
    global camera_active
    camera_active = True
    socketio.emit('camera_status', {'isVideoActive': True})
    return jsonify({'message': 'Camera activated'})

@app.route('/deactivate_camera', methods=['POST'])
def deactivate_camera():
    global camera_active
    camera_active = False
    global camera
    reset_colors()
    if camera.isOpened():
        camera.release()
        socketio.emit('camera_status', {'isVideoActive': False})
        return jsonify({"message": "Camera deactivated successfully"}), 200
    else:
        socketio.emit('camera_status', {'isVideoActive': False})
        return jsonify({"message": "Camera is not active"}), 400

@app.route('/camera_status', methods=['GET'])
def camera_status():
    global camera_active
    return jsonify({'isVideoActive': camera_active})

@socketio.on('message')
def handle_message(message):
    emit('message', message, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
