import cv2
import time
import numpy as np
import math
import pyautogui  # To simulate media key presses

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import HandTrackingModule as htm  # Your custom hand tracking module

# Camera setup
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

# Hand detector initialization
detector = htm.handDetector(detectionCon=0.7)

# Audio volume control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Get volume range for mapping
volRange = volume.GetVolumeRange()
minVol, maxVol = volRange[0], volRange[1]

# Volume bar params
volBarPos = 400  # Bottom Y coordinate of the bar
volBarHeight = 150  # Height of the volume bar

# For swipe detection
prev_x = None
swipe_time = 0
swipe_detected = False

running = True

while running:
    success, img = cap.read()
    if not success:
        continue

    img = detector.findHands(img, draw=True)
    lmlist = detector.findPosition(img, draw=True)

    if lmlist:
        fingers = detector.fingersUp()  # List like [1,1,1,1,1]

        x1, y1 = lmlist[4][1], lmlist[4][2]  # Thumb tip
        x2, y2 = lmlist[8][1], lmlist[8][2]  # Index tip
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        # Control volume by distance between thumb and index
        vol = np.interp(length, [20, 120], [minVol, maxVol])
        volume.SetMasterVolumeLevel(vol, None)
        volBar = np.interp(length, [20, 150], [volBarPos, volBarPos - volBarHeight])

        # Draw volume bar
        cv2.rectangle(img, (50, volBarPos - volBarHeight), (85, volBarPos), (0, 255, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, volBarPos), (0, 255, 0), cv2.FILLED)

        # Draw circles and line with colors
        cv2.circle(img, (x1, y1), 6, (0, 140, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 6, (255, 255, 0), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 6, (255, 0, 255), cv2.FILLED)

        # Highlight pinch
        if length < 50:
            cv2.circle(img, (cx, cy), 6, (0, 255, 255), cv2.FILLED)

        # Display volume value
        cv2.putText(img, f'Vol: {vol:.2f}', (40, volBarPos + 40),
                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)

        # Gesture Controls:
        # Open palm (5 fingers) → Play music
        if fingers == [1, 1, 1, 1, 1]:
            cv2.putText(img, "Play", (500, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
            pyautogui.press('playpause')  # Toggles play/pause on most media players
            time.sleep(1)  # Prevent multiple rapid triggers

        # Fist (0 fingers) → Pause music
        elif fingers == [0, 0, 0, 0, 0]:
            cv2.putText(img, "Pause", (500, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
            pyautogui.press('playpause')
            time.sleep(1)

        # Swipe right detection (track wrist or palm base x movement)
        wrist_x = lmlist[0][1]  # Wrist x-coordinate

        if prev_x is not None:
            diff = wrist_x - prev_x

            # Threshold for swipe detection (adjust as needed)
            if diff > 50 and not swipe_detected and (time.time() - swipe_time) > 2:
                cv2.putText(img, "Next Song", (500, 120), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)
                pyautogui.press('nexttrack')  # Next song media key
                swipe_detected = True
                swipe_time = time.time()

            # Reset swipe detection if hand stops moving
            if diff < 10:
                swipe_detected = False

        prev_x = wrist_x

    # FPS display
    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 70),
                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Img", img)

    key = cv2.waitKey(1)
    if key == 27:
        running = False

cap.release()
cv2.destroyAllWindows()
