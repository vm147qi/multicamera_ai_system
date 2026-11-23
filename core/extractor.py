import cv2
import os
import time
import csv

# ============================================
# CREATE OUTPUT DIRECTORY
# ============================================

os.makedirs("frames", exist_ok=True)

os.makedirs("logs", exist_ok=True)

# ============================================
# CSV FILE
# ============================================

CSV_FILE = "logs/metadata.csv"

# ============================================
# CREATE CSV HEADER
# ============================================

if not os.path.exists(CSV_FILE):

    with open(CSV_FILE, "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "timestamp",
            "stream_name",
            "protocol",
            "detections",
            "fps",
            "inference_time_ms"
        ])

# ============================================
# SAVE FRAME
# ============================================

def save_frame(
    frame,
    stream_name,
    protocol,
    detections,
    fps,
    inference_time
):

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # ============================================
    # SAFE STREAM NAME
    # ============================================

    safe_name = (
        stream_name
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "_")
    )

    # ============================================
    # PROTOCOL FOLDER
    # ============================================

    protocol_folder = f"frames/{protocol}"

    os.makedirs(protocol_folder, exist_ok=True)

    # ============================================
    # IMAGE FILE NAME
    # ============================================

    filename = (
        f"{protocol_folder}/"
        f"{safe_name}_"
        f"{timestamp}_"
        f"obj{detections}.jpg"
    )

    # ============================================
    # SAVE IMAGE
    # ============================================

    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite(filename, frame_bgr)

    # ============================================
    # SAVE CSV METADATA
    # ============================================

    with open(CSV_FILE, "a", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            timestamp,
            stream_name,
            protocol,
            detections,
            round(fps, 1),
            round(inference_time, 1)
        ])