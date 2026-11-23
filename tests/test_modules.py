import unittest
import numpy as np
import os
import csv
import sys

# ============================================
# PATH SETUP
# ============================================

# tests/ is one level below project root
# so we go up one level to reach core/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)


# ============================================
# TEST: DETECT PROTOCOL
# ============================================

class TestDetectProtocol(unittest.TestCase):
    """
    Tests for detect_protocol() in core/stream_manager.py.

    Verifies that the function correctly identifies
    the streaming protocol from a given URL or source string.
    This is critical for correct folder organization
    in the frame extractor (frames/{PROTOCOL}/).
    """

    def setUp(self):
        from core.stream_manager import detect_protocol
        self.detect_protocol = detect_protocol

    def test_rtsp_detected(self):
        """RTSP URL must return 'RTSP'."""
        result = self.detect_protocol("rtsp://192.168.1.100/stream")
        self.assertEqual(result, "RTSP")

    def test_hls_detected(self):
        """HLS URL with .m3u8 must return 'HLS'."""
        result = self.detect_protocol("http://example.com/stream.m3u8")
        self.assertEqual(result, "HLS")

    def test_mp4_detected(self):
        """MP4 file path must return 'VIDEO'."""
        result = self.detect_protocol("videos/test_video.mp4")
        self.assertEqual(result, "VIDEO")

    def test_avi_detected(self):
        """AVI file path must return 'VIDEO'."""
        result = self.detect_protocol("videos/test_video.avi")
        self.assertEqual(result, "VIDEO")

    def test_mov_detected(self):
        """MOV file path must return 'VIDEO'."""
        result = self.detect_protocol("videos/test_video.mov")
        self.assertEqual(result, "VIDEO")

    def test_webcam_detected(self):
        """Source '0' (integer as string) must return 'WEBCAM'."""
        result = self.detect_protocol("0")
        self.assertEqual(result, "WEBCAM")

    def test_unknown_detected(self):
        """Unknown source must return 'UNKNOWN'."""
        result = self.detect_protocol("some_unknown_source")
        self.assertEqual(result, "UNKNOWN")

    def test_rtsp_case_insensitive(self):
        """Protocol detection must be case-insensitive."""
        result = self.detect_protocol("RTSP://192.168.1.100/stream")
        self.assertEqual(result, "RTSP")


# ============================================
# TEST: NORMALIZE FRAME
# ============================================

class TestNormalizeFrame(unittest.TestCase):
    """
    Tests for normalize_frame() in core/normalizer.py.

    Verifies that the normalization pipeline correctly
    transforms input frames to the target resolution
    and color space required by YOLOv8 (RGB, 640x360).
    """

    def setUp(self):
        from core.normalizer import normalize_frame
        self.normalize_frame = normalize_frame

    def test_output_resolution(self):
        """
        Output frame must have resolution TARGET_WIDTH x TARGET_HEIGHT.
        Default: 640 x 360 pixels.
        """
        fake_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = self.normalize_frame(fake_frame)
        self.assertEqual(result.shape[1], 640)  # width
        self.assertEqual(result.shape[0], 360)  # height

    def test_output_channels(self):
        """Output frame must have 3 color channels (RGB)."""
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = self.normalize_frame(fake_frame)
        self.assertEqual(result.shape[2], 3)

    def test_small_frame_upscaled(self):
        """Small frames must be upscaled to target resolution."""
        fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = self.normalize_frame(fake_frame)
        self.assertEqual(result.shape[:2], (360, 640))

    def test_output_dtype(self):
        """Output frame must preserve uint8 data type."""
        fake_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = self.normalize_frame(fake_frame)
        self.assertEqual(result.dtype, np.uint8)

    def test_bgr_to_rgb_conversion(self):
        """
        BGR->RGB conversion must swap red and blue channels.
        A pure blue BGR frame (B=255,G=0,R=0) becomes
        pure blue in RGB at channel index 2.
        """
        fake_frame = np.zeros((360, 640, 3), dtype=np.uint8)
        fake_frame[:, :, 0] = 255  # Blue channel in BGR

        result = self.normalize_frame(fake_frame)

        # After BGR->RGB: blue is now at channel index 2
        self.assertEqual(result[0, 0, 2], 255)
        self.assertEqual(result[0, 0, 0], 0)


# ============================================
# TEST: PERFORMANCE MODULE
# ============================================

class TestPerformance(unittest.TestCase):
    """
    Tests for update_performance() and print_report()
    in core/performance.py.

    Verifies correct aggregation of per-stream metrics
    used for the final performance report (CSV export).
    """

    def setUp(self):
        """Reset all global counters before each test."""
        import core.performance as performance
        self.perf = performance

        performance.total_frames = 0
        performance.total_detections = 0
        performance.fps_sum = 0
        performance.ai_time_sum = 0
        performance.ai_calls = 0
        performance.stream_stats = {}

    def test_update_creates_stream_entry(self):
        """update_performance() must create a new entry for unknown stream."""
        self.perf.update_performance("test_stream", 14.5, 68.0, 3)
        self.assertIn("test_stream", self.perf.stream_stats)

    def test_update_increments_frames(self):
        """Each call must increment frame count by 1."""
        self.perf.update_performance("test_stream", 14.5, 68.0, 3)
        self.perf.update_performance("test_stream", 13.0, 75.0, 2)
        self.assertEqual(self.perf.stream_stats["test_stream"]["frames"], 2)

    def test_update_accumulates_detections(self):
        """Total detections must be the sum of all calls."""
        self.perf.update_performance("test_stream", 14.5, 68.0, 3)
        self.perf.update_performance("test_stream", 13.0, 75.0, 5)
        self.assertEqual(
            self.perf.stream_stats["test_stream"]["detections"], 8
        )

    def test_global_total_frames(self):
        """Global total_frames must count all frames across all streams."""
        self.perf.update_performance("stream_a", 14.0, 70.0, 2)
        self.perf.update_performance("stream_b", 12.0, 80.0, 1)
        self.assertEqual(self.perf.total_frames, 2)

    def test_global_total_detections(self):
        """Global total_detections must sum across all streams."""
        self.perf.update_performance("stream_a", 14.0, 70.0, 2)
        self.perf.update_performance("stream_b", 12.0, 80.0, 3)
        self.assertEqual(self.perf.total_detections, 5)

    def test_multiple_streams_independent(self):
        """Each stream must track its own metrics independently."""
        self.perf.update_performance("stream_a", 14.0, 70.0, 2)
        self.perf.update_performance("stream_b", 12.0, 80.0, 5)
        self.assertEqual(
            self.perf.stream_stats["stream_a"]["detections"], 2
        )
        self.assertEqual(
            self.perf.stream_stats["stream_b"]["detections"], 5
        )

    def test_print_report_creates_csv(self):
        """print_report() must create logs/performance_report.csv."""
        self.perf.update_performance("test_stream", 14.5, 68.0, 3)
        self.perf.print_report()
        self.assertTrue(os.path.exists("logs/performance_report.csv"))

    def test_print_report_csv_has_header(self):
        """performance_report.csv must contain the correct header row."""
        self.perf.update_performance("test_stream", 14.5, 68.0, 3)
        self.perf.print_report()

        with open("logs/performance_report.csv", "r") as f:
            reader = csv.reader(f)
            header = next(reader)

        self.assertIn("Stream", header)
        self.assertIn("Avg FPS", header)
        self.assertIn("Avg AI", header)

    def test_zero_frames_no_division_error(self):
        """print_report() must not raise ZeroDivisionError when no data."""
        try:
            self.perf.print_report()
        except ZeroDivisionError:
            self.fail(
                "print_report() raised ZeroDivisionError with no data"
            )


# ============================================
# TEST: SETTINGS CONSTANTS
# ============================================

class TestSettings(unittest.TestCase):
    """
    Tests for constants in core/settings.py.

    Verifies that configuration values are within
    acceptable ranges for the AI processing pipeline.
    """

    def setUp(self):
        from core.settings import (
            TARGET_WIDTH,
            TARGET_HEIGHT,
            TARGET_FPS,
            SAVE_EVERY_N_FRAMES,
            DETECTION_FRAME_SKIP,
            YOLO_CLASSES
        )
        self.TARGET_WIDTH = TARGET_WIDTH
        self.TARGET_HEIGHT = TARGET_HEIGHT
        self.TARGET_FPS = TARGET_FPS
        self.SAVE_EVERY_N_FRAMES = SAVE_EVERY_N_FRAMES
        self.DETECTION_FRAME_SKIP = DETECTION_FRAME_SKIP
        self.YOLO_CLASSES = YOLO_CLASSES

    def test_target_resolution_positive(self):
        """TARGET_WIDTH and TARGET_HEIGHT must be positive integers."""
        self.assertGreater(self.TARGET_WIDTH, 0)
        self.assertGreater(self.TARGET_HEIGHT, 0)

    def test_target_fps_positive(self):
        """TARGET_FPS must be a positive integer."""
        self.assertGreater(self.TARGET_FPS, 0)

    def test_save_every_n_frames_positive(self):
        """SAVE_EVERY_N_FRAMES must be a positive integer."""
        self.assertGreater(self.SAVE_EVERY_N_FRAMES, 0)

    def test_detection_frame_skip_valid(self):
        """DETECTION_FRAME_SKIP must be >= 1."""
        self.assertGreaterEqual(self.DETECTION_FRAME_SKIP, 1)

    def test_yolo_classes_not_empty(self):
        """YOLO_CLASSES must contain at least one class."""
        self.assertGreater(len(self.YOLO_CLASSES), 0)

    def test_yolo_classes_contains_person(self):
        """YOLO_CLASSES must contain class 0 (person) for traffic domain."""
        self.assertIn(0, self.YOLO_CLASSES)

    def test_yolo_classes_contains_car(self):
        """YOLO_CLASSES must contain class 2 (car) for traffic domain."""
        self.assertIn(2, self.YOLO_CLASSES)

    def test_resolution_is_640x360(self):
        """Default resolution must be 640x360 as specified in design."""
        self.assertEqual(self.TARGET_WIDTH, 640)
        self.assertEqual(self.TARGET_HEIGHT, 360)


# ============================================
# TEST: REMOVE STREAM BY INDEX
# ============================================

class TestRemoveStream(unittest.TestCase):
    """
    Tests for remove_stream_by_index() in core/stream_manager.py.

    Verifies correct stream removal with valid and invalid indices,
    without requiring a real camera or video file.
    A FakeCap class simulates cv2.VideoCapture.release().
    """

    def setUp(self):
        import core.stream_manager as sm
        self.sm = sm
        self.sm.streams.clear()

    def _make_fake_stream(self, name):
        """Helper: create a fake stream dict without real VideoCapture."""

        class FakeCap:
            def release(self):
                pass

        return {
            "name": name,
            "cap": FakeCap(),
            "type": "video",
            "source": "fake.mp4",
            "frame_count": 0,
            "saved_frames": 0,
            "last_save_time": 0,
            "status": "online",
            "protocol": "VIDEO"
        }

    def test_remove_valid_index(self):
        """Removing stream at valid index must reduce list length by 1."""
        self.sm.streams.append(self._make_fake_stream("stream_a"))
        self.sm.streams.append(self._make_fake_stream("stream_b"))
        self.sm.remove_stream_by_index(0)
        self.assertEqual(len(self.sm.streams), 1)

    def test_remove_correct_stream(self):
        """After removal at index 0, remaining stream must be stream_b."""
        self.sm.streams.append(self._make_fake_stream("stream_a"))
        self.sm.streams.append(self._make_fake_stream("stream_b"))
        self.sm.remove_stream_by_index(0)
        self.assertEqual(self.sm.streams[0]["name"], "stream_b")

    def test_remove_invalid_index_negative(self):
        """Negative index must not raise exception or modify the list."""
        self.sm.streams.append(self._make_fake_stream("stream_a"))
        self.sm.remove_stream_by_index(-1)
        self.assertEqual(len(self.sm.streams), 1)

    def test_remove_invalid_index_too_large(self):
        """Index >= list length must not raise exception."""
        self.sm.streams.append(self._make_fake_stream("stream_a"))
        self.sm.remove_stream_by_index(99)
        self.assertEqual(len(self.sm.streams), 1)

    def test_remove_from_empty_list(self):
        """Removing from empty list must not raise any exception."""
        try:
            self.sm.remove_stream_by_index(0)
        except Exception as e:
            self.fail(
                f"remove_stream_by_index() raised {e} on empty list"
            )


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    unittest.main(verbosity=2)