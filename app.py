from util import get_limits
from flask import Flask, render_template, Response, request, jsonify
from PIL import Image
import cv2

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
    color_name = data['colorName']
    bgr_values = data['bgrValues']
    colors[color_name] = bgr_values
    return jsonify({'message': 'Color added successfully'})

@app.route('/reset_colors', methods=['DELETE'])
def reset_colors():
    # Handle resetting color values
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

            for color_name, color_value in colors.items():
                lower_limit, upper_limit = get_limits(color=color_value)
                mask = cv2.inRange(hsvImage, lower_limit, upper_limit)
                bbox = Image.fromarray(mask).getbbox()

                if bbox is not None:
                    x1, y1, x2, y2 = bbox
                    frame = cv2.rectangle(frame, (x1, y1), (x2, y2), color_value, 5)
                    cv2.putText(frame, color_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_value, 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)
