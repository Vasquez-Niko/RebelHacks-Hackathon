# RebelHacks-Hackathon
Hackathon entry for RebelHacks 2026 at UNLV.

🎰 Vision-Based Slot Machine

This project implements a real-time gesture-controlled slot machine using classical computer vision techniques.

How It Works::

-The right 30% of the frame acts as a lever zone

-Motion is detected using frame differencing + thresholding

-A centroid of motion pixels is computed

-A finite state machine enforces:

-Motion MUST begin in the top 35%

-Then move downward past the 70% line,

-Within a 0.7 second timeout

-only valid top-to-bottom pulls trigger a spin

Key Parameters:
ROI_START = 0.7
MOTION_THRESHOLD = 25000

TOP_FRAC = 0.35
BOTTOM_FRAC = 0.70
MIN_MOTION_PIXELS = 1000
PULL_TIMEOUT = 0.7

Features:

Edge-triggered spin detection

Time-based spin animation

Deterministic payout evaluation

Cooldown system to prevent retriggers

On-screen debugging overlays (state + motion)

RUN:

pip install opencv-python numpy
python vegas_slot.py

Press q to quit.
