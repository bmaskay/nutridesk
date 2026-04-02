"""
meal_planner.py — Recipe selection & 7-day meal plan generation for NutriDesk

Algorithm:
1. Load recipe library JSON
2. Filter by client preferences (diet type, allergies, conditions, cuisines)
3. For each day: pick breakfast, 2 lunch options, 2 dinner options, optional snack
4. Try to hit per-meal calorie targets (±20% tolerance)
5. Rotate recipes across 7 days — no same recipe on back-to-back days
"""

import json
import random
from pathlib import Path
from typing import Optional

from utils.calculations import MEAL_DISTRIBUTION

RECIPE_PATH = Path(__file__).parent.parent.parent / "recipe_library.json"

# Condition tag map (client medical_conditions → recipe condition_flags)
CONDITION_FLAG_MAP = {
    "Diabetes / pre-diabetes":   "diabetes_friendly",
    "PCOS":                      "pcos_friendly",
    "Hypothyroidism / thyroid":  "thyroid_friendly",
}

# Diet type filter
DIET_RESTRICTIONS = {
    "Vegetarian":  {"exclude_meat": True},
    "Vegan":       {"exclude_meat": True, "exclude_dairy": True},
    "Eggetarian":  {"exclude_meat": True, "allow_egg": True},
    "Non-vegetarian": {},
}


def load_recipes() -> list[dict]:
    with open(RECIPE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Support both bare list and {"recipes": [...]} formats
    if isinstance(data, list):
        return data
    return data.get("recipes", [])


def filter_recipes(
    recipes: list[dict],
    diet_type: str = "Non-vegetarian",
    allergies: list[str] = None,
    dislikes: list[str] = None,
    preferred_cuisines: list[str] = None,
    medical_conditions: list[str] = None,
    preferred_meats: list[str] = None,
    preferred_vegs: list[str] = None,
) -> list[dict]:
    allergies = [a.lower() for a in (allergies or [])]
    dislikes   = [d.lower() for d in (dislikes or [])]

    required_flags = set()
    for cond in (medical_conditions or []):
        flag = CONDITION_FLAG_MAP.get(cond)
        if flag:
            required_flags.add(flag)

    filtered = []
    for r in recipes:
        tags  = [t.lower() for t in r.get("dietary_tags", [])]
        ingr  = [i.lower() for i in r.get("key_ingredients", [])]
        meat  = (r.get("meat_type") or "").lower()
        cuisine = r.get("cuisine", "")

        # Diet type filter
        if diet_type in ("Vegetarian", "Vegan", "Eggetarian"):
            if "vegetarian" not in tags and "vegan" not in tags:
                # Allow eggs for eggetarian
                if diet_type == "Eggetarian" and "egg" in ingr:
                    pass
                else:
                    continue

        # Allergy filter — exclude if any allergen in ingredients
        skip = False
        for allergen in allergies:
            if any(allergen in ing for ing in ingr):
                skip = True
                break
        if skip:
            continue

        # Dislikes — skip recipes whose name or ingredients match
        name_lower = r.get("name_en", "").lower()
        skip = False
        for dislike in dislikes:
            if dislike in name_lower or any(dislike in ing for ing in ingr):
                skip = True
                break
        if skip:
            continue

        # Medical condition flags — if conditions require flags, recipe must have ALL of them
        if required_flags:
            recipe_flags = set(r.get("condition_flags", []))
            if not required_flags.issubset(recipe_flags):
                continue

        # Cuisine preference (soft filter — include preferred + Nepali baseline)
        if preferred_cuisines:
            preferred_lower = [c.lower() for c in preferred_cuisines]
            if cuisine.lower() not in preferred_lower and cuisine.lower() != "nepali":
                # Don't hard-exclude — just deprioritise (we'll weight later)
                r = dict(r)
                r["_deprioritised"] = True

        filtered.append(r)

    return filtered


def pick_recipes(
    pool: list[dict],
    category: str,
    target_kcal: float,
    n: int = 1,
    exclude_ids: set = None,
    tolerance: float = 0.25,
) -> list[dict]:
    """
    Select n recipes from pool matching category and within calorie tolerance.
    Avoid ids in exclude_ids.
    """
    exclude_ids = exclude_ids or set()
    candidates = [
        r for r in pool
        if r.get("category", "").lower() == category.lower()
        and r.get("id") not in exclude_ids
        and abs(r.get("calories", 0) - target_kcal) / max(target_kcal, 1) <= tolerance
    ]

    # Relax tolerance if not enough candidates
    if len(candidates) < n:
        candidates = [
            r for r in pool
            if r.get("category", "").lower() == category.lower()
            and r.get("id") not in exclude_ids
        ]

    # Prefer non-deprioritised
    preferred = [r for r in candidates if not r.get("_deprioritised")]
    pool_use  = preferred if len(preferred) >= n else candidates

    if not pool_use:
        return []

    return random.sample(pool_use, min(n, len(pool_use)))


def generate_meal_plan(
    client: dict,
    assessment: dict,
    days: int = 7,
    seed: Optional[int] = None,
) -> dict:
    """
    Generate a day-by-day meal plan.
    Returns a dict keyed by day name with breakfast, lunch (2), dinner (2), snack.
    """
    if seed is not None:
        random.seed(seed)

    target_kcal = assessment.get("target_calories", 1800)

    # Per-meal calorie budgets
    b_target = target_kcal * MEAL_DISTRIBUTION["Breakfast"]
    l_target = target_kcal * MEAL_DISTRIBUTION["Lunch"]
    d_target = target_kcal * MEAL_DISTRIBUTION["Dinner"]
    s_target = target_kcal * MEAL_DISTRIBUTION["Snack"]

    all_recipes = load_recipes()

    filtered = filter_recipes(
        all_recipes,
        diet_type=client.get("diet_type", "Non-vegetarian"),
        allergies=client.get("allergies", []),
        dislikes=client.get("dislikes", []),
        preferred_cuisines=client.get("cuisine_pref", []),
        medical_conditions=client.get("medical_conditions", []),
        preferred_meats=client.get("meat_choices", []),
        preferred_vegs=client.get("veg_choices", []),
    )

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"]

    plan = {}
    used_breakfast = set()
    used_lunch     = set()
    used_dinner    = set()
    used_snack     = set()

    for i in range(days):
        day = days_of_week[i % 7]

        breakfast = pick_recipes(filtered, "breakfast", b_target, n=1, exclude_ids=used_breakfast)
        lunch     = pick_recipes(filtered, "lunch",     l_target, n=2, exclude_ids=used_lunch)
        dinner    = pick_recipes(filtered, "dinner",    d_target, n=2, exclude_ids=used_dinner)
        snack     = pick_recipes(filtered, "snack",     s_target, n=1, exclude_ids=used_snack)

        for r in breakfast: used_breakfast.add(r["id"])
        for r in lunch:     used_lunch.add(r["id"])
        for r in dinner:    used_dinner.add(r["id"])
        for r in snack:     used_snack.add(r["id"])

        # Reset pools when exhausted
        if len(used_breakfast) >= len([r for r in filtered if r.get("category","").lower()=="breakfast"]):
            used_breakfast.clear()
        if len(used_lunch) >= len([r for r in filtered if r.get("category","").lower()=="lunch"]):
            used_lunch.clear()
        if len(used_dinner) >= len([r for r in filtered if r.get("category","").lower()=="dinner"]):
            used_dinner.clear()
        if len(used_snack) >= len([r for r in filtered if r.get("category","").lower()=="snack"]):
            used_snack.clear()

        plan[day] = {
            "breakfast": breakfast,
            "lunch":     lunch,
            "dinner":    dinner,
            "snack":     snack,
        }

    return plan


def plan_daily_totals(day_plan: dict) -> dict:
    """Estimate kcal/protein for a single day (using option A for lunch/dinner)."""
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    slots = (
        day_plan.get("breakfast", [])[:1]
        + day_plan.get("lunch", [])[:1]
        + day_plan.get("dinner", [])[:1]
        + day_plan.get("snack", [])[:1]
    )
    for r in slots:
        totals["calories"]  += r.get("calories", 0)
        totals["protein_g"] += r.get("protein_g", 0)
        totals["carbs_g"]   += r.get("carbs_g", 0)
        totals["fat_g"]     += r.get("fat_g", 0)
    return {k: round(v, 1) for k, v in totals.items()}


def snack_swap_suggestions(client: dict) -> list[dict]:
    """Return 5 healthy snack alternatives from the recipe library."""
    all_recipes = load_recipes()
    snacks = [r for r in all_recipes if r.get("category", "").lower() == "snack"]
    # Filter by diet type
    diet = client.get("diet_type", "Non-vegetarian")
    if diet in ("Vegetarian", "Vegan", "Eggetarian"):
        snacks = [r for r in snacks if "vegetarian" in [t.lower() for t in r.get("dietary_tags", [])]]
    random.shuffle(snacks)
    return snacks[:5]
