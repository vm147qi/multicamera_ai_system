import time

from ultralytics import YOLO

# ============================================
# LOAD MODEL
# ============================================

model = YOLO("yolov8n.pt")

# ============================================
# DETECT OBJECTS
# ============================================

def detect_objects(frame):

    start_time = time.time()

    # ============================================
    # YOLO INFERENCE
    # ============================================

    results = model(
        frame,
        classes=[0, 1, 2, 3, 5, 7]
    )

    end_time = time.time()

    # ============================================
    # PERFORMANCE METRICS
    # ============================================

    inference_time = (end_time - start_time) * 1000

    fps = 1000 / inference_time if inference_time > 0 else 0

    # ============================================
    # ANNOTATED FRAME
    # ============================================

    annotated_frame = results[0].plot()

    # ============================================
    # DETECTION COUNT
    # ============================================

    detections = len(results[0].boxes)

    # ============================================
    # RETURN RESULTS
    # ============================================

    return (
        annotated_frame,
        fps,
        inference_time,
        detections
    )