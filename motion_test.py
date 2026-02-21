import cv2
import numpy as np
import time

cap = cv2.VideoCapture(0)

prev_frame = None

cooldown_seconds = 1.0
last_spin_time = 0.0

while True:
    ret, frame = cap.read()
    if not ret:
        break
# convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (21, 21), 0)

    h, w = gray.shape

# Define a vertical region on right side
    roi = blur[:, int(w * 0.7):w]

    if prev_frame is None:
        prev_frame = blur
        continue

# Frame difference
    #diff = cv2.absdiff(prev_frame, blur)
    prev_roi = prev_frame[:, int(w * 0.7):w]
    diff = cv2.absdiff(prev_roi, roi)

# Threshold
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

# Count motion pixels
    motion_score = np.sum(thresh) / 255

    print("Motion Score:", motion_score)

    #if motion_score > 4000:
    #    print("SPIN TRIGGERED!")
    now = time.time()
    if motion_score > 4000 and (now - last_spin_time) > cooldown_seconds:
        last_spin_time = now
        print("SPIN!")
        print("SPIN!")
        print("SPIN!")

     # Draw green lever box
    cv2.rectangle(
        frame,
        (int(w * 0.7), 0),
        (w, h),
        (0, 255, 0),
        2
    )

    cv2.imshow("Motion", thresh)
    cv2.imshow("Camera", frame)

    prev_frame = blur

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()