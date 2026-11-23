import csv
import os

# ============================================
# PERFORMANCE STORAGE
# ============================================

total_frames = 0

total_detections = 0

fps_sum = 0

ai_time_sum = 0

ai_calls = 0

# ============================================
# STREAM PERFORMANCE STORAGE
# ============================================

stream_stats = {}

# ============================================
# UPDATE PERFORMANCE
# ============================================

def update_performance(
    stream_name,
    fps,
    inference_time,
    detections
):

    global total_frames
    global total_detections
    global fps_sum
    global ai_time_sum
    global ai_calls

    total_frames += 1

    total_detections += detections

    fps_sum += fps

    ai_time_sum += inference_time

    ai_calls += 1

    # ============================================
    # CREATE STREAM STATS
    # ============================================

    if stream_name not in stream_stats:

        stream_stats[stream_name] = {

            "frames": 0,
            "detections": 0,
            "saved_frames": 0,
            "fps_sum": 0,
            "ai_sum": 0
        }

    # ============================================
    # UPDATE STREAM STATS
    # ============================================

    stream_stats[stream_name]["frames"] += 1

    stream_stats[stream_name]["detections"] += detections

    stream_stats[stream_name]["fps_sum"] += fps

    stream_stats[stream_name]["ai_sum"] += inference_time

# ============================================
# PRINT REPORT
# ============================================

def print_report():

    average_fps = (
        fps_sum / ai_calls
        if ai_calls > 0 else 0
    )

    average_ai = (
        ai_time_sum / ai_calls
        if ai_calls > 0 else 0
    )

    # ============================================
    # AVERAGE DETECTIONS PER FRAME
    # ============================================

    average_detections = (
        total_detections / total_frames
        if total_frames > 0 else 0
    )

    print("\n==============================")
    print(" PERFORMANCE REPORT ")
    print("==============================")

    print(f"Total Frames: {total_frames}")

    print(f"Detected Objects (All Frames): {total_detections}")

    print(f"Average FPS: {average_fps:.1f}")

    print(f"Average AI Latency: {average_ai:.1f} ms")

    print(
        f"Average Detections per Frame: "
        f"{average_detections:.2f}"
    )

    print("==============================")

    # ============================================
    # CREATE LOGS DIRECTORY
    # ============================================

    os.makedirs("logs", exist_ok=True)

    # ============================================
    # SAVE PERFORMANCE CSV
    # ============================================

    with open(
        "logs/performance_report.csv",
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Stream",
            "Total Frames",
            "Detected Objects (All Frames)",
            "Saved Frames",
            "Avg FPS",
            "Avg AI",
            "Avg Detections per Frame"
        ])

        for stream_name, stats in stream_stats.items():

            avg_fps = (
                stats["fps_sum"] / stats["frames"]
            )

            avg_ai = (
                stats["ai_sum"] / stats["frames"]
            )

            average_detections = (
                stats["detections"] / stats["frames"]
                if stats["frames"] > 0 else 0
            )

            writer.writerow([

                stream_name,

                stats["frames"],

                stats["detections"],

                stats["saved_frames"],

                round(avg_fps, 1),

                round(avg_ai, 1),

                round(average_detections, 2)
            ])