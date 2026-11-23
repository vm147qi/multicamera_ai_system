import cv2

# ============================================
# STREAM STORAGE
# ============================================

streams = []

# ============================================
# ADD VIDEO
# ============================================

def add_video_stream(filepath):

    cap = cv2.VideoCapture(filepath)

    if not cap.isOpened():

        print("ERROR: Cannot open video")

        return

    streams.append({
        "name": filepath.split("/")[-1],
        "cap": cap,
        "type": "video",
        "source": filepath,
        "frame_count": 0,
        "saved_frames": 0,
        "last_save_time": 0,
        "status": "online",
        "protocol": detect_protocol(filepath)
    })

    print("Video added")

# ============================================
# ADD WEBCAM
# ============================================

def add_webcam_stream():

    for stream in streams:

        if stream["name"] == "Laptop Camera":

            print("Laptop camera already connected")

            return

    cap = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():

        print("ERROR: Cannot open webcam")

        return

    streams.append({
        "name": "Laptop Camera",
        "cap": cap,
        "type": "webcam",
        "source": 0,
        "frame_count": 0,
        "saved_frames": 0,
        "last_save_time": 0,
        "status": "online",
        "protocol": "WEBCAM"
    })

    print("Webcam connected")

# ============================================
# ADD RTSP/HLS STREAM
# ============================================

def add_rtsp_stream(stream_url):

    for stream in streams:

        if stream["source"] == stream_url:

            print("Stream already connected")

            return

    cap = cv2.VideoCapture(stream_url)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 20)

    if not cap.isOpened():

        print("ERROR: Cannot open stream")

        return

    # ============================================
    # STREAM NAME
    # ============================================

    if "192.168" in stream_url:

        stream_name = "phone_camera"

    elif "kukaj" in stream_url:

        stream_name = "public_camera"

    elif ".m3u8" in stream_url:

        stream_name = "hls_stream"

    else:

        stream_name = "rtsp_stream"

    streams.append({

        "name": stream_name,
        "cap": cap,
        "type": "rtsp",
        "source": stream_url,
        "frame_count": 0,
        "saved_frames": 0,
        "last_save_time": 0,
        "status": "online",
        "protocol": detect_protocol(stream_url)
    })

    print(f"{stream_name} connected")

# ============================================
# REMOVE STREAM
# ============================================

def remove_stream_by_index(index):

    if index < 0 or index >= len(streams):

        print("Invalid stream index")

        return

    stream = streams.pop(index)

    stream["cap"].release()

    print(f"Removed: {stream['name']}")

# ============================================
# RECONNECT STREAM
# ============================================

def reconnect_stream(stream):

    print(f"Reconnecting: {stream['name']}")


    stream["cap"].release()

    new_cap = cv2.VideoCapture(
        stream["source"]
    )


    if new_cap.isOpened():

        stream["cap"] = new_cap

        stream["status"] = "online"

        print("Reconnect successful")

    else:

        stream["status"] = "offline"

        print("Reconnect failed")

# ============================================
# DETECT STREAM PROTOCOL
# ============================================

def detect_protocol(source):

    source = str(source).lower()

    # ============================================
    # RTSP
    # ============================================

    if source.startswith("rtsp://"):

        return "RTSP"

    # ============================================
    # HLS
    # ============================================

    elif ".m3u8" in source:

        return "HLS"

    # ============================================
    # VIDEO FILE
    # ============================================

    elif source.endswith((".mp4", ".avi", ".mov")):

        return "VIDEO"

    # ============================================
    # WEBCAM
    # ============================================

    elif source == "0":

        return "WEBCAM"

    # ============================================
    # UNKNOWN
    # ============================================

    return "UNKNOWN"