from util import get_limits, get_black_limits, get_white_limits
from flask import Flask, render_template, Response, request, jsonify
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)

camera = None

def initialize_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(1)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

colors = {}
matching_areas = []

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
        success, frame = camera.read()
        if not success:
            break
        else:
            hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # combined_mask = np.zeros(hsvImage.shape[:2], dtype=np.uint8)
            
            colors_copy = colors.copy()

            for bgr_values in colors_copy.values():
                if bgr_values == (0, 0, 0):
                    lower_limit, upper_limit = get_black_limits()
                elif bgr_values == (255, 255, 255):
                    lower_limit, upper_limit = get_white_limits()
                else:
                    lower_limit, upper_limit = get_limits(color=bgr_values)
                mask = cv2.inRange(hsvImage, lower_limit, upper_limit)
                # Combine masks for different colors
                # combined_mask = cv2.bitwise_or(combined_mask, mask)

                # Apply morphological operations to reduce noise
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                # combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
                # combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

                # Find contours in the mask
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > 1000:  # Filter out small contours by area
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

@app.route('/release', methods=['POST'])
def release_camera():
    reset_colors()
    if camera.isOpened():
        camera.release()
        return jsonify({"message": "Camera shutdown successfully"}), 200
    else:
        return jsonify({"message": "Camera is not active"}), 400

if __name__ == "__main__":
    app.run(debug=True)
