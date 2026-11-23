import cv2

from core.settings import (
    TARGET_WIDTH,
    TARGET_HEIGHT
)

# ============================================
# NORMALIZE FRAME
# ============================================

def normalize_frame(frame):

    # ============================================
    # RESOLUTION NORMALIZATION
    # ============================================

    frame = cv2.resize(
        frame,
        (
            TARGET_WIDTH,
            TARGET_HEIGHT
        )
    )

    # ============================================
    # COLOR NORMALIZATION
    # ============================================

    frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    return frame