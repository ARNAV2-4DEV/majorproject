from datetime import datetime, timedelta


def calculate_streak(session_dates: list) -> int:
    if not session_dates:
        return 0

    unique_days = {d.date() for d in session_dates}
    today = datetime.now().date()

    start_day = today if today in unique_days else today - timedelta(days=1)

    streak = 0
    day = start_day
    while day in unique_days:
        streak += 1
        day -= timedelta(days=1)

    return streak


def analyze_habit(session_dates: list) -> dict:
    """
    session_dates: list of datetime objects, one per completed workout
    session.

    Returns risk level + streak + a motivational nudge appropriate to
    the situation.
    """
    if not session_dates:
        return {
            "risk": "unknown",
            "reason": "No workout history yet.",
            "nudge": "Log your first session to start tracking your habit!",
            "streak_days": 0,
            "sessions_last_7_days": 0,
        }

    session_dates = sorted(session_dates)
    now = datetime.now()
    last_date = session_dates[-1]
    days_since = (now - last_date).days
    streak = calculate_streak(session_dates)

    last_7_days = [d for d in session_dates if (now - d).days < 7]
    prev_7_days = [d for d in session_dates if 7 <= (now - d).days < 14]

    if days_since >= 4:
        return {
            "risk": "high",
            "reason": f"No activity logged in {days_since} days.",
            "nudge": "It's been a few days - even a 15 minute session keeps the streak alive.",
            "streak_days": streak,
            "sessions_last_7_days": len(last_7_days),
        }

    if len(last_7_days) < len(prev_7_days) and len(last_7_days) <= 1:
        return {
            "risk": "medium",
            "reason": f"Only {len(last_7_days)} session(s) this week vs {len(prev_7_days)} last week.",
            "nudge": "Your consistency dipped a bit - let's plan your next session now.",
            "streak_days": streak,
            "sessions_last_7_days": len(last_7_days),
        }

    return {
        "risk": "low",
        "reason": "Consistent recent activity.",
        "nudge": "Great consistency - keep it up!",
        "streak_days": streak,
        "sessions_last_7_days": len(last_7_days),
    }