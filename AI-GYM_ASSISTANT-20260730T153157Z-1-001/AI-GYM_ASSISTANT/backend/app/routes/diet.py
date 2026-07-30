import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.dietician.calorie_engine import (
    calculate_daily_calories,
    ActivityLevel,
    suggest_meal_plan,
    generate_grocery_list,
)
from app.modules.dietician.chatbot import get_chat_response
from app.database import get_db
from app.models.diet_log import DietLog

router = APIRouter(prefix="/diet", tags=["diet"])


class DietRequest(BaseModel):
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")
    height_cm: float = Field(..., gt=0, description="Height in centimeters")
    age: int = Field(..., gt=0, le=120)
    sex: str = Field(..., description="'male' or 'female'")
    activity_level: ActivityLevel = ActivityLevel.MODERATE
    goal: str = Field("maintain", description="'lose', 'maintain', or 'gain'")
    diet_preference: str = Field(
        "non_vegetarian", description="'vegetarian', 'vegan', or 'non_vegetarian'"
    )
    budget_level: Optional[str] = Field(
        None, description="'low', 'medium', or 'high' - omit for no budget constraint"
    )
    cooking_access: Optional[str] = Field(
        None,
        description=(
            "'none' (hostel/mess/canteen only), 'limited' (kettle/microwave "
            "only), or 'full' (can actually cook) - omit for no constraint"
        ),
    )


@router.post("/calculate")
def calculate_diet_plan(request: DietRequest, db: Session = Depends(get_db)):
    """
    Full pipeline: BMI + calorie targets -> meal plan -> grocery list.
    This is what the frontend calls when a user fills out their profile.
    Also saves this calculation to the database.
    """
    if request.sex.lower() not in ("male", "female"):
        raise HTTPException(status_code=400, detail="sex must be 'male' or 'female'")
    if request.goal not in ("lose", "maintain", "gain"):
        raise HTTPException(status_code=400, detail="goal must be 'lose', 'maintain', or 'gain'")

    calorie_data = calculate_daily_calories(
        weight_kg=request.weight_kg,
        height_cm=request.height_cm,
        age=request.age,
        sex=request.sex,
        activity_level=request.activity_level,
        goal=request.goal,
    )

    meal_plan = suggest_meal_plan(
        target_calories=calorie_data["target_calories"],
        diet_preference=request.diet_preference,
        budget_level=request.budget_level,
        cooking_access=request.cooking_access,
    )

    grocery_list = generate_grocery_list(meal_plan)

    db_log = DietLog(
        bmi=calorie_data["bmi"],
        target_calories=calorie_data["target_calories"],
        diet_preference=request.diet_preference,
        budget_level=request.budget_level,
        cooking_access=request.cooking_access,
        meal_plan_json=json.dumps(meal_plan),
    )
    db.add(db_log)
    db.commit()

    return {
        "calorie_data": calorie_data,
        "meal_plan": meal_plan,
        "grocery_list": grocery_list,
    }


@router.get("/history")
def get_diet_history(limit: int = 50, db: Session = Depends(get_db)):
    """Returns past diet calculations, most recent first."""
    logs = db.query(DietLog).order_by(DietLog.created_at.desc()).limit(limit).all()
    return {
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "bmi": log.bmi,
                "target_calories": log.target_calories,
                "diet_preference": log.diet_preference,
                "budget_level": log.budget_level,
                "cooking_access": log.cooking_access,
                "meal_plan": json.loads(log.meal_plan_json) if log.meal_plan_json else None,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    calorie_data: Optional[dict] = None


@router.post("/chat")
def diet_chat(request: ChatRequest):
    """
    Natural language diet Q&A, e.g. "I don't eat dairy, what should I have
    for breakfast instead?" Powered by Groq's free-tier LLM API - requires
    GROQ_API_KEY to be set in a .env file (see chatbot.py for setup steps).
    """
    result = get_chat_response(request.message, user_context=request.calorie_data)
    if result["error"]:
        raise HTTPException(status_code=503, detail=result["error"])
    return {"reply": result["reply"]}