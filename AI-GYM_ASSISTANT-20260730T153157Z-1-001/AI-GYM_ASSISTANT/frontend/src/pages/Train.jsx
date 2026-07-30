import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import './Train.css';

export default function Train() {
  const [exercises, setExercises] = useState([]);
  const [exercise, setExercise] = useState('bicep_curl');
  const [mode, setMode] = useState('live'); // 'live' or 'upload'

  const [connected, setConnected] = useState(false);
  const [liveResult, setLiveResult] = useState(null);
  const [liveError, setLiveError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  const streamRef = useRef(null);

  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api
      .getExercises()
      .then((data) => setExercises(data.exercises || []))
      .catch(() => setExercises(['bicep_curl', 'squat']));
  }, []);

  useEffect(() => {
    return () => stopLiveSession();
  }, []);

  const handleModeChange = (newMode) => {
    if (newMode !== 'live' && connected) {
      stopLiveSession();
    }
    setMode(newMode);
  };

  async function startLiveSession() {
    setLiveError(null);
    setLiveResult(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const ws = new WebSocket(`${api.wsBase}/workout/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        ws.send(JSON.stringify({ exercise }));

        intervalRef.current = setInterval(() => {
          if (ws.readyState !== WebSocket.OPEN) return;
          const canvas = canvasRef.current;
          if (!canvas || !videoRef.current) return;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
          ws.send(canvas.toDataURL('image/jpeg', 0.6));
        }, 200);
      };

      ws.onmessage = (event) => {
        setLiveResult(JSON.parse(event.data));
      };

      ws.onerror = () => {
        setLiveError('Connection to the live tracker failed. Is the backend running?');
      };

      ws.onclose = () => setConnected(false);
    } catch (err) {
      setLiveError(err.message || 'Could not access the camera.');
    }
  }

  function stopLiveSession() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setConnected(false);
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const result = await api.analyzeWorkout(exercise, file);
      setUploadResult(result);
    } catch (err) {
      setUploadError(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="container train-page">
      <p className="eyebrow">Vision</p>
      <h1 className="train-page__title">Train</h1>
      <p className="train-page__sub">
        Pick an exercise, then either track it live on camera or upload a
        recorded clip.
      </p>

      <div className="train-page__controls">
        <label className="field-label" htmlFor="exercise-select">
          Exercise
        </label>
        <select
          id="exercise-select"
          value={exercise}
          onChange={(e) => setExercise(e.target.value)}
          disabled={connected}
        >
          {exercises.map((ex) => (
            <option key={ex} value={ex}>
              {ex.replaceAll('_', ' ')}
            </option>
          ))}
        </select>

        <div className="mode-toggle">
          <button
            type="button"
            className={mode === 'live' ? 'mode-toggle__btn mode-toggle__btn--active' : 'mode-toggle__btn'}
            onClick={() => handleModeChange('live')}
          >
            Live camera
          </button>
          <button
            type="button"
            className={mode === 'upload' ? 'mode-toggle__btn mode-toggle__btn--active' : 'mode-toggle__btn'}
            onClick={() => handleModeChange('upload')}
          >
            Upload video
          </button>
        </div>
      </div>

      {mode === 'live' && (
        <div className="live-panel">
          <div className="live-panel__video-wrap">
            <video ref={videoRef} className="live-panel__video" muted playsInline />
            <canvas ref={canvasRef} width="480" height="360" style={{ display: 'none' }} />
          </div>

          <div className="live-panel__side">
            {!connected ? (
              <button type="button" className="btn btn-primary" onClick={startLiveSession}>
                Start camera
              </button>
            ) : (
              <button type="button" className="btn btn-ghost" onClick={stopLiveSession}>
                Stop session
              </button>
            )}

            {liveError && <p className="error-text">{liveError}</p>}

            {liveResult && (
              <div className="live-stats">
                <div className="live-stats__primary">
                  {liveResult.type === 'hold'
                    ? `${liveResult.hold_seconds ?? 0}s held`
                    : `${liveResult.rep_count ?? 0} reps`}
                </div>
                <div className="live-stats__row">
                  <span>Angle</span>
                  <span>{liveResult.angle != null ? `${liveResult.angle}°` : '-'}</span>
                </div>
                <div className="live-stats__row">
                  <span>Feedback</span>
                  <span>{liveResult.feedback || '-'}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {mode === 'upload' && (
        <form className="upload-panel" onSubmit={handleUpload}>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button className="btn btn-primary" type="submit" disabled={!file || uploading}>
            {uploading ? 'Analyzing…' : 'Analyze video'}
          </button>

          {uploadError && <p className="error-text">{uploadError}</p>}

          {uploadResult && (
            <div className="live-stats">
              <div className="live-stats__primary">
                {uploadResult.total_reps != null
                  ? `${uploadResult.total_reps} reps`
                  : `${uploadResult.total_hold_seconds ?? 0}s held`}
              </div>
              <div className="live-stats__row">
                <span>Frames processed</span>
                <span>{uploadResult.frames_processed}</span>
              </div>
              {uploadResult.annotated_video_id && (
                <a
                  className="module-card__link"
                  href={`${api.base}/workout/result-video/${uploadResult.annotated_video_id}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  View annotated video &#8594;
                </a>
              )}
            </div>
          )}
        </form>
      )}
    </div>
  );
}