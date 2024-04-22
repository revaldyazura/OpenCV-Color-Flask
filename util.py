import numpy as np
import cv2


def get_limits(color):
    c = np.uint8([[color]])  # BGR values
    hsvC = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)

    hue, saturation, value = hsvC[0][0]  # Get the HSV components

    # Define a range around the hue value
    hue_lower = hue - 10 if hue > 10 else 0
    hue_upper = hue + 10 if hue < 245 else 255

    # Use the extracted saturation and value
    saturation_lower = max(0, saturation - 30)  # Adjust based on color characteristics
    saturation_upper = min(255, saturation + 30)
    value_lower = max(0, value - 30)
    value_upper = min(255, value + 30)

    lowerLimit = np.array([hue_lower, saturation_lower, value_lower], dtype=np.uint8)
    upperLimit = np.array([hue_upper, saturation_upper, value_upper], dtype=np.uint8)

    return lowerLimit, upperLimit
