import screen_brightness_control as sbc
import winsound
import time
import urllib.request

# --- CONFIGURATION ---
IPHONE_WEBHOOK_URL = "https://api.pushcut.io/9xNWvZoaoorQYcx1sBHJr/notifications/TurnOnFocus"

# STATE TRACKING
last_beep_time = 0
is_dimmed = False
original_brightness = 100
is_focus_mode_active = False

def init():
    global original_brightness
    try:
        current = sbc.get_brightness()
        if current:
            original_brightness = current[0]
    except:
        original_brightness = 100

def trigger_fatigue_alert():
    global is_dimmed
    if not is_dimmed:
        try:
            sbc.set_brightness(20)
            is_dimmed = True
            winsound.Beep(500, 500) # Low pitch warning
        except Exception as e:
            print(f"Brightness Error: {e}")

def trigger_distraction_alert():
    global last_beep_time
    current_time = time.time()
    if current_time - last_beep_time > 2:
        winsound.Beep(1000, 200) # High pitch warning
        last_beep_time = current_time

def trigger_focus_mode():
    global is_focus_mode_active
    # We allow it to trigger multiple times for testing
    try:
        print(f"Attempting to trigger iPhone...")
        
        # 1. SEND SIGNAL
        with urllib.request.urlopen(IPHONE_WEBHOOK_URL) as response:
            if response.getcode() == 200:
                print(">>> SUCCESS: iPhone Focus Mode Triggered! <<<")
                
                # 2. PLAY VICTORY SOUND (Audio Verification)
                # This proves to the professor that the system worked
                winsound.Beep(1000, 100)
                winsound.Beep(1500, 100)
                winsound.Beep(2000, 400) # Rising tone "Ding-Ding-DING!"
                
                is_focus_mode_active = True
            else:
                print(f">>> FAIL: Server returned code {response.getcode()} <<<")
    except Exception as e:
        print(f">>> ERROR connecting to iPhone: {e} <<<")

def reset_screen():
    global is_dimmed
    if is_dimmed:
        try:
            sbc.set_brightness(original_brightness)
            is_dimmed = False
        except:
            pass