import cv2
import time
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import HandTrackinModule as htm  # Your custom hand tracking module

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

running = True  # Control variable to stop the loop

while running:
    success, img = cap.read()
    if not success:
        continue  # Skip if frame not read properly

    img = detector.findHands(img, draw=True)
    lmlist = detector.findPosition(img, draw=True)

    if lmlist:
        x1, y1 = lmlist[4][1], lmlist[4][2]  # Thumb tip
        x2, y2 = lmlist[8][1], lmlist[8][2]  # Index tip
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        # Draw smaller circles and line between thumb and index finger with attractive colors
        cv2.circle(img, (x1, y1), 6, (0, 140, 255), cv2.FILLED)       # Thumb: bright orange (BGR)
        cv2.circle(img, (x2, y2), 6, (255, 255, 0), cv2.FILLED)       # Index: bright cyan
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)           # Line: magenta
        cv2.circle(img, (cx, cy), 6, (255, 0, 255), cv2.FILLED)       # Center: magenta

        # Calculate distance between thumb and index finger
        length = math.hypot(x2 - x1, y2 - y1)

        # Map the length to volume range
        vol = np.interp(length, [20, 120], [minVol, maxVol])
        volume.SetMasterVolumeLevel(vol, None)

        # Map length to volume bar position (for visual bar)
        volBar = np.interp(length, [20, 150], [volBarPos, volBarPos - volBarHeight])

        # Draw volume bar
        cv2.rectangle(img, (50, volBarPos - volBarHeight), (85, volBarPos), (0, 255, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, volBarPos), (0, 255, 0), cv2.FILLED)

        # Display the volume in raw range (e.g., -65.25 to 0.0)
        cv2.putText(img, f'Vol: {vol:.2f}', (40, volBarPos + 40),
                    cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)

        # Highlight if fingers are close (pinch)
        if length < 50:
            cv2.circle(img, (cx, cy), 6, (0, 255, 255), cv2.FILLED)     # Highlight: bright yellow

    # Calculate and display FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 70),
                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Img", img)

    # Wait for 1ms and check if ESC is pressed (27 is ESC)
    key = cv2.waitKey(1)
    if key == 27:
        running = False  # Stop the loop without using break

# Cleanup
cap.release()
cv2.destroyAllWindows()
