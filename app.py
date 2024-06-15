from util import get_limits
from flask import Flask, render_template, Response, request, jsonify
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__) # initialize flask app

camera = cv2.VideoCapture(0) # set camera that going to use
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) # set camera resolution
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

colors = {} # store colors value in object 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_color', methods=['POST'])
def add_color():
    data = request.json
    # color_name = data['colorName']
    bgr_values = tuple(data['bgrValues'])
    colors[bgr_values] = bgr_values
    return jsonify({'message': 'Color added successfully'})

@app.route('/reset_colors', methods=['DELETE'])
def reset_colors():
    global colors
    colors = {}
    return jsonify({'message': 'Color values reset successfully'})

def generate_frames():
    kernel = np.ones((5, 5), np.uint8)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            for bgr_values in colors.values():
                lower_limit, upper_limit = get_limits(color=bgr_values)
                mask = cv2.inRange(hsvImage, lower_limit, upper_limit)
                dilated_mask = cv2.dilate(mask, kernel, iterations=1)
                bbox = Image.fromarray(dilated_mask).getbbox()

                if bbox is not None:
                    x1, y1, x2, y2 = bbox
                    frame = cv2.rectangle(frame, (x1, y1), (x2, y2), bgr_values, 5)
                    cv2.putText(frame, str(bgr_values), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, bgr_values, 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)
