import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # fast + free-tier friendly

SYSTEM_PROMPT = (
    "You are a friendly, knowledgeable AI fitness dietician for people in a "
    "wide range of real-life situations - not just people with a full "
    "kitchen and unlimited budget. Many users are hostel/dorm students "
    "eating from a mess hall or canteen with no cooking equipment, people "
    "in remote areas with limited food variety, or people on a tight "
    "budget. ALWAYS consider the user's stated budget and cooking access "
    "if provided, and default to assuming modest budget and limited "
    "cooking access if the user hasn't said otherwise - do not assume "
    "access to a full kitchen, specialty ingredients, or supplements "
    "unless they mention it. Prefer common, cheap, widely available foods "
    "(rice, dal/lentils, eggs, bananas, seasonal vegetables, peanut "
    "butter) over expensive or hard-to-find ones. Give concise, practical "
    "advice, under 150 words unless asked for more detail. Do not give "
    "medical diagnoses - suggest consulting a doctor for medical concerns."
)


def get_chat_response(user_message: str, user_context: dict = None) -> dict:
    """
    user_message: the user's question, e.g. "I don't eat dairy, what should I eat instead?"
    user_context: optional dict (e.g. their calorie_data from calculate_daily_calories)
                  so the chatbot can personalize its answer.

    Returns: {"reply": str | None, "error": str | None}
    Exactly one of "reply" / "error" will be set - check "error" first.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {
            "reply": None,
            "error": (
                "GROQ_API_KEY not set. Create a .env file in the backend/ "
                "folder with GROQ_API_KEY=your_key - see chatbot.py docstring."
            ),
        }

    context_note = f"\n\nUser's current stats: {user_context}" if user_context else ""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message + context_note},
        ],
        "temperature": 0.7,
        "max_tokens": 300,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return {"reply": reply, "error": None}
    except requests.exceptions.RequestException as e:
        return {"reply": None, "error": f"Chatbot request failed: {str(e)}"}
    except (KeyError, IndexError) as e:
        return {"reply": None, "error": f"Unexpected response format from Groq: {str(e)}"}