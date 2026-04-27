"""
meal_planner.py — Recipe selection & 7-day meal plan generation for NutriDesk

Algorithm:
1. Load recipe library JSON
2. Filter by client preferences (diet type, allergies, conditions, cuisines, veg/meat choices)
3. For each day: pick meals according to client's meal_frequency setting
4. Try to hit per-meal calorie targets (±25% tolerance)
5. Rotate recipes across 7 days — no same recipe on back-to-back days

Condition filtering uses a weighted scoring approach rather than hard AND logic,
so clients with multiple conditions still get a viable meal pool.
"""

import json
import random
from pathlib import Path
from typing import Optional

from utils.calculations import MEAL_DISTRIBUTION

RECIPE_PATH = Path(__file__).parent.parent / "recipe_library.json"

# ── Condition tag map (client medical_conditions → recipe condition_flags) ──
# All conditions now mapped — hypertension, cholesterol, IBS, anaemia, fatty liver
# added alongside the original three.

CONDITION_FLAG_MAP = {
    "Diabetes / pre-diabetes":       "diabetes_friendly",
    "PCOS":                          "pcos_friendly",
    "Hypothyroidism / thyroid":      "thyroid_friendly",
    "Hypertension":                  "hypertension_friendly",
    "High cholesterol":              "cholesterol_friendly",
    "IBS / digestive issues":        "ibs_friendly",
    "Anaemia / iron deficiency":     "anaemia_friendly",
    "Fatty liver":                   "fatty_liver_friendly",
    # Kidney disease needs specialist management — no hard filter applied;
    # the PDF surfaces a clinical caution note instead.
    "Kidney disease":                None,
}

# ── Diet type filter ────────────────────────────────────────────────────────

DIET_RESTRICTIONS = {
    "Vegetarian":     {"exclude_meat": True},
    "Vegan":          {"exclude_meat": True, "exclude_dairy": True},
    "Eggetarian":     {"exclude_meat": True, "allow_egg": True},
    "Non-vegetarian": {},
}


def load_recipes() -> list[dict]:
    with open(RECIPE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
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
    """
    Filter recipes by hard constraints (diet, allergies, dislikes) and
    soft-score by condition flags and preferences.

    Multi-condition logic: instead of requiring ALL condition flags (which
    dramatically shrinks the pool), recipes earn a proportional score for
    each matching flag. Recipes with zero matching flags are deprioritised
    rather than excluded — keeping the pool viable for clients with 3+ conditions.
    """
    allergies  = [a.lower() for a in (allergies or [])]
    dislikes   = [d.lower() for d in (dislikes or [])]

    required_flags = {}
    for cond in (medical_conditions or []):
        flag = CONDITION_FLAG_MAP.get(cond)
        if flag:
            required_flags[flag] = True
    total_flags = len(required_flags)

    pref_meats = set(m.lower() for m in (preferred_meats or []))
    pref_vegs  = set(v.lower() for v in (preferred_vegs or []))

    DAIRY_INGREDIENTS = {"milk", "curd", "yogurt", "dahi", "ghee", "paneer",
                         "butter", "cream", "cheese"}

    filtered = []
    for r in recipes:
        tags    = [t.lower() for t in r.get("dietary_tags", [])]
        ingr    = [i.lower() for i in r.get("key_ingredients", [])]
        meat    = (r.get("meat_type") or "").lower()
        cuisine = r.get("cuisine", "").lower()

        # Skip side-dish items (too low-calorie to be a standalone meal)
        if r.get("is_side_dish"):
            continue

        # ── Hard filter: diet type ───────────────────────────────────────
        if diet_type in ("Vegetarian", "Vegan", "Eggetarian"):
            is_veg = "vegetarian" in tags or "vegan" in tags
            has_egg = any(e in ingr for e in ("egg", "eggs", "anda"))
            if not is_veg:
                if diet_type == "Eggetarian" and has_egg:
                    pass
                else:
                    continue
            if diet_type == "Vegan":
                if any(d in ingr for d in DAIRY_INGREDIENTS):
                    continue

        # ── Hard filter: allergies ───────────────────────────────────────
        skip = False
        for allergen in allergies:
            if any(allergen in ing for ing in ingr):
                skip = True
                break
        if skip:
            continue

        # ── Hard filter: dislikes ────────────────────────────────────────
        name_lower = r.get("name_en", "").lower()
        for dislike in dislikes:
            if dislike in name_lower or any(dislike in ing for ing in ingr):
                skip = True
                break
        if skip:
            continue

        # ── Soft scoring ─────────────────────────────────────────────────
        recipe_flags = set(r.get("condition_flags", []))
        score = 0.0

        # Condition match score (fraction of client's required flags matched)
        if total_flags:
            matched = sum(1 for f in required_flags if f in recipe_flags)
            score += matched / total_flags
        else:
            score += 1.0

        # Cuisine preference boost
        preferred_lower = [c.lower() for c in (preferred_cuisines or [])]
        if preferred_lower:
            if cuisine in preferred_lower:
                score += 0.3
            elif cuisine == "nepali":
                score += 0.1

        # Preferred meat boost (non-veg clients)
        if pref_meats and meat and any(pm in meat for pm in pref_meats):
            score += 0.2

        # Preferred vegetable boost
        if pref_vegs:
            matched_veg = sum(1 for pv in pref_vegs if any(pv in ing for ing in ingr))
            if matched_veg:
                score += 0.1 * min(matched_veg, 2)

        # Slight penalty if no condition flags at all when client has conditions
        if total_flags > 0 and not recipe_flags:
            score -= 0.4

        r = dict(r)
        r["_score"] = round(score, 3)
        filtered.append(r)

    return filtered


def _cuisine_matches(recipe_cuisine: str, preferred_cuisines: list[str]) -> bool:
    """True if the recipe's cuisine overlaps with any of the client's preferences.
    Handles compound values like 'Continental / South Asian' correctly."""
    parts = [p.strip().lower() for p in recipe_cuisine.replace("/", "|").split("|")]
    prefs = [p.strip().lower() for p in preferred_cuisines]
    return any(
        any(pref in part or part in pref for part in parts)
        for pref in prefs
    )


def pick_recipes(
    pool: list[dict],
    category: str,
    target_kcal: float,
    n: int = 1,
    exclude_ids: set = None,
    tolerance: float = 0.25,
    preferred_cuisines: list[str] = None,
) -> list[dict]:
    """
    Select n recipes from pool matching category and within calorie tolerance.
    Prefers higher-scored recipes. Falls back to full category if range is tight.

    Cuisine guarantee: if preferred_cuisines are provided and n >= 2, at least
    one result will be from a preferred cuisine when such recipes exist in the pool.
    For n=1 (breakfast), a preferred-cuisine recipe is chosen if available.
    """
    exclude_ids = exclude_ids or set()
    pref = preferred_cuisines or []

    cat_pool = [
        r for r in pool
        if r.get("category", "").lower() == category.lower()
        and r.get("id") not in exclude_ids
    ]

    candidates = [
        r for r in cat_pool
        if abs(r.get("calories", 0) - target_kcal) / max(target_kcal, 1) <= tolerance
    ]

    if len(candidates) < n:
        candidates = cat_pool

    if not candidates:
        return []

    candidates.sort(key=lambda r: r.get("_score", 0), reverse=True)
    top = candidates[: max(n * 3, len(candidates) // 2 + 1)]
    results = random.sample(top, min(n, len(top)))

    # ── Cuisine guarantee ──────────────────────────────────────────────────
    if pref:
        already_pref = any(_cuisine_matches(r.get("cuisine", ""), pref) for r in results)
        if not already_pref:
            # Find a preferred-cuisine candidate not already selected
            selected_ids = {r.get("id") for r in results}
            pref_candidates = [
                r for r in cat_pool
                if _cuisine_matches(r.get("cuisine", ""), pref)
                and r.get("id") not in selected_ids
            ]
            if pref_candidates:
                pref_candidates.sort(key=lambda r: r.get("_score", 0), reverse=True)
                pref_pick = pref_candidates[0]
                if len(results) >= 2:
                    results[-1] = pref_pick   # replace lowest-priority slot
                else:
                    results = [pref_pick]     # for n=1 slots (breakfast)

    return results


def _count_treat_meals(day_plan: dict) -> int:
    """Count how many treat_meal=True recipes appear across a single day's slots."""
    return sum(
        1 for slot in ("breakfast", "lunch", "dinner", "snack")
        for r in day_plan.get(slot, [])
        if r.get("treat_meal")
    )


def _replace_treat(
    recipe: dict,
    pool: list[dict],
    category: str,
    target_kcal: float,
    exclude_ids: set,
) -> dict:
    """Return a non-treat alternative for recipe, or the original if none found."""
    non_treat = [
        r for r in pool
        if r.get("category", "").lower() == category
        and not r.get("treat_meal")
        and r.get("id") not in exclude_ids
        and r.get("id") != recipe.get("id")
    ]
    if not non_treat:
        return recipe
    non_treat.sort(key=lambda r: r.get("_score", 0), reverse=True)
    return random.choice(non_treat[: max(1, len(non_treat) // 2)])


def generate_meal_plan(
    client: dict,
    assessment: dict,
    days: int = 7,
    seed: Optional[int] = None,
) -> dict:
    """
    Generate a day-by-day meal plan.

    Respects meal_frequency and meal_slots:
      - meal_slots controls which of Breakfast / Lunch / Dinner are included
        (e.g. ["Lunch", "Dinner"] for a 2-meal client who skips breakfast)
      - snacks = meal_freq - 3, capped at 0 minimum
    """
    if seed is not None:
        random.seed(seed)

    target_kcal = assessment.get("target_calories", 1800)
    meal_freq   = int(client.get("meal_frequency", 3) or 3)
    snack_count = max(0, meal_freq - 3)

    # Which main meal slots to generate
    _default_slots = ["Breakfast", "Lunch", "Dinner"]
    meal_slots = client.get("meal_slots") or _default_slots
    if not meal_slots:
        meal_slots = _default_slots
    use_breakfast = "Breakfast" in meal_slots
    use_lunch     = "Lunch"     in meal_slots
    use_dinner    = "Dinner"    in meal_slots

    # If calorie budget is constrained to fewer meals, redistribute proportionally
    active_slots = [s for s in ["Breakfast", "Lunch", "Dinner"] if s in meal_slots]
    _dist = {k: v for k, v in MEAL_DISTRIBUTION.items() if k in meal_slots}
    _total_dist = sum(_dist.values()) or 1
    # Scale targets so skipped meals' calories go to the remaining slots
    _scale = 1 / _total_dist

    b_target = target_kcal * MEAL_DISTRIBUTION["Breakfast"] * _scale if use_breakfast else 0
    l_target = target_kcal * MEAL_DISTRIBUTION["Lunch"]     * _scale if use_lunch     else 0
    d_target = target_kcal * MEAL_DISTRIBUTION["Dinner"]    * _scale if use_dinner    else 0
    s_budget = target_kcal * MEAL_DISTRIBUTION["Snack"]
    s_target = s_budget / max(snack_count, 1)

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

    def _pool_size(cat):
        return len([r for r in filtered if r.get("category", "").lower() == cat])

    for i in range(days):
        day = days_of_week[i % 7]

        breakfast, snacks = [], []
        _pref_cuisines = client.get("cuisine_pref") or []

        if use_breakfast:
            breakfast = pick_recipes(filtered, "breakfast", b_target, n=1,
                                     exclude_ids=used_breakfast,
                                     preferred_cuisines=_pref_cuisines)
        lunch  = pick_recipes(filtered, "lunch",  l_target, n=2, exclude_ids=used_lunch,
                              preferred_cuisines=_pref_cuisines)  if use_lunch  else []
        dinner = pick_recipes(filtered, "dinner", d_target, n=2, exclude_ids=used_dinner,
                              preferred_cuisines=_pref_cuisines) if use_dinner else []
        if snack_count >= 1:
            snacks = pick_recipes(filtered, "snack", s_target, n=snack_count,
                                  exclude_ids=used_snack,
                                  preferred_cuisines=_pref_cuisines)

        # ── Treat-meal cap: max 1 treat per day ───────────────────────────
        # Check all picked slots and replace extras (lower-priority slots first)
        _day_draft = {"breakfast": breakfast, "lunch": lunch,
                      "dinner": dinner, "snack": snacks}
        _all_used  = ({r["id"] for r in breakfast} | {r["id"] for r in lunch}
                      | {r["id"] for r in dinner}  | {r["id"] for r in snacks})
        _treat_found = False
        for _slot in ("breakfast", "lunch", "dinner", "snack"):
            _slot_recipes = _day_draft[_slot]
            for _idx, _r in enumerate(_slot_recipes):
                if _r.get("treat_meal"):
                    if _treat_found:
                        # Already have one treat today — swap this one out
                        _replacement = _replace_treat(
                            _r, filtered, _slot, {
                                "breakfast": b_target, "lunch": l_target,
                                "dinner": d_target, "snack": s_target,
                            }.get(_slot, d_target),
                            _all_used - {_r["id"]},
                        )
                        _slot_recipes[_idx] = _replacement
                    else:
                        _treat_found = True
        breakfast = _day_draft["breakfast"]
        lunch     = _day_draft["lunch"]
        dinner    = _day_draft["dinner"]
        snacks    = _day_draft["snack"]

        for r in breakfast: used_breakfast.add(r["id"])
        for r in lunch:     used_lunch.add(r["id"])
        for r in dinner:    used_dinner.add(r["id"])
        for r in snacks:    used_snack.add(r["id"])

        if len(used_breakfast) >= _pool_size("breakfast"):
            used_breakfast.clear()
        if len(used_lunch) >= _pool_size("lunch"):
            used_lunch.clear()
        if len(used_dinner) >= _pool_size("dinner"):
            used_dinner.clear()
        if len(used_snack) >= _pool_size("snack"):
            used_snack.clear()

        plan[day] = {
            "breakfast": breakfast,
            "lunch":     lunch,
            "dinner":    dinner,
            "snack":     snacks,
        }

    return plan


def plan_daily_totals(day_plan: dict) -> dict:
    """
    Estimate kcal/macros for a single day using option A for lunch/dinner
    and counting all snack slots.
    """
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    slots = (
        day_plan.get("breakfast", [])[:1]
        + day_plan.get("lunch", [])[:1]
        + day_plan.get("dinner", [])[:1]
        + day_plan.get("snack", [])           # all snack slots
    )
    for r in slots:
        totals["calories"]  += r.get("calories", 0)
        totals["protein_g"] += r.get("protein_g", 0)
        totals["carbs_g"]   += r.get("carbs_g", 0)
        totals["fat_g"]     += r.get("fat_g", 0)
    return {k: round(v, 1) for k, v in totals.items()}


def build_grocery_list(plan: dict) -> dict:
    """
    Aggregate key ingredients from all option-A meals in the 7-day plan.
    Returns a dict grouped by: Produce, Grains & Legumes, Protein, Dairy & Eggs, Pantry.
    """
    from collections import Counter

    PRODUCE_KW = {
        "spinach","palak","paalungo","tomato","onion","garlic","ginger","carrot",
        "potato","aloo","cauliflower","gobi","cabbage","capsicum","pumpkin",
        "mushroom","broccoli","cucumber","eggplant","baingan","bitter gourd",
        "bottle gourd","lauki","radish","asparagus","bok choy","napa cabbage",
        "lotus root","fiddlehead","okra","bhindi","yam","corn","makai","peas",
        "beans","banana","papaya","mango","apple","strawberry","blueberry",
        "lemon","lime","coriander","cilantro","fenugreek","methi","spring onion",
        "seasonal fruit","fruit","apple","watermelon","guava","orange",
    }
    GRAIN_KW = {
        "rice","bhat","chiura","beaten rice","roti","bread","oats","oatmeal",
        "wheat","atta","noodles","pasta","quinoa","millet","kodo","brown rice",
        "dhido","flour","chowmein","phaapar","buckwheat",
    }
    PROTEIN_KW = {
        "chicken","buff","buffalo","mutton","goat","fish","prawn","shrimp",
        "egg","eggs","tofu","soya","soybean","paneer","dal","lentil","lentils",
        "chana","chickpea","moong","kwati","black lentil","masoor","rajma",
        "kidney bean","bhatmas","wonton",
    }
    DAIRY_KW = {
        "dahi","yogurt","milk","ghee","butter","cream","cheese","curd",
    }

    counter: Counter = Counter()
    for day_plan in plan.values():
        for slot in ("breakfast","lunch","dinner","snack"):
            for r in day_plan.get(slot, [])[:1]:
                for ing in r.get("key_ingredients", []):
                    counter[ing.lower()] += 1

    grouped: dict = {
        "Produce & Vegetables": [],
        "Grains, Legumes & Carbs": [],
        "Protein Sources": [],
        "Dairy & Eggs": [],
        "Pantry & Spices": [],
    }

    seen: set = set()
    for ing, cnt in counter.most_common():
        if ing in seen:
            continue
        seen.add(ing)
        label = ing.title() + (f" (×{cnt})" if cnt > 1 else "")

        matched = False
        for kw in PRODUCE_KW:
            if kw in ing:
                grouped["Produce & Vegetables"].append(label)
                matched = True
                break
        if not matched:
            for kw in GRAIN_KW:
                if kw in ing:
                    grouped["Grains, Legumes & Carbs"].append(label)
                    matched = True
                    break
        if not matched:
            for kw in PROTEIN_KW:
                if kw in ing:
                    grouped["Protein Sources"].append(label)
                    matched = True
                    break
        if not matched:
            for kw in DAIRY_KW:
                if kw in ing:
                    grouped["Dairy & Eggs"].append(label)
                    matched = True
                    break
        if not matched:
            grouped["Pantry & Spices"].append(label)

    return {k: sorted(v) for k, v in grouped.items() if v}


def swap_single_recipe(
    plan: dict,
    day: str,
    slot: str,
    position: int,
    client: dict,
    assessment: dict,
) -> dict:
    """
    Replace one recipe in the plan with a different valid alternative.

    Args:
        plan:       The full 7-day plan dict (will be mutated in place).
        day:        e.g. "Monday"
        slot:       "breakfast" | "lunch" | "dinner" | "snack"
        position:   Index within the slot's recipe list (0 = option A, 1 = option B)
        client:     Full client dict
        assessment: Full assessment dict

    Returns the modified plan.
    """
    from utils.calculations import MEAL_DISTRIBUTION

    # Collect all recipe IDs already in the plan (to avoid repeats)
    used_ids: set = set()
    for _day, _dp in plan.items():
        for _slot, _recipes in _dp.items():
            for _r in _recipes:
                if _r:
                    used_ids.add(_r.get("id"))

    # Target kcal for the slot
    target_kcal = assessment.get("target_calories", 1800)
    _dist = MEAL_DISTRIBUTION
    slot_targets = {
        "breakfast": target_kcal * _dist["Breakfast"],
        "lunch":     target_kcal * _dist["Lunch"],
        "dinner":    target_kcal * _dist["Dinner"],
        "snack":     target_kcal * _dist["Snack"],
    }
    slot_target = slot_targets.get(slot, target_kcal * 0.3)

    # Category mapping
    cat_map = {"breakfast": "breakfast", "lunch": "lunch",
               "dinner": "dinner", "snack": "snack"}
    category = cat_map.get(slot, slot)

    # Current recipe id to exclude
    current_slot = plan[day].get(slot, [])
    current_id = current_slot[position].get("id") if position < len(current_slot) else None
    if current_id:
        used_ids.discard(current_id)  # allow swapping back in edge cases

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

    alternatives = pick_recipes(
        filtered, category, slot_target, n=1,
        exclude_ids=used_ids | ({current_id} if current_id else set()),
    )

    # Fall back without the used-IDs constraint if nothing found
    if not alternatives:
        alternatives = pick_recipes(
            filtered, category, slot_target, n=1,
            exclude_ids={current_id} if current_id else set(),
        )

    if alternatives:
        plan[day][slot][position] = alternatives[0]

    return plan


def snack_swap_suggestions(client: dict) -> list[dict]:
    """Return 5 healthy snack alternatives from the recipe library."""
    all_recipes = load_recipes()
    snacks = [
        r for r in all_recipes
        if r.get("category", "").lower() == "snack"
        and not r.get("is_side_dish")
    ]
    diet = client.get("diet_type", "Non-vegetarian")
    if diet in ("Vegetarian", "Vegan", "Eggetarian"):
        snacks = [
            r for r in snacks
            if "vegetarian" in [t.lower() for t in r.get("dietary_tags", [])]
        ]
    random.shuffle(snacks)
    return snacks[:5]
