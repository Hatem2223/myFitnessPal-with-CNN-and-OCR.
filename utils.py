from typing import Dict
activity_map = {"sedentary":1.2,"light":1.375,"moderate":1.55,"active":1.725,"very_active":1.9}

def mifflin_st_jeor(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    return (10*weight_kg + 6.25*height_cm - 5*age + (5 if sex.lower().startswith('m') else -161))

def tdee(sex: str, weight_kg: float, height_cm: float, age: int, activity_level: str) -> float:
    return mifflin_st_jeor(sex, weight_kg, height_cm, age) * activity_map.get(activity_level, 1.55)

def macro_targets(tdee_kcal: float, goal: str) -> Dict[str, float]:
    if goal == "lose":
        calories = tdee_kcal * 0.85
    elif goal == "gain":
        calories = tdee_kcal * 1.15
    else:
        calories = tdee_kcal
    return {
        "calories": round(calories, 0),
        "protein_g": round((calories * 0.30)/4, 0),
        "carbs_g": round((calories * 0.40)/4, 0),
        "fat_g": round((calories * 0.30)/9, 0),
    }