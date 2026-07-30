from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class DietLog(Base):
    __tablename__ = "diet_logs"

    id = Column(Integer, primary_key=True, index=True)
    bmi = Column(Float, nullable=False)
    target_calories = Column(Integer, nullable=False)
    diet_preference = Column(String, nullable=False)
    budget_level = Column(String, nullable=True)
    cooking_access = Column(String, nullable=True)
    meal_plan_json = Column(Text, nullable=True)  # meal plan stored as JSON text
    created_at = Column(DateTime(timezone=True), server_default=func.now())