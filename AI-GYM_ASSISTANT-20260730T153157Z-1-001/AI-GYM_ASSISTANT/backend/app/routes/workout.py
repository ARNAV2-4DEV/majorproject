import os
import shutil
import tempfile
import time
import uuid
import base64

import cv2
import numpy as np
from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException,
    WebSocket, WebSocketDisconnect, Depends,
)
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.modules.gym_trainer.pose_detection import (
    process_video,
    ExerciseConfig,
    RepCounter,
    create_pose_detector,
    mp,
)
from app.database import get_db
from app.models.workout_session import WorkoutSession
router = APIRouter(prefix="/workout", tags=["workout"])

OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "gym_ai_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.get("/exercises")
def list_exercises():
    """Return supported exercises for the frontend dropdown."""
    return {"exercises": list(ExerciseConfig.EXERCISES.keys())}


@router.post("/analyze")
async def analyze_workout(
    exercise: str = Form(...),
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a workout video + exercise name.
    Returns rep count, final form feedback, and a link to the annotated video.
    Also saves this session to the database (see /workout/history).
    """
    if exercise not in ExerciseConfig.EXERCISES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported exercise '{exercise}'. Choose from {list(ExerciseConfig.EXERCISES.keys())}",
        )

    session_id = str(uuid.uuid4())
    input_path = os.path.join(OUTPUT_DIR, f"{session_id}_input.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{session_id}_annotated.mp4")

    with open(input_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    try:
        result = process_video(input_path, exercise, save_annotated_path=output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        os.remove(input_path)

    # Persist this session - this is what makes Habit Tracker and
    # Performance Analyzer possible later, instead of them working off
    # nothing every time the server restarts.
    db_session = WorkoutSession(
        exercise=exercise,
        session_type=result.get("frame_log", [{}])[-1].get("type", "rep") if result.get("frame_log") else "rep",
        total_reps=result.get("total_reps"),
        total_hold_seconds=result.get("total_hold_seconds"),
    )
    db.add(db_session)
    db.commit()

    result["annotated_video_id"] = session_id
    return result

@router.get("/history")
def get_workout_history(limit: int = 50, db: Session = Depends(get_db)):
    """Returns past workout sessions, most recent first. Used by the Habit
    Tracker and Performance Analyzer (Phases 3 and 5) and eventually the
    frontend dashboard to show real history."""
    sessions = (
        db.query(WorkoutSession)
        .order_by(WorkoutSession.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "exercise": s.exercise,
                "session_type": s.session_type,
                "total_reps": s.total_reps,
                "total_hold_seconds": s.total_hold_seconds,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
    }
@router.get("/result-video/{session_id}")
async def get_annotated_video(session_id: str):
    from fastapi.responses import FileResponse

    path = os.path.join(OUTPUT_DIR, f"{session_id}_annotated.mp4")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(path, media_type="video/mp4")


@router.websocket("/live")
async def live_workout(websocket: WebSocket):
    """Protocol:

    1. Client connects, then sends one JSON message: {"exercise": "bicep_curl"}
    2. Client then sends a stream of text messages, each a base64-encoded
       JPEG frame (data URL format from canvas.toDataURL()).
    3. Server responds to each frame with a JSON rep-count update.
    """
    await websocket.accept()

    init_msg = await websocket.receive_json()
    exercise = init_msg.get("exercise", "bicep_curl")

    try:
        counter = RepCounter(exercise)
    except ValueError as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
        return

    detector = create_pose_detector()
    start_time = time.time()

    try:
        while True:
            data = await websocket.receive_text()
            # Strip the "data:image/jpeg;base64," prefix if present
            if "," in data:
                data = data.split(",", 1)[1]

            img_bytes = base64.b64decode(data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            height, width = frame.shape[:2]
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=image_rgb
            )
            timestamp_ms = int((time.time() - start_time) * 1000)

            result = detector.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                frame_result = counter.update(
                    landmarks, width, height, timestamp_ms
                )
                await websocket.send_json(frame_result)
            else:
                await websocket.send_json(
                    {
                        "feedback": "No person detected - step into frame",
                        "rep_count": getattr(counter, "rep_count", 0),
                        "angle": None,
                        "stage": None,
                    }
                )

    except WebSocketDisconnect:
        pass
    finally:
        detector.close()


@router.get("/live-test", response_class=HTMLResponse)
async def live_test_page():
    options = "".join(
        [
            f'<option value="{exercise}">{exercise.replace("_", " ").title()}</option>'
            for exercise in ExerciseConfig.EXERCISES.keys()
        ]
    )

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>AI Gym Trainer - Live Test</title>
</head>
<body style="font-family: sans-serif; text-align:center; background:#111; color:#eee;">
    <h2>Live Rep Counter Test</h2>
    <select id="exercise">
        {options}
    </select>
    <button onclick="start()">Start Camera</button>
    <br><br>
    <video id="video" width="480" height="360" autoplay muted style="border:2px solid #555;"></video>
    <canvas id="canvas" width="480" height="360" style="display:none;"></canvas>
    <h1 id="reps">Reps: 0</h1>
    <p id="feedback">Waiting...</p>
    <p id="angle"></p>

    <script>
        let ws;
        let frameSender = null;
        let stream = null;

        async function start() {{
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const exercise = document.getElementById('exercise').value;

            // Reset UI
            document.getElementById("reps").innerText = "Reps: 0";
            document.getElementById("feedback").innerText = "Calibrating...";
            document.getElementById("angle").innerText = "";

            // Close previous websocket
            if (ws) {{
                ws.close();
            }}

            // Stop previous timer
            if (frameSender) {{
                clearInterval(frameSender);
            }}

            // Stop previous camera
            if (stream) {{
                stream.getTracks().forEach(track => track.stop());
            }}

            stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
            video.srcObject = stream;

            ws = new WebSocket("ws://" + window.location.host + "/workout/live");

            ws.onopen = () => {{
                ws.send(JSON.stringify({{ exercise: exercise }}));
                frameSender = setInterval(() => {{
                    if (ws.readyState !== WebSocket.OPEN) return;

                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const dataUrl = canvas.toDataURL("image/jpeg", 0.6);
                    ws.send(dataUrl);
                }}, 100);
            }};

            ws.onmessage = (event) => {{
                const data = JSON.parse(event.data);
                document.getElementById('reps').innerText = "Reps: " + (data.rep_count ?? 0);
                document.getElementById("feedback").innerText = data.feedback + (data.stage ? " | " + data.stage : "");
                document.getElementById('angle').innerText = data.angle ? ("Angle: " + data.angle) : "";
            }};

            ws.onerror = (e) => console.error("WebSocket error:", e);
        }}
    </script>
</body>
</html>"""