import cv2
import mediapipe as mp
import pyautogui
import time
import subprocess
import psutil
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Volume setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# VLC path & song folder path
vlc_path = "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
song_folder_path = "D:\\song"

def is_vlc_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and 'vlc' in proc.info['name'].lower():
            return proc
    return None

def is_vlc_idle():
    # VLC idle check using window title
    for proc in psutil.process_iter(['name', 'cmdline']):
        if proc.info['name'] and 'vlc' in proc.info['name'].lower():
            cmdline = proc.info['cmdline']
            if '--started-from-file' in cmdline or len(cmdline) == 1:
                return True
    return False

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_draw = mp.solutions.drawing_utils

            #   Time duration
last_action_time = time.time()
action_delay = 1.5
vlc_last_open_time = 0
vlc_protection_delay = 3
action_text = ""

def get_finger_status(lm_list):
    def is_up(tip, dip):
        return lm_list[tip][1] < lm_list[dip][1]
    return [
        lm_list[4][0] > lm_list[3][0],  # Thumb
        is_up(8, 6),
        is_up(12, 10),
        is_up(16, 14),
        is_up(20, 18)
    ]

while True:
    success, image = cap.read()
    image = cv2.flip(image, 1)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    total_fingers = 0
    hand_landmarks_list = []

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            lm_list = []
            h, w, c = image.shape
            for lm in hand_landmarks.landmark:
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((cx, cy))
            hand_landmarks_list.append(lm_list)

        current_time = time.time()
        if current_time - last_action_time > action_delay:

            all_fingers = []
            for lm_list in hand_landmarks_list:
                fingers = get_finger_status(lm_list)
                total_fingers += fingers.count(True)
                all_fingers.append(fingers)

            if len(hand_landmarks_list) == 1:
                lm_list = hand_landmarks_list[0]
                fingers = all_fingers[0]

                if fingers[1] and not fingers[2]:
                    pyautogui.press('space')
                    action_text = "Play / Pause"
                elif lm_list[4][0] - lm_list[0][0] > 60:
                    pyautogui.press('right')
                    action_text = "Fast Forward"
                elif lm_list[0][0] - lm_list[4][0] > 60:
                    pyautogui.press('left')
                    action_text = "Rewind"
                elif total_fingers == 2:
                    current_vol = volume.GetMasterVolumeLevelScalar()
                    volume.SetMasterVolumeLevelScalar(min(current_vol + 0.1, 1.0), None)
                    action_text = "Volume Up"
                elif total_fingers == 3:
                    current_vol = volume.GetMasterVolumeLevelScalar()
                    volume.SetMasterVolumeLevelScalar(max(current_vol - 0.1, 0.0), None)
                    action_text = "Volume Down"
                elif total_fingers == 5:
                    if not is_vlc_running():
                        try:
                            subprocess.Popen([vlc_path])
                            vlc_last_open_time = current_time
                            action_text = "VLC Opened"
                        except:
                            action_text = "VLC Not Found"
                    else:
                        action_text = "VLC Already Running"
                elif fingers == [False, True, True, True, True]:
                    if current_time - vlc_last_open_time > vlc_protection_delay:
                        proc = is_vlc_running()
                        if proc:
                            proc.terminate()
                            action_text = "VLC Closed"
                        else:
                            action_text = "VLC Not Running"
                    else:
                        action_text = "Ignore Close"

            if total_fingers == 6:
                pyautogui.press('nexttrack')
                action_text = "Next Song"
            elif total_fingers == 7:
                pyautogui.press('prevtrack')
                action_text = "Previous Song"

            # 8 Fingers → Play folder in existing VLC if idle
            elif total_fingers == 8:
                if is_vlc_running() and is_vlc_idle():
                    try:
                        subprocess.Popen([vlc_path, "--one-instance", "--playlist-enqueue", song_folder_path])
                        action_text = "Playing D:\\song in VLC"
                    except:
                        action_text = "Failed to play folder"
                else:
                    action_text = "VLC not idle or not open"

            last_action_time = current_time

    if action_text:
        cv2.putText(image, action_text, (30, 60), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (0, 255, 0), 3)

    cv2.imshow("Gesture Media Controller", image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
