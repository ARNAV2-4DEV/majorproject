from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import workout, diet, habit
from app.database import init_db

app = FastAPI(
    title="AI Gym & Fitness Assistant API",
    description="Backend for pose-based rep counting, diet planning, and habit tracking.",
    version="0.1.0",
)

init_db()  # creates gym_assistant.db and its tables if they don't exist yet
app.include_router(workout.router)
app.include_router(diet.router)
app.include_router(habit.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Gym & Fitness Assistant API is running"}