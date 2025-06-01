import cv2
import mediapipe as mp
import numpy as np
import pygame
import os
import math
import time
from tkinter import filedialog, Tk, messagebox

# Save/Load resume position
RESUME_FILE = "resume_info.txt"

def save_resume_info(index, pos):
    with open(RESUME_FILE, "w") as f:
        f.write(f"{index},{pos}")

def load_resume_info():
    if os.path.exists(RESUME_FILE):
        with open(RESUME_FILE, "r") as f:
            try:
                index, pos = f.read().split(",")
                return int(index), float(pos)
            except:
                return 0, 0
    return 0, 0

# Select music folder
root = Tk()
root.withdraw()
choice = messagebox.askquestion("Choose Source", "Use local folder?\nYes = Local Folder\nNo = Project 'songs' Folder")
folder = filedialog.askdirectory(title="Select Music Folder") if choice == 'yes' else os.path.join(os.getcwd(), "songs")
if not folder or not os.path.exists(folder):
    print("Folder not found.")
    exit()

songs = [f for f in os.listdir(folder) if f.endswith(('.mp3', '.wav'))]
if not songs:
    print("No songs found.")
    exit()

pygame.mixer.init()
volume = 0.5
pygame.mixer.music.set_volume(volume)
song_index, pause_pos = load_resume_info()
paused = True

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

volume_locked = False
last_lock_state = None
lock_change_time = 0
lock_cooldown = 1.0
scroll_offset = 0

# Swipe tracking
swipe_in_progress = False
swipe_start_x = 0
swipe_start_time = 0
swipe_threshold = 50  # Lowered threshold for better swipe detection
swipe_cooldown = 1.0
last_swipe_time = 0

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def finger_up(lm, tip, pip):
    return lm[tip][1] < lm[pip][1]

def all_fingers_closed(lm):
    return all(lm[t][1] > lm[t - 2][1] for t in [8, 12, 16, 20])

def index_only_up(lm):
    return (finger_up(lm, 8, 6) and
            not finger_up(lm, 12, 10) and
            not finger_up(lm, 16, 14) and
            not finger_up(lm, 20, 18))

def play_song(index, start_pos=0):
    pygame.mixer.music.load(os.path.join(folder, songs[index]))
    pygame.mixer.music.play(start=start_pos)
    pygame.mixer.music.set_volume(volume)
    print(f"Playing song: {songs[index]} at position {start_pos}")

while True:
    success, img = cap.read()
    if not success:
        break
    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    hand_data, hand_sides = [], []

    if results.multi_hand_landmarks and results.multi_handedness:
        for i in range(len(results.multi_hand_landmarks)):
            side = results.multi_handedness[i].classification[0].label
            lmList = [(int(lm.x * w), int(lm.y * h)) for lm in results.multi_hand_landmarks[i].landmark]
            hand_data.append(lmList)
            hand_sides.append(side)
            mp_draw.draw_landmarks(img, results.multi_hand_landmarks[i], mp_hands.HAND_CONNECTIONS)

        current_time = time.time()

        for i, side in enumerate(hand_sides):
            hand = hand_data[i]

            # Lock/Unlock Volume with RIGHT hand
            if side == "Right":
                thumb_up = finger_up(hand, 4, 3)
                index_up = finger_up(hand, 8, 6)
                if current_time - lock_change_time > lock_cooldown:
                    if thumb_up and not index_up and last_lock_state != 'locked':
                        volume_locked = True
                        last_lock_state = 'locked'
                        lock_change_time = current_time
                        print("Volume locked")
                    elif index_up and not thumb_up and last_lock_state != 'unlocked':
                        volume_locked = False
                        last_lock_state = 'unlocked'
                        lock_change_time = current_time
                        print("Volume unlocked")

            # Volume Control with LEFT hand
            if side == "Left" and not volume_locked:
                d = distance(hand[4], hand[8])
                vol = np.clip(np.interp(d, [30, 200], [0.0, 1.0]), 0.0, 1.0)
                volume = vol
                pygame.mixer.music.set_volume(volume)
                bar = int(np.interp(d, [30, 200], [400, 200]))
                cv2.rectangle(img, (50, 200), (85, 400), (0, 255, 0), 3)
                cv2.rectangle(img, (50, bar), (85, 400), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, f'{int(vol * 100)}%', (50, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
                cv2.line(img, hand[4], hand[8], (255, 0, 255), 3)

            # Play/Pause, Swipe for LEFT hand
            if side == "Left":
                cx = hand[8][0]

                # Play if index and middle fingers up
                if finger_up(hand, 8, 6) and finger_up(hand, 12, 10) and paused:
                    play_song(song_index, pause_pos)
                    paused = False
                    time.sleep(0.3)

                # Pause if all fingers closed
                elif all_fingers_closed(hand) and not paused:
                    pause_pos = pygame.mixer.music.get_pos() / 1000.0
                    save_resume_info(song_index, pause_pos)
                    pygame.mixer.music.pause()
                    paused = True
                    time.sleep(0.3)

                # Swipe (index only up)
                elif index_only_up(hand):
                    if not swipe_in_progress:
                        swipe_start_x = cx
                        swipe_start_time = current_time
                        swipe_in_progress = True
                        print(f"Swipe started at x={swipe_start_x}")
                    else:
                        dx = cx - swipe_start_x
                        print(f"Swipe progress dx={dx}")

                        if abs(dx) > swipe_threshold and (current_time - last_swipe_time > swipe_cooldown):
                            if dx > 0:
                                song_index = (song_index + 1) % len(songs)
                                print("Swiped Right -> Next song")
                            else:
                                song_index = (song_index - 1 + len(songs)) % len(songs)
                                print("Swiped Left -> Previous song")
                            pause_pos = 0
                            save_resume_info(song_index, pause_pos)
                            play_song(song_index)
                            paused = False
                            last_swipe_time = current_time
                            swipe_in_progress = False
                            time.sleep(0.3)
                else:
                    swipe_in_progress = False
    else:
        text = "Show Your Hand Gesture"
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)
        cv2.putText(img, text, ((w - text_w) // 2, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 3)

    title = f"🎵 {songs[song_index]}"
    scroll_offset = (scroll_offset + 1) % (len(title) * 12)
    x = 10 - scroll_offset % (len(title) * 12)
    cv2.putText(img, title, (x, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    lock_text = "Volume Locked" if volume_locked else "Volume Adjustable"
    (text_w, _) = cv2.getTextSize(lock_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    cv2.putText(img, lock_text, (w - text_w - 10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 205, 50), 2)

    cv2.imshow("Gesture Music Controller", img)
    if cv2.waitKey(1) == 27:
        break

if not paused:
    pause_pos = pygame.mixer.music.get_pos() / 1000.0
save_resume_info(song_index, pause_pos)

cap.release()
cv2.destroyAllWindows()
