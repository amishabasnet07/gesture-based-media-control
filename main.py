import cv2
import time
import os
import numpy as np
import math
from pygame import mixer
import HandTrackingModule as htm
from youtube_downloader import download_audio_from_youtube  # ✅ Added this

# INIT
mixer.init()

# Download a YouTube audio and add it to the playlist ✅
url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"  # 👈 Replace with your link
downloaded_song = download_audio_from_youtube(url)

song_folder = "songs"
songs = os.listdir(song_folder)
songs = [song for song in songs if song.endswith(".mp3")]  # Filter only mp3s
current_song_index = songs.index(downloaded_song) if downloaded_song in songs else 0

mixer.music.load(os.path.join(song_folder, songs[current_song_index]))
mixer.music.play()

# CAMERA
cap = cv2.VideoCapture(0)
detector = htm.handDetector(detectionCon=0.7)
pTime = 0

def countFingers(lmList):
    fingers = []
    tipIds = [4, 8, 12, 16, 20]

    if lmList[tipIds[0]][1] < lmList[tipIds[0] - 1][1]:  # Thumb
        fingers.append(1)
    else:
        fingers.append(0)

    for id in range(1, 5):
        if lmList[tipIds[id]][2] < lmList[tipIds[id] - 2][2]:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers.count(1)

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    if lmList:
        fingersUp = countFingers(lmList)

        # Volume Control
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        length = math.hypot(x2 - x1, y2 - y1)
        vol = np.interp(length, [20, 150], [0, 1])
        mixer.music.set_volume(vol)

        # Control
        if fingersUp == 5:
            mixer.music.unpause()
            cv2.putText(img, "Play", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)
        elif fingersUp == 0:
            mixer.music.pause()
            cv2.putText(img, "Pause", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
        elif fingersUp == 1:
            current_song_index = (current_song_index + 1) % len(songs)
            mixer.music.load(os.path.join(song_folder, songs[current_song_index]))
            mixer.music.play()
            time.sleep(1)
        elif fingersUp == 2:
            current_song_index = (current_song_index - 1) % len(songs)
            mixer.music.load(os.path.join(song_folder, songs[current_song_index]))
            mixer.music.play()
            time.sleep(1)

    # FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Media Player", img)
    if cv2.waitKey(1) == 27:  # ESC key
        break

cap.release()
cv2.destroyAllWindows()
