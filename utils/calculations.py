"""
calculations.py — Clinical nutrition calculations for NutriDesk
Formulas: Mifflin-St Jeor BMR, activity-based TDEE, macro splits, BMI, hydration
"""

from datetime import date, timedelta


# ── Activity multipliers ────────────────────────────────────────────────────

ACTIVITY_MULTIPLIERS = {
    "Sedentary (desk job, little/no exercise)":   1.20,
    "Lightly active (light exercise 1–3 days/wk)": 1.375,
    "Moderately active (moderate exercise 3–5 days/wk)": 1.55,
    "Very active (hard exercise 6–7 days/wk)":    1.725,
    "Extra active (physical job + hard training)": 1.90,
}

# ── Goal-based calorie adjustments ─────────────────────────────────────────

GOAL_ADJUSTMENTS = {
    "Fat loss":          -500,
    "Mild fat loss":     -250,
    "Maintain weight":    0,
    "Lean muscle gain":  +250,
    "Muscle gain":       +500,
}

# ── Macro ratios by goal (protein_pct, carb_pct, fat_pct) ──────────────────
# Lean muscle gain uses slightly more protein vs Muscle gain, which prioritises carbs

MACRO_RATIOS = {
    "Fat loss":          (0.35, 0.40, 0.25),
    "Mild fat loss":     (0.30, 0.45, 0.25),
    "Maintain weight":   (0.25, 0.50, 0.25),
    "Lean muscle gain":  (0.32, 0.43, 0.25),   # Higher protein, moderate carbs
    "Muscle gain":       (0.28, 0.47, 0.25),   # More carbs for volume training
}

# ── Gender-based minimum safe calorie floors ────────────────────────────────
# Women: 1200 kcal / Men: 1500 kcal (evidence-based clinical minimums)

MIN_CALORIES = {
    "female": 1200,
    "male":   1500,
    "other":  1200,
}


def calculate_age(dob_str: str) -> int:
    """Return age in years from ISO date string YYYY-MM-DD."""
    if not dob_str:
        return 0
    dob = date.fromisoformat(dob_str)
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if not height_cm or not weight_kg:
        return 0.0
    h_m = height_cm / 100
    return round(weight_kg / (h_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 23.0:
        return "Normal (Asian BMI)"
    elif bmi < 27.5:
        return "Overweight (Asian BMI)"
    else:
        return "Obese (Asian BMI)"


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor BMR (kcal/day)."""
    if not all([weight_kg, height_cm, age]):
        return 0.0
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender.lower() in ("male", "m"):
        return round(base + 5, 1)
    else:
        return round(base - 161, 1)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    return round(bmr * multiplier, 1)


def calculate_target_calories(tdee: float, goal: str, gender: str = "Female") -> float:
    """Apply goal adjustment then enforce gender-appropriate minimum."""
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    floor = MIN_CALORIES.get(gender.lower(), 1200)
    return round(max(tdee + adjustment, floor), 1)


def calculate_macros(target_calories: float, goal: str, weight_kg: float = 0) -> dict:
    """
    Return macro targets in grams.

    Protein is the higher of:
      - percentage-based split (MACRO_RATIOS)
      - weight-based floor: 1.2–1.6 g/kg body weight depending on goal
    This prevents under-provisioning protein for lighter clients on low-calorie plans.
    Carbs and fat are recalculated from remaining calories to keep total accurate.
    """
    p_pct, c_pct, f_pct = MACRO_RATIOS.get(goal, (0.25, 0.50, 0.25))
    protein_pct_g = round((target_calories * p_pct) / 4, 1)

    # Weight-based protein floor
    if weight_kg:
        if goal in ("Fat loss", "Lean muscle gain", "Muscle gain"):
            protein_floor_g = round(weight_kg * 1.6, 1)
        elif goal == "Mild fat loss":
            protein_floor_g = round(weight_kg * 1.4, 1)
        else:
            protein_floor_g = round(weight_kg * 1.2, 1)
        protein_g = max(protein_pct_g, protein_floor_g)
    else:
        protein_g = protein_pct_g

    # Recalculate carbs and fat from remaining calories after protein
    protein_kcal = protein_g * 4
    remaining = max(target_calories - protein_kcal, 0)
    total_cf = c_pct + f_pct
    carbs_g = round((remaining * (c_pct / total_cf)) / 4, 1)
    fat_g   = round((remaining * (f_pct / total_cf)) / 9, 1)

    return {
        "protein_g": round(protein_g, 1),
        "carbs_g":   carbs_g,
        "fat_g":     fat_g,
    }


def calculate_hydration(weight_kg: float) -> float:
    """Recommended water intake in litres (35 ml/kg body weight)."""
    return round((weight_kg * 35) / 1000, 1)


def calculate_ideal_weight_range(height_cm: float, gender: str) -> tuple[float, float]:
    """Healthy BMI range 18.5–22.9 (Asian) converted to kg."""
    h_m = height_cm / 100
    low  = round(18.5 * h_m ** 2, 1)
    high = round(22.9 * h_m ** 2, 1)
    return low, high


def fat_loss_timeline(current_weight: float, target_weight: float,
                      goal: str = "Fat loss") -> dict:
    """
    Estimate realistic timeline based on goal-appropriate weekly rate.
      Fat loss:      0.5 kg/week (500 kcal deficit)
      Mild fat loss: 0.25 kg/week (250 kcal deficit)
    """
    if not target_weight or current_weight <= target_weight:
        return {}

    weekly_loss_kg = 0.5 if goal == "Fat loss" else 0.25
    kg_to_lose = round(current_weight - target_weight, 1)
    weeks = round(kg_to_lose / weekly_loss_kg)
    months = round(weeks / 4.3, 1)

    # Correctly compute target date by adding weeks as days (not just adjusting year)
    target_date = date.today() + timedelta(weeks=weeks)

    return {
        "kg_to_lose":     kg_to_lose,
        "weeks":          weeks,
        "months":         months,
        "weekly_rate_kg": weekly_loss_kg,
        "target_date":    str(target_date),
    }


def full_assessment(client: dict) -> dict:
    """
    Run all calculations for a client dict.
    Returns a dict with BMI, BMR, TDEE, targets, macros, hydration.
    """
    age      = calculate_age(client.get("dob", ""))
    weight   = client.get("weight_kg", 0) or 0
    height   = client.get("height_cm", 0) or 0
    gender   = client.get("gender", "Female")
    goal     = client.get("goal", "Maintain weight")
    activity = client.get("activity_level", "Lightly active (light exercise 1–3 days/wk)")

    bmi       = calculate_bmi(weight, height)
    bmr       = calculate_bmr(weight, height, age, gender)
    tdee      = calculate_tdee(bmr, activity)
    target    = calculate_target_calories(tdee, goal, gender)
    macros    = calculate_macros(target, goal, weight)
    hydration = calculate_hydration(weight)
    ideal_low, ideal_high = calculate_ideal_weight_range(height, gender)

    return {
        "age":            age,
        "bmi":            bmi,
        "bmi_category":   bmi_category(bmi),
        "bmr":            bmr,
        "tdee":           tdee,
        "target_calories": target,
        "goal_adjustment": GOAL_ADJUSTMENTS.get(goal, 0),
        "protein_g":      macros["protein_g"],
        "carbs_g":        macros["carbs_g"],
        "fat_g":          macros["fat_g"],
        "hydration_L":    hydration,
        "ideal_weight_low":  ideal_low,
        "ideal_weight_high": ideal_high,
    }


# ── Meal calorie distribution (% of daily target per meal) ─────────────────
# Snack bumped from 5% → 9% to reflect realistic portions.
# Lunch/dinner adjusted slightly to balance.

MEAL_DISTRIBUTION = {
    "Breakfast": 0.27,
    "Lunch":     0.34,
    "Dinner":    0.30,
    "Snack":     0.09,   # per snack slot
}
