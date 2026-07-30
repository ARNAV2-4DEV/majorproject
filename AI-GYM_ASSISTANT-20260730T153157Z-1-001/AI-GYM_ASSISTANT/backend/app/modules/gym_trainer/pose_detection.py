import math
import os
import urllib.request

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "pose_landmarker_lite.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)


def ensure_model_downloaded():
    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        print("Downloading pose landmark model (one-time, ~30MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")


class PoseLandmarkIndex:
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28


POSE_CONNECTIONS = [
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (24, 26),
    (26, 28),
]


def calculate_angle(a, b, c):
    """Angle (degrees, 0-180) at point b, formed by points a-b-c, each (x, y)."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(
        a[1] - b[1], a[0] - b[0]
    )
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle


def draw_landmarks(frame, landmarks, width, height):
    points = [(int(lm.x * width), int(lm.y * height)) for lm in landmarks]
    for a_idx, b_idx in POSE_CONNECTIONS:
        cv2.line(frame, points[a_idx], points[b_idx], (0, 255, 0), 2)
    for idx in set(sum(POSE_CONNECTIONS, ())):
        cv2.circle(frame, points[idx], 5, (0, 0, 255), -1)


class ExerciseConfig:
    EXERCISES = {
        "bicep_curl": {
            "type": "rep",
            "left_landmarks": (
                PoseLandmarkIndex.LEFT_SHOULDER,
                PoseLandmarkIndex.LEFT_ELBOW,
                PoseLandmarkIndex.LEFT_WRIST,
            ),
            "right_landmarks": (
                PoseLandmarkIndex.RIGHT_SHOULDER,
                PoseLandmarkIndex.RIGHT_ELBOW,
                PoseLandmarkIndex.RIGHT_WRIST,
            ),
            "start_angle": 165,
            "peak_angle": 60,
            "form_min": 25,
        },
        "squat": {
            "type": "rep",
            "left_landmarks": (
                PoseLandmarkIndex.LEFT_HIP,
                PoseLandmarkIndex.LEFT_KNEE,
                PoseLandmarkIndex.LEFT_ANKLE,
            ),
            "right_landmarks": (
                PoseLandmarkIndex.RIGHT_HIP,
                PoseLandmarkIndex.RIGHT_KNEE,
                PoseLandmarkIndex.RIGHT_ANKLE,
            ),
            "start_angle": 170,
            "peak_angle": 85,
            "form_min": 65,
        },
        "push_up": {
            "type": "rep",
            "left_landmarks": (
                PoseLandmarkIndex.LEFT_SHOULDER,
                PoseLandmarkIndex.LEFT_ELBOW,
                PoseLandmarkIndex.LEFT_WRIST,
            ),
            "right_landmarks": (
                PoseLandmarkIndex.RIGHT_SHOULDER,
                PoseLandmarkIndex.RIGHT_ELBOW,
                PoseLandmarkIndex.RIGHT_WRIST,
            ),
            "start_angle": 170,
            "peak_angle": 80,
            "form_min": 60,
        },
        "shoulder_press": {
            "type": "rep",
            "left_landmarks": (
                PoseLandmarkIndex.LEFT_SHOULDER,
                PoseLandmarkIndex.LEFT_ELBOW,
                PoseLandmarkIndex.LEFT_WRIST,
            ),
            "right_landmarks": (
                PoseLandmarkIndex.RIGHT_SHOULDER,
                PoseLandmarkIndex.RIGHT_ELBOW,
                PoseLandmarkIndex.RIGHT_WRIST,
            ),
            "start_angle": 90,
            "peak_angle": 160,
        },
        "lateral_raise": {
            "type": "rep",
            "left_landmarks": (
                PoseLandmarkIndex.LEFT_HIP,
                PoseLandmarkIndex.LEFT_SHOULDER,
                PoseLandmarkIndex.LEFT_ELBOW,
            ),
            "right_landmarks": (
                PoseLandmarkIndex.RIGHT_HIP,
                PoseLandmarkIndex.RIGHT_SHOULDER,
                PoseLandmarkIndex.RIGHT_ELBOW,
            ),
            "start_angle": 20,
            "peak_angle": 85,
        },
        "lunge": {
            "type": "rep",
            "left_landmarks": (
                PoseLandmarkIndex.LEFT_HIP,
                PoseLandmarkIndex.LEFT_KNEE,
                PoseLandmarkIndex.LEFT_ANKLE,
            ),
            "right_landmarks": (
                PoseLandmarkIndex.RIGHT_HIP,
                PoseLandmarkIndex.RIGHT_KNEE,
                PoseLandmarkIndex.RIGHT_ANKLE,
            ),
            "start_angle": 170,
            "peak_angle": 95,
            "form_min": 70,
        },
        "plank": {
            "type": "hold",
            "left_landmarks": (
                PoseLandmarkIndex.LEFT_SHOULDER,
                PoseLandmarkIndex.LEFT_HIP,
                PoseLandmarkIndex.LEFT_ANKLE,
            ),
            "right_landmarks": (
                PoseLandmarkIndex.RIGHT_SHOULDER,
                PoseLandmarkIndex.RIGHT_HIP,
                PoseLandmarkIndex.RIGHT_ANKLE,
            ),
            "hold_min": 155,
            "hold_max": 180,
        },
    }


class RepCounter:

    def __init__(self, exercise: str):
        if exercise not in ExerciseConfig.EXERCISES:
            raise ValueError(
                f"Unsupported exercise '{exercise}'. "
                f"Choose from {list(ExerciseConfig.EXERCISES.keys())}"
            )
        self.exercise = exercise
        self.config = ExerciseConfig.EXERCISES[exercise]
        self.type = self.config["type"]
        self.last_feedback = ""

        # Movement tracking
        self.previous_angle = None
        self.filtered_angle = None
        self.direction = None  # "up" or "down"
        self.min_angle_seen = 999
        self.max_angle_seen = -999
        self.rep_started = False

        # Calibration state
        self.max_angle = -999
        self.min_angle = 999
        self.calibration_frames = 0
        self.calibrated = False
        self.start_threshold = None
        self.end_threshold = None

        if self.type == "rep":
            self.inverted = (
                self.config["peak_angle"] > self.config["start_angle"]
            )
            self.stage = "up" if not self.inverted else "down"
            self.rep_count = 0
        else:  # "hold"
            self.hold_seconds = 0.0
            self._in_position = False
            self._last_timestamp_ms = None

    def update(self, landmarks, image_width, image_height, timestamp_ms=None):
        left_points = self.config["left_landmarks"]
        right_points = self.config["right_landmarks"]

        left_visibility = sum(
            landmarks[idx].visibility for idx in left_points
        ) / len(left_points)
        right_visibility = sum(
            landmarks[idx].visibility for idx in right_points
        ) / len(right_points)

        if right_visibility > left_visibility:
            p1_idx, p2_idx, p3_idx = right_points
            body_side = "right"
        else:
            p1_idx, p2_idx, p3_idx = left_points
            body_side = "left"

        p1 = landmarks[p1_idx]
        p2 = landmarks[p2_idx]
        p3 = landmarks[p3_idx]
        a = (p1.x * image_width, p1.y * image_height)
        b = (p2.x * image_width, p2.y * image_height)
        c = (p3.x * image_width, p3.y * image_height)
        raw_angle = calculate_angle(a, b, c)

        if max(left_visibility, right_visibility) < 0.60:
            return {
                "exercise": self.exercise,
                "type": self.type,
                "feedback": "Move fully into the camera",
                "rep_count": getattr(self, "rep_count", 0),
                "angle": None,
                "stage": (
                    getattr(self, "stage", None)
                    if self.type == "rep"
                    else None
                ),
            }

        # Apply Exponential Moving Average (EMA) smoothing
        if self.filtered_angle is None:
            self.filtered_angle = raw_angle
        else:
            self.filtered_angle = (
                0.7 * self.filtered_angle + 0.3 * raw_angle
            )

        angle = self.filtered_angle

        if self.type == "rep":
            result = self._update_rep(angle)
        else:
            result = self._update_hold(angle, timestamp_ms)

        result["body_side"] = body_side
        return result

    def _update_rep(self, angle):
        # First frame setup
        if self.previous_angle is None:
            self.previous_angle = angle

        # Track min/max angle reached during current repetition
        self.min_angle_seen = min(self.min_angle_seen, angle)
        self.max_angle_seen = max(self.max_angle_seen, angle)

        # Determine movement direction with a 2-degree deadband noise filter
        if angle < self.previous_angle - 2:
            current_direction = "down"
        elif angle > self.previous_angle + 2:
            current_direction = "up"
        else:
            current_direction = self.direction

        feedback = ""

        # Direction inflection point checks
        if self.direction == "down" and current_direction == "up":
            self.rep_started = True

        elif (
            self.direction == "up"
            and current_direction == "down"
            and self.rep_started
        ):
            movement_range = self.max_angle_seen - self.min_angle_seen

            # Minimum range of motion required for each exercise
            required = {
                "bicep_curl": 65,
                "push_up": 55,
                "squat": 70,
                "lunge": 65,
                "shoulder_press": 60,
                "lateral_raise": 45,
            }.get(self.exercise, 55)

            if movement_range > required:
                self.rep_count += 1
                feedback = "Good rep!"

            # Reset ranges for next repetition cycle
            self.min_angle_seen = angle
            self.max_angle_seen = angle
            self.rep_started = False

        self.direction = current_direction
        self.previous_angle = angle

        return {
            "exercise": self.exercise,
            "type": "rep",
            "angle": round(angle, 1),
            "rep_count": self.rep_count,
            "stage": current_direction,
            "feedback": feedback,
        }

    def _update_hold(self, angle, timestamp_ms):
        hold_min = self.config["hold_min"]
        hold_max = self.config["hold_max"]
        in_position = hold_min <= angle <= hold_max

        if timestamp_ms is not None:
            if (
                in_position
                and self._in_position
                and self._last_timestamp_ms is not None
            ):
                self.hold_seconds += (
                    timestamp_ms - self._last_timestamp_ms
                ) / 1000.0
            self._last_timestamp_ms = timestamp_ms
            self._in_position = in_position

        feedback = (
            "Great - hold that position!"
            if in_position
            else "Straighten your body - avoid sagging or piking your hips."
        )
        self.last_feedback = feedback

        return {
            "exercise": self.exercise,
            "type": "hold",
            "angle": round(angle, 1),
            "hold_seconds": round(self.hold_seconds, 1),
            "feedback": self.last_feedback,
        }


def create_pose_detector():
    ensure_model_downloaded()
    base_options = mp_tasks.BaseOptions(model_asset_path=MODEL_PATH)
    options = mp_vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.VIDEO,
        num_poses=1,
    )
    return mp_vision.PoseLandmarker.create_from_options(options)


def process_video(
    video_path: str, exercise: str, save_annotated_path: str = None
):
    """Processes a video file frame-by-frame, returns final result + per-frame log."""
    counter = RepCounter(exercise)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    writer = None
    if save_annotated_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            save_annotated_path, fourcc, fps, (width, height)
        )

    detector = create_pose_detector()
    frame_log = []
    frame_idx = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        timestamp_ms = int((frame_idx / fps) * 1000)

        result = detector.detect_for_video(mp_image, timestamp_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            frame_result = counter.update(
                landmarks, width, height, timestamp_ms
            )
            frame_log.append(frame_result)

            if writer:
                draw_landmarks(frame, landmarks, width, height)
                headline = (
                    f"Reps: {frame_result['rep_count']}"
                    if frame_result["type"] == "rep"
                    else f"Hold: {frame_result['hold_seconds']}s"
                )
                cv2.putText(
                    frame,
                    headline,
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 0),
                    3,
                )
                cv2.putText(
                    frame,
                    frame_result["feedback"],
                    (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )

        if writer:
            writer.write(frame)
        frame_idx += 1

    cap.release()
    if writer:
        writer.release()
    detector.close()

    summary = {
        "exercise": exercise,
        "frames_processed": len(frame_log),
        "frame_log": frame_log,
    }
    if frame_log:
        last = frame_log[-1]
        if last["type"] == "rep":
            summary["total_reps"] = last["rep_count"]
        else:
            summary["total_hold_seconds"] = last["hold_seconds"]
    return summary