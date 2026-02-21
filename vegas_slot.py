import cv2
import numpy as np
import time


# ============================================================
# Vegas Slot Machine (Computer Vision)
# - Uses frame differencing in a lever ROI
# - Tracks motion centroid to require a TOP->BOTTOM pull gesture
# - Triggers a timed spin, then scores once when spin ends
# ============================================================


# ----------------------------
# Camera setup
# ----------------------------
# On Windows, CAP_DSHOW is often the most reliable.
# If it fails on another OS, you can change to cv2.VideoCapture(0).
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError("Cannot open camera. Try changing camera index (0/1/2) or remove CAP_DSHOW.")


# ----------------------------
# Tunable parameters (your tuned values)
# ----------------------------
ROI_START = 0.7            # right 30% of screen is "lever zone"
MOTION_THRESHOLD = 25000   # (kept for debugging / optional gating)

TOP_FRAC = 0.35            # top zone boundary (as fraction of frame height)
BOTTOM_FRAC = 0.70         # bottom zone boundary (as fraction of frame height)
MIN_MOTION_PIXELS = 1000   # require this many white pixels in motion mask to consider motion
PULL_TIMEOUT = 0.7         # seconds allowed to go top -> bottom

cooldown_seconds = 1.0     # minimum time between spins
spin_duration = 1.2        # seconds the reels "spin"
result_display_seconds = 2.0
jackpot_flash_seconds = 2.0


# ----------------------------
# Slot machine config
# ----------------------------
symbols = ["CHERRY", "DIAMOND", "7", "LEMON", "BELL"]
final_reels = ["?", "?", "?"]


# ----------------------------
# State variables
# ----------------------------
prev_frame = None

money = 100

last_spin_time = 0.0
spinning_until = 0.0
was_spinning = False

# Pull detection FSM
pull_state = "IDLE"  # IDLE -> ARMED -> (SPIN) -> IDLE
armed_time = 0.0

# UI message persistence
result_text = "PULL TO SPIN"
result_until = 0.0

# Jackpot flashing persistence
jackpot_until = 0.0


def compute_motion_mask(prev_roi_blur, roi_blur, thresh_val=25):
    """
    Compute binary motion mask using abs diff + threshold.
    Returns thresh (binary image of motion).
    """
    diff = cv2.absdiff(prev_roi_blur, roi_blur)
    _, thresh = cv2.threshold(diff, thresh_val, 255, cv2.THRESH_BINARY)
    return thresh


while True:
    ret, frame = cap.read()
    if not ret:
        break

    now = time.time()

    # ----------------------------
    # Preprocess frame
    # ----------------------------
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (21, 21), 0)

    h, w = gray.shape
    x0 = int(w * ROI_START)

    # Lever ROI is right-side vertical strip
    roi = blur[:, x0:w]

    if prev_frame is None:
        prev_frame = blur
        continue

    prev_roi = prev_frame[:, x0:w]

    # ----------------------------
    # Motion detection
    # ----------------------------
    thresh = compute_motion_mask(prev_roi, roi, thresh_val=25)

    # motion_score retained for debugging/tuning
    motion_score = np.sum(thresh) / 255.0

    # Centroid of motion pixels in ROI
    ys, xs = np.where(thresh > 0)
    motion_pixels = len(xs)
    centroid_y = float(np.mean(ys)) if motion_pixels > 0 else None

    # ----------------------------
    # Pull detection FSM (top -> bottom within timeout)
    # ----------------------------
    top_y = h * TOP_FRAC
    bottom_y = h * BOTTOM_FRAC

    # only allow starting a spin if not currently spinning + cooldown passed
    can_spin = (now - last_spin_time) > cooldown_seconds and now >= spinning_until

    # Optional additional gating using MOTION_THRESHOLD (not strictly required)
    # If you find false positives, uncomment:
    # can_spin = can_spin and (motion_score < MOTION_THRESHOLD * 10)  # example gating

    if centroid_y is not None and motion_pixels > MIN_MOTION_PIXELS:
        # Draw centroid dot (yellow)
        cx = x0 + int(np.mean(xs))
        cy = int(centroid_y)
        cv2.circle(frame, (cx, cy), 8, (0, 255, 255), -1)

        if pull_state == "IDLE":
            # Arm only if motion starts near the TOP zone
            if centroid_y < top_y:
                pull_state = "ARMED"
                armed_time = now

        elif pull_state == "ARMED":
            # If too slow, disarm
            if (now - armed_time) > PULL_TIMEOUT:
                pull_state = "IDLE"
            # Trigger when centroid goes below the bottom line
            elif centroid_y > bottom_y and can_spin:
                last_spin_time = now
                spinning_until = now + spin_duration
                final_reels = list(np.random.choice(symbols, size=3))
                pull_state = "IDLE"
    else:
        # No meaningful motion -> reset to avoid accidental arming
        pull_state = "IDLE"

    # ----------------------------
    # Spin display
    # ----------------------------
    is_spinning = now < spinning_until
    if is_spinning:
        display_reels = ["|", "|", "|"]
    else:
        display_reels = final_reels

    # ----------------------------
    # Score exactly ONCE when spin ends (transition True -> False)
    # ----------------------------
    if was_spinning and not is_spinning:
        if final_reels[0] == final_reels[1] == final_reels[2]:
            money += 50
            result_text = "JACKPOT +$50"
            status_color = (0, 215, 255)  # gold
            jackpot_until = now + jackpot_flash_seconds
        elif len(set(final_reels)) == 2:
            money += 10
            status_color = (0,255,0) #green
            result_text = "NICE +$10"
            #status_color = (0,255,0) #green
        else:
            money -= 5
            result_text = "LOSE -$5"
            status_color = (0, 0, 255) #red

        result_until = now + result_display_seconds

    # Status line logic
    if is_spinning:
        status_text = "SPINNING..."
        status_color = (255, 255, 255)  # white

    else:
        if now < result_until:
            status_text = result_text
            # keep previous status_color (green/red)
        else:
            status_text = "PULL TO SPIN"
            status_color = (255, 255, 255)

    was_spinning = is_spinning  # must update every frame

    # ----------------------------
    # UI overlay
    # ----------------------------
    # Lever zone box
    cv2.rectangle(frame, (x0, 0), (w, h), (0, 255, 0), 2)
    cv2.putText(frame, "LEVER ZONE", (x0 + 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Top/bottom guide lines
    cv2.line(frame, (x0, int(top_y)), (w, int(top_y)), (255, 255, 0), 2)
    cv2.line(frame, (x0, int(bottom_y)), (w, int(bottom_y)), (255, 255, 0), 2)
    cv2.putText(frame, f"state: {pull_state}", (x0 + 10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # Reels display
    cv2.putText(frame, f"{display_reels[0]} | {display_reels[1]} | {display_reels[2]}",
                (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

    # Money + status
    cv2.putText(frame, f"MONEY: ${money}", (30, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
    cv2.putText(frame, status_text, (30, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 3)

    # Debug: motion score
    cv2.putText(frame, f"motion_score: {int(motion_score)}  motion_pixels: {motion_pixels}",
                (30, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Jackpot flashing overlay (fixed: timer-based, drawn every frame for N seconds)
    if now < jackpot_until:
        color = (0, 0, 255) if int(now * 12) % 2 == 0 else (0, 255, 255)
        cv2.putText(frame, "!!! JACKPOT !!!",
                    (60, 330), cv2.FONT_HERSHEY_SIMPLEX, 1.8, color, 5)

    # Show windows
    cv2.imshow("Vegas Slot Machine", frame)
    # cv2.imshow("Motion Mask", thresh)  # uncomment if you want to see the mask

    key = cv2.waitKey(10) & 0xFF
    if key == ord('q') or key == 27:  # q or ESC
        break

    prev_frame = blur

cap.release()
cv2.destroyAllWindows()