import numpy as np
import cv2

def get_limits(color, hue_offset=10, saturation_offset=40, value_offset=50):
    c = np.uint8([[color]]) 
    hsvC = cv2.cvtColor(c, cv2.COLOR_BGR2HSV)
    hue = hsvC[0][0][0]
    saturation = hsvC[0][0][1]
    value = hsvC[0][0][2]

    
    lower_hue = max(0, hue - hue_offset)
    upper_hue = min(180, hue + hue_offset)

    
    lower_saturation = max(0, saturation - saturation_offset)
    upper_saturation = min(255, saturation + saturation_offset)
    lower_value = max(0, value - value_offset)
    upper_value = min(255, value + value_offset)

    
    lower_limit = np.array([lower_hue, lower_saturation, lower_value], dtype=np.uint8)
    upper_limit = np.array([upper_hue, upper_saturation, upper_value], dtype=np.uint8)

    return lower_limit, upper_limit

def get_black_limits():
    lower_black = np.array([0, 0, 0], dtype=np.uint8)
    upper_black = np.array([180, 255, 50], dtype=np.uint8)
    return lower_black, upper_black

def get_white_limits():
    lower_white = np.array([0, 0, 200], dtype=np.uint8)
    upper_white = np.array([180, 30, 255], dtype=np.uint8)
    return lower_white, upper_white
