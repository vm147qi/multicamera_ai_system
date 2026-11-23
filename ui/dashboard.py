import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog

import cv2
import numpy as np
import time

from PIL import Image, ImageTk
from core.extractor import save_frame
from core.detector import detect_objects
from core.normalizer import normalize_frame
from core.performance import stream_stats
from core.stream_manager import (
    streams,
    add_video_stream,
    add_webcam_stream,
    add_rtsp_stream,
    remove_stream_by_index,
    reconnect_stream
)

from core.settings import (
    DETECTION_FRAME_SKIP,
    PANEL_WIDTH,
    PANEL_HEIGHT,
    HEADER_HEIGHT,
    SAVE_EVERY_N_FRAMES,
    TARGET_FPS
)

from core.performance import (
    update_performance,
    print_report
)

# ============================================
# REQUIRED STREAMS TO START RECORDING
# ============================================

REQUIRED_STREAMS = 4

# ============================================
# FRAME STORAGE
# ============================================

frame_counter = 0

last_results = {}

# ============================================
# ADD VIDEO
# ============================================

def add_video():

    filepath = filedialog.askopenfilename(
        filetypes=[("Video files", "*.mp4 *.avi")]
    )

    if filepath:

        add_video_stream(filepath)

# ============================================
# ADD WEBCAM
# ============================================

def add_webcam():

    add_webcam_stream()

# ============================================
# ADD STREAM
# ============================================
    
def add_rtsp():

    stream_url = simpledialog.askstring(
        "Add Stream",
        "Enter HLS / RTSP URL:"
    )

    if stream_url:

        add_rtsp_stream(stream_url)

# ============================================
# REMOVE STREAM
# ============================================

def remove_stream():

    if len(streams) == 0:

        print("No streams to remove")

        return

    stream_list = ""

    for i, stream in enumerate(streams):

        stream_list += f"{i}: {stream['name']}\n"

    stream_index = simpledialog.askinteger(
        "Remove Stream",
        f"Select stream index:\n\n{stream_list}"
    )

    if stream_index is not None:

        remove_stream_by_index(stream_index)

# ============================================
# UPDATE STREAMS
# ============================================

def update_streams(video_label, root):

    global frame_counter

    frame_counter += 1

    if len(streams) == 0:

        empty = np.zeros((720, 1280, 3), dtype=np.uint8)

        text = "NO ACTIVE STREAMS"

        font = cv2.FONT_HERSHEY_SIMPLEX

        font_scale = 2

        thickness = 4

        text_size = cv2.getTextSize(
            text,
            font,
            font_scale,
            thickness
        )[0]

        text_x = (empty.shape[1] - text_size[0]) // 2

        text_y = (empty.shape[0] + text_size[1]) // 2

        cv2.putText(
            empty,
            text,
            (text_x, text_y),
            font,
            font_scale,
            (0, 255, 0),
            thickness
        )
        rgb = cv2.cvtColor(empty, cv2.COLOR_BGR2RGB)

        img = Image.fromarray(rgb)

        imgtk = ImageTk.PhotoImage(image=img)

        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        root.after(30, update_streams, video_label, root)

        return

    frames = []

    active_streams = []

    total_detections = 0

    # ============================================
    # PROCESS STREAMS
    # ============================================

    for index, stream in enumerate(streams):

        stream_name = stream["name"]

        cap = stream["cap"]

        ret, frame = cap.read()

        # ============================================
        # STREAM ERROR
        # ============================================

        if not ret:

            print(f"Stream disconnected: {stream_name}")

            stream["status"] = "offline"

            reconnect_stream(stream)

            continue

        # ============================================
        # EMPTY FRAME
        # ============================================

        if frame is None:

            print(f"Empty frame: {stream_name}")

            continue

        # ============================================
        # FRAME COUNTER
        # ============================================

        stream["frame_count"] += 1

        # ============================================
        # FPS NORMALIZATION
        # ============================================

        source_fps = cap.get(cv2.CAP_PROP_FPS)

        if source_fps <= 0:

            source_fps = 30

        frame_interval = int(source_fps / TARGET_FPS)

        if frame_interval < 1:

            frame_interval = 1

        # ============================================
        # REMOVE FINISHED VIDEO
        # ============================================

        if not ret:

            cap.release()

            continue

        # ============================================
        # NORMALIZATION
        # ============================================

        frame = normalize_frame(frame)

        # ============================================
        # AI DETECTION
        # ============================================

        if (
            frame_counter % DETECTION_FRAME_SKIP == 0
            and stream["frame_count"] % frame_interval == 0
        ):

            frame, fps, inference_time, detections = detect_objects(frame)

            if len(streams) >= REQUIRED_STREAMS:
                update_performance(
                stream_name,
                fps,
                inference_time,
                detections
            )

            last_results[stream_name] = {

                "frame": frame.copy(),

                "fps": fps,

                "inference_time": inference_time,

                "detections": detections
            }

        else:

            if stream_name in last_results:

                frame = last_results[stream_name]["frame"].copy()

                fps = last_results[stream_name]["fps"]

                inference_time = last_results[stream_name]["inference_time"]

                detections = last_results[stream_name]["detections"]

            else:

                fps = 0

                inference_time = 0

                detections = 0

        # ============================================
        # TOTAL DETECTIONS
        # ============================================

        total_detections += detections

        # ============================================
        # SAVE FRAME EVERY 30 FRAMES
        # ============================================

        current_time = time.time()

        if (
            stream["frame_count"] % SAVE_EVERY_N_FRAMES == 0
            and detections > 0
            and len(streams) >= REQUIRED_STREAMS
        ):

            save_frame(
                frame,
                stream_name.replace("/", "_"),
                stream["protocol"],
                detections,
                fps,
                inference_time
            )

            stream["saved_frames"] += 1

            stream_stats[stream_name]["saved_frames"] += 1

            stream["last_save_time"] = current_time

        # ============================================
        # PANEL POSITION
        # ============================================

        panel_y = 0

        if index < 2:

            panel_y = HEADER_HEIGHT


        # ============================================
        # DARK PANEL
        # ============================================

        cv2.rectangle(
            frame,
            (0, panel_y),
            (PANEL_WIDTH, PANEL_HEIGHT + panel_y),
            (20, 20, 20),
            -1
        )

        # ============================================
        # STREAM INFO
        # ============================================

        cv2.putText(
            frame,
            stream["name"],
            (15, 30 + panel_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (15, 65 + panel_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"AI: {inference_time:.1f} ms",
            (15, 100 + panel_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Objects: {detections}",
            (15, 135 + panel_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 100, 255),
            2
        )

        cv2.putText(
            frame,
            f"Protocol: {stream['protocol']}",
            (15, 205 + panel_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 180, 0),
            2
        )

        cv2.putText(
            frame,
            f"Saved: {stream['saved_frames']}",
            (15, 240 + panel_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 120),
            2
        )

        cv2.putText(
            frame,
            f"Status: {stream['status'].upper()}",
            (15, 170 + panel_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 200, 255),
            2
        )

        frames.append(frame)

        active_streams.append(stream)

    streams.clear()

    streams.extend(active_streams)

    # ============================================
    # NO VALID FRAMES
    # ============================================

    if len(frames) == 0:

        root.after(30, update_streams, video_label, root)

        return

    # ============================================
    # GRID LAYOUT
    # ============================================

    if len(frames) == 1:

        combined = frames[0]

    elif len(frames) == 2:

        combined = cv2.hconcat(frames)

    else:

        rows = []

        for i in range(0, len(frames), 2):

            if i + 1 < len(frames):

                row = cv2.hconcat([frames[i], frames[i + 1]])

            else:

                black = np.zeros((360, 640, 3), dtype=np.uint8)

                row = cv2.hconcat([frames[i], black])

            rows.append(row)

        combined = cv2.vconcat(rows)

    # ============================================
    # DASHBOARD HEADER
    # ============================================

    cv2.rectangle(
        combined,
        (0, 0),
        (combined.shape[1], 40),
        (9, 9, 9),
        -1
    )

    cv2.putText(
        combined,
        f"VisionFlow AI | Streams: {len(streams)} | Total Objects: {total_detections}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 240, 0),
        2
    )

    # ============================================
    # CONVERT TO TKINTER
    # ============================================

    img = Image.fromarray(combined)

    imgtk = ImageTk.PhotoImage(image=img)

    video_label.imgtk = imgtk

    video_label.configure(image=imgtk)

    root.after(15, update_streams, video_label, root)

# ============================================
# DASHBOARD WINDOW
# ============================================

def run_dashboard():

    root = tk.Tk()

    root.title("VisionFlow AI")

    root.state("zoomed")

    root.configure(bg="#111111")

    # ============================================
    # TOP MENU
    # ============================================

    top_frame = tk.Frame(root, bg="#111111")

    top_frame.pack(fill="x", pady=10)

    # ============================================
    # ADD VIDEO BUTTON
    # ============================================

    add_video_button = tk.Button(
        top_frame,
        text="ADD VIDEO",
        font=("Arial", 14, "bold"),
        bg="#007ACC",
        fg="white",
        padx=20,
        pady=10,
        borderwidth=0,
        command=add_video
    )

    add_video_button.pack(side="left", padx=10)

    # ============================================
    # ADD WEBCAM BUTTON
    # ============================================

    add_webcam_button = tk.Button(
        top_frame,
        text="ADD WEBCAM",
        font=("Arial", 14, "bold"),
        bg="#00AA00",
        fg="white",
        padx=20,
        pady=10,
        borderwidth=0,
        command=add_webcam
    )

    add_webcam_button.pack(side="left", padx=10)

    # ============================================
    # ADD RTSP BUTTON
    # ============================================

    add_rtsp_button = tk.Button(
        top_frame,
        text="ADD STREAM",
        font=("Arial", 14, "bold"),
        bg="#AA5500",
        fg="white",
        padx=20,
        pady=10,
        borderwidth=0,
        command=add_rtsp
    )

    add_rtsp_button.pack(side="left", padx=10)

    # ============================================
    # REMOVE STREAM BUTTON
    # ============================================

    remove_stream_button = tk.Button(
        top_frame,
        text="REMOVE STREAM",
        font=("Arial", 14, "bold"),
        bg="#AA0000",
        fg="white",
        padx=20,
        pady=10,
        borderwidth=0,
        command=remove_stream
    )

    remove_stream_button.pack(side="left", padx=10)

    # ============================================
    # VIDEO PANEL
    # ============================================

    video_label = tk.Label(root, bg="black")

    video_label.pack(expand=True)

    # ============================================
    # START LOOP
    # ============================================

    update_streams(video_label, root)

    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: (
            print_report(),
            root.destroy()
        )
    )

    root.mainloop()