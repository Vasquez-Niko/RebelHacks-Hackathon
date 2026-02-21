import cv2
import numpy as np
import time

# ---- Camera ----
# If you needed DirectShow earlier, keep CAP_DSHOW:
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    raise RuntimeError("Cannot open camera")

# ---- Motion detection state ----
prev_frame = None

# ---- Slot machine state ----
symbols = ["CHERRY", "DIAMOND", "7", "LEMON", "BELL"]
#symbols = ["🍒", "💎", "7", "🍋", "🔔"]
reels = ["?", "?", "?"]
final_reels = ["?", "?", "?"]

money = 100
result_text = "PULL TO SPIN"
result_until = 0.0  # show the last win/loss until this time
bet = 5

cooldown_seconds = 1.0
last_spin_time = 0.0

spin_duration = 1.2
spinning_until = 0.0
was_spinning = False

result_text = "PULL TO SPIN"
result_until = 0.0

# Tune these:
ROI_START = 0.7         # right 30% of screen is "lever zone"
MOTION_THRESHOLD = 4000 # you already found this ballpark

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (21, 21), 0)

    h, w = gray.shape
    x0 = int(w * ROI_START)

    # Define ROI (lever zone)
    roi = blur[:, x0:w]

    if prev_frame is None:
        prev_frame = blur
        continue

    prev_roi = prev_frame[:, x0:w]

    diff = cv2.absdiff(prev_roi, roi)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    motion_score = np.sum(thresh) / 255.0

    now = time.time()

    # Trigger spin (cooldown + threshold)
    if motion_score > MOTION_THRESHOLD and (now - last_spin_time) > cooldown_seconds and now >= spinning_until:
        last_spin_time = now
        spinning_until = now + spin_duration
        final_reels = list(np.random.choice(symbols, size=3))

    # Spin animation: randomize reels while spinning
    is_spinning = now < spinning_until
#   if is_spinning:
#       reels = list(np.random.choice(symbols, size=3))
    if is_spinning:
        display_reels = ["|", "|", "|"]  # spinning animation placeholder
    else:
        display_reels = final_reels

    # Score when spin ends (transition spinning -> not spinning)

    # --- result message timer (add these vars once near the top too; see next section)
# result_text = "PULL TO SPIN"
# result_until = 0.0

    # Score ONLY when spin ends (transition True -> False)
    if was_spinning and not is_spinning:
        if final_reels[0] == final_reels[1] == final_reels[2]:
            money += 50
            result_text = "JACKPOT +$50"
        elif len(set(final_reels)) == 2:
            money += 10
            result_text = "NICE +$10"
        else:
            money -= 5
            result_text = "LOSE -$5"

    result_until = now + 2.0  # keep message visible for 2 seconds

# choose what status to display
    if is_spinning:
        status_text = "SPINNING..."
    else:
        status_text = result_text if now < result_until else "PULL TO SPIN"

        was_spinning = is_spinning

    # ---- UI overlay ----
    # Lever zone box
    cv2.rectangle(frame, (x0, 0), (w, h), (0, 255, 0), 2)
    cv2.putText(frame, "LEVER ZONE", (x0 + 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Reels display
    cv2.putText(frame, f"{display_reels[0]} | {display_reels[1]} | {display_reels[2]}",
                (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

    # Money + status
    cv2.putText(frame, f"MONEY: ${money}", (30, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
    cv2.putText(frame, result_text, (30, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

    # Optional: show motion score for tuning
    cv2.putText(frame, f"motion: {int(motion_score)}", (30, 260),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow("Vegas Slot Machine", frame)
    # If you want to see the threshold mask too:
    # cv2.imshow("Motion Mask", thresh)

    key = cv2.waitKey(10) & 0xFF
    if key == ord('q') or key == 27:  # q or ESC
        break

    prev_frame = blur

cap.release()
cv2.destroyAllWindows()