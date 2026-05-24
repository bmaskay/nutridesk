"""
personalization.py — Auto-selects exercises, guidelines, snacks & avoid items
based on a client's profile (conditions, fitness level, lifestyle, diet type).

Usage:
    from utils.personalization import build_personalized_plan
    plan = build_personalized_plan(client)
    # Returns dict with keys: exercises, guidelines, avoid_items, snacks
"""

from utils.personalization_library import (
    EXERCISES, LIFESTYLE_GUIDELINES, AVOID_ITEMS, SNACK_OPTIONS
)

# Map intake form condition strings to library condition keys
_CONDITION_MAP = {
    "pcos": "pcos",
    "pcod": "pcos",
    "type 2 diabetes": "diabetes",
    "type 1 diabetes": "diabetes",
    "diabetes": "diabetes",
    "pre-diabetes": "prediabetes",
    "prediabetes": "prediabetes",
    "hypothyroidism": "hypothyroidism",
    "hyperthyroidism": "hyperthyroidism",
    "thyroid": "hypothyroidism",  # default to hypo if unspecified
    "hypertension": "hypertension",
    "high blood pressure": "hypertension",
    "fatty liver": "fatty_liver",
    "nafld": "fatty_liver",
    "ibs": "ibs",
    "irritable bowel": "ibs",
    "knee pain": "knee_pain",
    "knee issues": "knee_pain",
    "back pain": "back_pain",
    "lower back pain": "back_pain",
    "obesity": "obesity",
    "postpartum": "postpartum",
    "post partum": "postpartum",
    "elderly": "elderly",
}

# Map fitness_level from intake form
_LEVEL_MAP = {
    "beginner": "Beginner",
    "moderate": "Moderate",
    "advanced": "Advanced",
}

# Lifestyle type detection from exercise_notes and occupation fields
_LIFESTYLE_KEYWORDS = {
    "sedentary": ["sedentary", "no exercise", "inactive", "couch"],
    "desk_job": ["desk", "office", "wfh", "work from home", "sitting", "computer"],
    "physical_job": ["nurse", "teacher", "construction", "factory", "standing", "labour", "labourer", "shop"],
    "very_active": ["gym", "athlete", "sport", "training", "crossfit", "5 days", "6 days"],
    "moderately_active": ["walk", "yoga", "3 days", "4 days", "exercise"],
    "postpartum": ["postpartum", "post partum", "delivery", "new mom", "nursing", "breastfeed"],
    "elderly": ["senior", "elderly", "retired", "60", "65", "70", "75", "80"],
}


def _parse_conditions(client: dict) -> list[str]:
    """Normalise the client's medical_conditions list to library keys."""
    raw = client.get("medical_conditions") or []
    if isinstance(raw, str):
        try:
            import json
            raw = json.loads(raw)
        except Exception:
            raw = [raw]
    keys = set()
    for c in raw:
        c_lower = c.lower().strip()
        for keyword, key in _CONDITION_MAP.items():
            if keyword in c_lower:
                keys.add(key)
    return list(keys)


def _parse_lifestyle(client: dict) -> str:
    """Infer a lifestyle type from exercise_notes and occupation."""
    text = " ".join([
        (client.get("exercise_notes") or ""),
        (client.get("occupation") or ""),
        (client.get("lifestyle") or ""),
    ]).lower()

    # Check explicit lifestyle field first
    lifestyle_field = (client.get("lifestyle") or "").lower()
    if "sedentary" in lifestyle_field:
        return "sedentary"
    if "very active" in lifestyle_field or "highly active" in lifestyle_field:
        return "very_active"
    if "moderately" in lifestyle_field:
        return "moderately_active"
    if "lightly" in lifestyle_field:
        return "lightly_active"

    for lifestyle_type, keywords in _LIFESTYLE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return lifestyle_type

    # Fallback: use fitness_level as proxy
    fitness = (client.get("fitness_level") or "Moderate").lower()
    if fitness == "beginner":
        return "lightly_active"
    if fitness == "advanced":
        return "moderately_active"
    return "lightly_active"


def build_default_exercises(client: dict) -> list[dict]:
    """
    Auto-select a balanced circuit of exercises for the client.
    Returns list of exercise dicts with an added 'active_reps' key.
    """
    conditions = _parse_conditions(client)
    lifestyle = _parse_lifestyle(client)
    fitness_level = _LEVEL_MAP.get(
        (client.get("fitness_level") or "Moderate").lower(), "Moderate"
    )

    # Filter out exercises the client should avoid
    available = []
    for ex in EXERCISES:
        should_avoid = any(c in conditions for c in ex.get("avoid_if", []))
        if not should_avoid:
            available.append(ex)

    # Score exercises — prefer ones that are good for the client's conditions/lifestyle
    def score(ex):
        s = 0
        for c in conditions:
            if c in ex.get("good_for", []):
                s += 3
        if lifestyle in ex.get("lifestyle_priority", []):
            s += 2
        if "all" in ex.get("lifestyle_priority", []):
            s += 1
        return s

    available.sort(key=score, reverse=True)

    # Build a balanced circuit: aim for ~2 cardio, ~4 core, ~2 strength, ~2 flexibility
    targets = {"cardio": 2, "core": 4, "strength": 2, "flexibility": 2}
    selected = []
    counts = {cat: 0 for cat in targets}

    for ex in available:
        cat = ex["category"]
        if cat in targets and counts[cat] < targets[cat]:
            # Resolve reps for the fitness level
            reps_val = ex["reps"].get(fitness_level, ex["reps"].get("Moderate"))
            unit = ex["unit"]
            if unit == "reps":
                reps_str = f"{reps_val} reps"
            else:
                reps_str = str(reps_val)

            entry = dict(ex)
            entry["active_reps"] = reps_str
            entry["active_level"] = fitness_level
            selected.append(entry)
            counts[cat] += 1

        if all(counts[c] >= targets[c] for c in targets):
            break

    return selected


def build_default_guidelines(client: dict) -> list[dict]:
    """Auto-select relevant lifestyle guidelines for the client."""
    conditions = _parse_conditions(client)
    lifestyle = _parse_lifestyle(client)

    selected = []
    for g in LIFESTYLE_GUIDELINES:
        cond_match = (
            not g["conditions"] or  # applies to everyone
            any(c in conditions for c in g["conditions"])
        )
        lifestyle_match = (
            not g["lifestyle_tags"] or  # applies to everyone
            lifestyle in g["lifestyle_tags"]
        )
        if cond_match and lifestyle_match:
            selected.append(dict(g))

    return selected


def build_default_avoid_items(client: dict) -> list[str]:
    """
    Build a personalised avoid list.
    Returns a flat list of avoid item name strings.
    """
    conditions = _parse_conditions(client)
    diet_type = client.get("diet_type") or ""

    avoid = []
    for item in AVOID_ITEMS:
        # Skip if already excluded by diet type (e.g., vegetarians don't need 'avoid meat')
        if diet_type in item.get("diet_exclude", []):
            continue
        # Include if it's a universal item or matches a condition
        if not item["conditions"] or any(c in conditions for c in item["conditions"]):
            avoid.append(item["name"])

    return avoid


def build_default_snacks(client: dict) -> list[dict]:
    """Auto-select relevant snack options for the client."""
    conditions = _parse_conditions(client)
    diet_type = client.get("diet_type") or ""
    is_veg = diet_type in ("Vegetarian", "Vegan", "Eggetarian")

    scored = []
    for snack in SNACK_OPTIONS:
        # Skip non-veg snacks for vegetarians
        if is_veg and not snack["veg"]:
            continue

        score = 0
        for c in conditions:
            if c in snack.get("conditions", []):
                score += 2
        if not snack["conditions"]:
            score += 1  # universal snacks get a base score

        scored.append((score, snack))

    scored.sort(key=lambda x: x[0], reverse=True)
    # Return top 8 snacks
    return [dict(s) for _, s in scored[:8]]


def build_personalized_plan(client: dict) -> dict:
    """
    Build a full personalised plan for the client.
    Returns:
        {
            "exercises": [...],
            "guidelines": [...],
            "avoid_items": [...],   # list of strings
            "snacks": [...],
        }
    """
    return {
        "exercises": build_default_exercises(client),
        "guidelines": build_default_guidelines(client),
        "avoid_items": build_default_avoid_items(client),
        "snacks": build_default_snacks(client),
    }
