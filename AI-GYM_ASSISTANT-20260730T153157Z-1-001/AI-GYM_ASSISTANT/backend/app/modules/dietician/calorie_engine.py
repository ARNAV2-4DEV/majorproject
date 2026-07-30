from enum import Enum


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Mifflin-St Jeor equation."""
    if sex.lower() == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def calculate_daily_calories(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    activity_level: ActivityLevel,
    goal: str = "maintain",  # "lose", "maintain", "gain"
) -> dict:
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    maintenance = bmr * ACTIVITY_MULTIPLIERS[activity_level]

    if goal == "lose":
        target = maintenance - 500  # ~0.5kg/week loss
    elif goal == "gain":
        target = maintenance + 500
    else:
        target = maintenance

    bmi = calculate_bmi(weight_kg, height_cm)

    return {
        "bmi": bmi,
        "bmi_category": bmi_category(bmi),
        "bmr": round(bmr),
        "maintenance_calories": round(maintenance),
        "target_calories": round(target),
        "goal": goal,
        "macros": {
            "protein_g": round(target * 0.30 / 4),
            "carbs_g": round(target * 0.40 / 4),
            "fat_g": round(target * 0.30 / 9),
        },
    }



MEAL_DATABASE = {
    "breakfast": [
        {"name": "Oats with banana and peanut butter", "calories": 380, "protein_g": 14,
         "tags": ["vegetarian", "vegan"], "budget": "low", "cooking": "limited"},
        {"name": "Greek yogurt with berries and granola", "calories": 320, "protein_g": 20,
         "tags": ["vegetarian"], "budget": "medium", "cooking": "none"},
        {"name": "Scrambled eggs with whole wheat toast", "calories": 350, "protein_g": 22,
         "tags": ["non_vegetarian", "vegetarian"], "budget": "low", "cooking": "full"},
        {"name": "Tofu scramble with vegetables", "calories": 300, "protein_g": 18,
         "tags": ["vegan", "vegetarian"], "budget": "medium", "cooking": "full"},
        {"name": "Banana + boiled eggs (mess/canteen)", "calories": 300, "protein_g": 18,
         "tags": ["non_vegetarian", "vegetarian"], "budget": "low", "cooking": "none"},
        {"name": "Peanut butter sandwich (bread + PB, no cooking)", "calories": 340, "protein_g": 12,
         "tags": ["vegan", "vegetarian"], "budget": "low", "cooking": "none"},
    ],
    "lunch": [
        {"name": "Grilled chicken breast with rice and broccoli", "calories": 520, "protein_g": 42,
         "tags": ["non_vegetarian"], "budget": "high", "cooking": "full"},
        {"name": "Chickpea and vegetable curry with rice", "calories": 480, "protein_g": 18,
         "tags": ["vegan", "vegetarian"], "budget": "medium", "cooking": "full"},
        {"name": "Paneer tikka with mixed salad", "calories": 450, "protein_g": 24,
         "tags": ["vegetarian"], "budget": "medium", "cooking": "full"},
        {"name": "Dal-rice + salad (standard hostel mess meal)", "calories": 420, "protein_g": 20,
         "tags": ["vegan", "vegetarian"], "budget": "low", "cooking": "none"},
        {"name": "Mess-hall thali (rice, dal, sabzi, roti)", "calories": 500, "protein_g": 18,
         "tags": ["vegetarian"], "budget": "low", "cooking": "none"},
    ],
    "dinner": [
        {"name": "Grilled fish with quinoa and vegetables", "calories": 480, "protein_g": 38,
         "tags": ["non_vegetarian"], "budget": "high", "cooking": "full"},
        {"name": "Stir-fried tofu with brown rice", "calories": 440, "protein_g": 22,
         "tags": ["vegan", "vegetarian"], "budget": "medium", "cooking": "full"},
        {"name": "Chicken stir fry with vegetables", "calories": 460, "protein_g": 35,
         "tags": ["non_vegetarian"], "budget": "high", "cooking": "full"},
        {"name": "Rajma (kidney bean curry) with rice", "calories": 410, "protein_g": 17,
         "tags": ["vegan", "vegetarian"], "budget": "low", "cooking": "full"},
        {"name": "Mess-hall dinner (rice/roti, dal, vegetable)", "calories": 460, "protein_g": 16,
         "tags": ["vegetarian"], "budget": "low", "cooking": "none"},
    ],
    "snack": [
        {"name": "Mixed nuts and an apple", "calories": 220, "protein_g": 6,
         "tags": ["vegan", "vegetarian"], "budget": "medium", "cooking": "none"},
        {"name": "Protein shake", "calories": 180, "protein_g": 25,
         "tags": ["vegetarian"], "budget": "medium", "cooking": "none"},
        {"name": "Roasted chickpeas / roasted chana", "calories": 200, "protein_g": 10,
         "tags": ["vegan", "vegetarian"], "budget": "low", "cooking": "none"},
        {"name": "Banana (cheapest available fruit)", "calories": 105, "protein_g": 1,
         "tags": ["vegan", "vegetarian"], "budget": "low", "cooking": "none"},
        {"name": "Buttermilk / chaas", "calories": 90, "protein_g": 3,
         "tags": ["vegetarian"], "budget": "low", "cooking": "none"},
    ],
}

# Ordering used to relax constraints if no exact match exists for a slot 
_BUDGET_RANK = {"low": 0, "medium": 1, "high": 2}
_COOKING_RANK = {"none": 0, "limited": 1, "full": 2}


def suggest_meal_plan(
    target_calories: int,
    diet_preference: str = "non_vegetarian",
    budget_level: str = None,
    cooking_access: str = None,
) -> dict:
    """
    diet_preference: "vegetarian", "vegan", or "non_vegetarian"
    budget_level: "low", "medium", "high", or None (no constraint)
    cooking_access: "none", "limited", "full", or None (no constraint)

    "none" cooking_access + "low" budget together covers the hostel /
    no-kitchen / tight-money case explicitly - the plan will only suggest
    meals realistically available from a mess hall, canteen, or a shop,
    with no cooking equipment assumed.
    """
    plan = {}
    total_calories = 0

    for slot, options in MEAL_DATABASE.items():
        candidates = [m for m in options if diet_preference in m["tags"]]

        if budget_level:
            max_budget_rank = _BUDGET_RANK[budget_level]
            budget_matches = [m for m in candidates if _BUDGET_RANK[m["budget"]] <= max_budget_rank]
            if budget_matches:
                candidates = budget_matches
            

        if cooking_access:
            max_cooking_rank = _COOKING_RANK[cooking_access]
            cooking_matches = [m for m in candidates if _COOKING_RANK[m["cooking"]] <= max_cooking_rank]
            if cooking_matches:
                candidates = cooking_matches

        if not candidates:
            candidates = options  

        chosen = candidates[0]
        plan[slot] = chosen
        total_calories += chosen["calories"]

    return {
        "target_calories": target_calories,
        "planned_calories": total_calories,
        "difference": target_calories - total_calories,
        "constraints_applied": {
            "budget_level": budget_level,
            "cooking_access": cooking_access,
        },
        "meals": plan,
    }


def generate_grocery_list(meal_plan: dict) -> list:
    """
    Very simple ingredient extraction from meal names - a real version
    would use a proper recipe/ingredient database. This is intentionally
    lightweight for the MVP.

    Meals with cooking == "none" (mess hall, canteen, ready-to-eat) are
    skipped - there's nothing to buy, it's already-prepared food. Only
    meals that actually require ingredients get added to the list.
    """
    import re

    grocery_set = set()
    for meal in meal_plan.get("meals", {}).values():
        if meal.get("cooking") == "none":
            continue  

        cleaned = re.sub(r"[()/+\-]", " ", meal["name"].lower())
        words = cleaned.replace(",", "").replace("with", "").split()
        grocery_set.update(w for w in words if len(w) > 3)

    return sorted(grocery_set)


# TODO (next build step): NLP chatbot for diet Q&A
def chat_placeholder(user_message: str) -> str:
    return (
        "Diet chatbot not yet implemented. "
        "Calorie/BMI calculations and meal suggestions are working."
    )