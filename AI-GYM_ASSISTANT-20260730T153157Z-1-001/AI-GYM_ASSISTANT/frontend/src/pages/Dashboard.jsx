import { useEffect, useState } from 'react';
import { api } from '../api/client';
import './Dashboard.css';

const RISK_LABEL = {
  low: 'On track',
  medium: 'Slipping',
  high: 'At risk',
  unknown: 'No data yet',
};

export default function Dashboard() {
  const [habit, setHabit] = useState(null);
  const [workoutHistory, setWorkoutHistory] = useState([]);
  const [dietHistory, setDietHistory] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getHabitStatus(), api.getWorkoutHistory(), api.getDietHistory()])
      .then(([habitData, workoutData, dietData]) => {
        setHabit(habitData);
        setWorkoutHistory(workoutData.sessions || []);
        setDietHistory(dietData.logs || []);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="container dashboard-page">
      <p className="eyebrow">Consistency</p>
      <h1 className="dashboard-page__title">Dashboard</h1>

      {error && (
        <p className="error-text">
          Couldn't reach the backend: {error}. Is the server running?
        </p>
      )}

      {habit && (
        <div className="habit-banner">
          <div className="habit-banner__streak">
            <span className="habit-banner__streak-value">{habit.streak_days}</span>
            <span className="habit-banner__streak-label">day streak</span>
          </div>
          <div className="habit-banner__body">
            <span className={`risk-pill risk-pill--${habit.risk}`}>
              {RISK_LABEL[habit.risk] || habit.risk}
            </span>
            <p>{habit.nudge}</p>
            <p className="habit-banner__reason">{habit.reason}</p>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        <div className="history-panel">
          <h3 className="diet-result__heading">Workout history</h3>
          {workoutHistory.length === 0 ? (
            <p className="history-panel__empty">No sessions logged yet - go train.</p>
          ) : (
            <ul className="history-list">
              {workoutHistory.map((s) => (
                <li key={s.id} className="history-list__item">
                  <span className="history-list__exercise">
                    {s.exercise.replaceAll('_', ' ')}
                  </span>
                  <span className="history-list__metric">
                    {s.session_type === 'hold'
                      ? `${s.total_hold_seconds ?? 0}s`
                      : `${s.total_reps ?? 0} reps`}
                  </span>
                  <span className="history-list__date">
                    {s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="history-panel">
          <h3 className="diet-result__heading">Diet history</h3>
          {dietHistory.length === 0 ? (
            <p className="history-panel__empty">No diet plans calculated yet.</p>
          ) : (
            <ul className="history-list">
              {dietHistory.map((log) => (
                <li key={log.id} className="history-list__item">
                  <span className="history-list__exercise">BMI {log.bmi}</span>
                  <span className="history-list__metric">{log.target_calories} kcal</span>
                  <span className="history-list__date">
                    {log.created_at ? new Date(log.created_at).toLocaleDateString() : ''}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}