import cv2
import os
import mediapipe as mp
from tkinter import Tk, filedialog
import pyfirmata2
import numpy as np
from PIL import Image

# Setup Arduino and pins
finger_angle = 115
BOARD_PORT = "COM8"
board = pyfirmata2.Arduino(BOARD_PORT)
iterator = pyfirmata2.util.Iterator(board)
iterator.start()

# Define servo pins
fingers_pins = {
    "RIGHT_PINKY": board.get_pin('d:2:s'),
    "RIGHT_MIDDLE": board.get_pin('d:3:s'),
    "RIGHT_RING": board.get_pin('d:4:s'),
    "RIGHT_INDEX": board.get_pin('d:5:s'),
    "RIGHT_THUMB": board.get_pin('d:6:s'),
    "LEFT_RING": board.get_pin('d:8:s'),
    "LEFT_MIDDLE": board.get_pin('d:9:s'),
    "LEFT_THUMB": board.get_pin('d:10:s'),
    "LEFT_PINKY": board.get_pin('d:11:s'),
    "LEFT_INDEX": board.get_pin('d:12:s')
}

# Move servo function
def move_servo(pin, index, fingers_statuses):
    status = 0 if not fingers_statuses[index] else finger_angle
    if index.startswith("LEFT"):
        status = 180 if not fingers_statuses[index] else 180 - finger_angle
    pin.write(status)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_drawing = mp.solutions.drawing_utils

# Function to detect hands in an image
def detect_hands(image):
    imgRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    return results

# Function to count the number of raised fingers
def count_fingers_from_results(results):
    fingers_statuses = {finger: False for finger in fingers_pins.keys()}
    count = {'RIGHT': 0, 'LEFT': 0}

    if results.multi_hand_landmarks:
        for hand_index, hand_info in enumerate(results.multi_handedness):
            hand_label = hand_info.classification[0].label.upper()
            hand_landmarks = results.multi_hand_landmarks[hand_index]
            fingers_tips_ids = [
                mp_hands.HandLandmark.INDEX_FINGER_TIP,
                mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                mp_hands.HandLandmark.RING_FINGER_TIP,
                mp_hands.HandLandmark.PINKY_TIP
            ]

            for tip_id in fingers_tips_ids:
                finger_name = tip_id.name.split("_")[0]
                pip_joint = tip_id - 2  # Compare with PIP joint
                if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[pip_joint].y:
                    fingers_statuses[f"{hand_label}_{finger_name}"] = True
                    count[hand_label] += 1

            # Thumb check
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
            thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP]

            if hand_label == 'RIGHT':
                if thumb_tip.x < thumb_mcp.x and thumb_tip.y < thumb_ip.y:
                    fingers_statuses[f"{hand_label}_THUMB"] = True
                    count[hand_label] += 1
            else:
                if thumb_tip.x > thumb_mcp.x and thumb_tip.y < thumb_ip.y:
                    fingers_statuses[f"{hand_label}_THUMB"] = True
                    count[hand_label] += 1

    return fingers_statuses, count

# Move robotic hands based on detected gestures
def move_robotic_hands(fingers_statuses):
    for finger, status in fingers_statuses.items():
        move_servo(fingers_pins[finger], finger, fingers_statuses)

# Load image using PIL and convert to numpy array
def load_image(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        return np.array(img)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

# Process images from a folder
def process_images_from_folder(folder_path):
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    if not image_files:
        print("No images found in the selected folder.")
        return

    for image_file in image_files:
        image_path = os.path.normpath(os.path.join(folder_path, image_file))
        print(f"Processing: {image_path}")

        image = load_image(image_path)
        if image is None:
            continue

        results = detect_hands(image)
        fingers_statuses, count = count_fingers_from_results(results)
        move_robotic_hands(fingers_statuses)

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imshow('Hand Gesture', image)
        cv2.waitKey(3000)

    cv2.destroyAllWindows()

# Main function to process the folder of images
if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="Select a Folder with Images")

    if folder_selected:
        process_images_from_folder(folder_selected)
    else:
        print("No folder selected.")
