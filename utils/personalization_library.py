"""
personalization_library.py — Tagged library for client personalisation
Exercises, lifestyle guidelines, avoid items, and snack swaps.
All items are tagged by condition, lifestyle type, and diet type.
"""

CONDITIONS = [
    "pcos", "diabetes", "prediabetes", "hypothyroidism", "hyperthyroidism",
    "hypertension", "fatty_liver", "ibs", "knee_pain", "back_pain",
    "obesity", "postpartum", "elderly",
]

LIFESTYLE_TYPES = [
    "sedentary", "desk_job", "lightly_active", "moderately_active",
    "very_active", "physical_job", "elderly", "postpartum",
]

EXERCISES = [
    # ── Cardio ──
    {"name": "Jumping Jacks", "category": "cardio",
     "reps": {"Beginner": 30, "Moderate": 40, "Advanced": 50}, "unit": "reps",
     "good_for": ["weight_loss", "pcos", "diabetes", "hypothyroidism"],
     "avoid_if": ["knee_pain", "back_pain", "postpartum"],
     "modification": "March in place with high knees instead — same cardio benefit, zero joint impact",
     "modification_for": ["knee_pain", "postpartum"],
     "lifestyle_priority": ["sedentary", "desk_job"]},

    {"name": "Marching in Place", "category": "cardio",
     "reps": {"Beginner": 40, "Moderate": 60, "Advanced": 80}, "unit": "reps",
     "good_for": ["knee_pain", "hypertension", "elderly", "postpartum", "diabetes"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["sedentary", "desk_job", "elderly", "postpartum"]},

    {"name": "Skipping (Jump Rope)", "category": "cardio",
     "reps": {"Beginner": 200, "Moderate": 350, "Advanced": 500}, "unit": "reps",
     "good_for": ["weight_loss", "pcos", "hypothyroidism", "fatty_liver"],
     "avoid_if": ["knee_pain", "back_pain", "postpartum"],
     "modification": "Step-overs with the rope touching the ground instead of jumping",
     "modification_for": ["knee_pain"],
     "lifestyle_priority": ["moderately_active", "very_active"]},

    {"name": "Step Touch (Side to Side)", "category": "cardio",
     "reps": {"Beginner": 30, "Moderate": 50, "Advanced": 70}, "unit": "reps",
     "good_for": ["elderly", "knee_pain", "postpartum", "hypertension"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["sedentary", "elderly", "postpartum"]},

    {"name": "High Knees", "category": "cardio",
     "reps": {"Beginner": 20, "Moderate": 30, "Advanced": 40}, "unit": "reps",
     "good_for": ["weight_loss", "pcos", "diabetes", "fatty_liver"],
     "avoid_if": ["knee_pain", "back_pain", "postpartum"],
     "modification": "Slow marching with deliberate knee lift instead",
     "modification_for": ["knee_pain"],
     "lifestyle_priority": ["moderately_active", "very_active"]},

    {"name": "Spot Jogging", "category": "cardio",
     "reps": {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}, "unit": "duration",
     "good_for": ["weight_loss", "diabetes", "pcos", "hypothyroidism"],
     "avoid_if": ["knee_pain", "back_pain", "postpartum"],
     "modification": "Brisk marching in place instead",
     "modification_for": ["knee_pain"],
     "lifestyle_priority": ["desk_job", "lightly_active"]},

    {"name": "Calf Raises", "category": "cardio",
     "reps": {"Beginner": 12, "Moderate": 15, "Advanced": 20}, "unit": "reps",
     "good_for": ["diabetes", "elderly", "desk_job", "sedentary", "hypertension"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["desk_job", "elderly", "sedentary"]},

    # ── Core ──
    {"name": "Crunches", "category": "core",
     "reps": {"Beginner": 8, "Moderate": 10, "Advanced": 12}, "unit": "reps",
     "good_for": ["weight_loss", "pcos", "fatty_liver"],
     "avoid_if": ["back_pain", "postpartum"],
     "modification": "Dead bug instead — lying on back, extend opposite arm and leg alternately",
     "modification_for": ["back_pain", "postpartum"],
     "lifestyle_priority": ["all"]},

    {"name": "Leg Raise", "category": "core",
     "reps": {"Beginner": 8, "Moderate": 10, "Advanced": 12}, "unit": "reps",
     "good_for": ["weight_loss", "pcos"],
     "avoid_if": ["back_pain", "postpartum"],
     "modification": "Bent knee leg raise — same core work, less spinal load",
     "modification_for": ["back_pain"],
     "lifestyle_priority": ["all"]},

    {"name": "Oblique Crunches (Elbow to Knee)", "category": "core",
     "reps": {"Beginner": 8, "Moderate": 10, "Advanced": 12}, "unit": "reps",
     "good_for": ["weight_loss", "pcos"],
     "avoid_if": ["back_pain", "postpartum"],
     "modification": "Side-lying hip abduction — lie on side, lift top leg 45 degrees",
     "modification_for": ["back_pain", "postpartum"],
     "lifestyle_priority": ["all"]},

    {"name": "Russian Twist", "category": "core",
     "reps": {"Beginner": 8, "Moderate": 10, "Advanced": 12}, "unit": "reps",
     "good_for": ["weight_loss", "pcos"],
     "avoid_if": ["back_pain", "postpartum", "ibs"],
     "modification": "Seated torso rotation without leaning back",
     "modification_for": ["back_pain"],
     "lifestyle_priority": ["all"]},

    {"name": "Plank", "category": "core",
     "reps": {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}, "unit": "duration",
     "good_for": ["weight_loss", "pcos", "back_pain", "fatty_liver"],
     "avoid_if": ["postpartum"],
     "modification": "Knee plank — same hold, weight on knees not toes",
     "modification_for": ["postpartum", "back_pain"],
     "lifestyle_priority": ["all"]},

    {"name": "Bicycle Crunches", "category": "core",
     "reps": {"Beginner": 8, "Moderate": 10, "Advanced": 12}, "unit": "reps",
     "good_for": ["weight_loss", "pcos"],
     "avoid_if": ["back_pain", "postpartum", "knee_pain"],
     "modification": "Slow alternating leg extension lying flat",
     "modification_for": ["back_pain"],
     "lifestyle_priority": ["all"]},

    {"name": "Heel Touch", "category": "core",
     "reps": {"Beginner": 8, "Moderate": 10, "Advanced": 12}, "unit": "reps",
     "good_for": ["weight_loss", "back_pain"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["all"]},

    {"name": "Leg Straight Hold", "category": "core",
     "reps": {"Beginner": "45 sec", "Moderate": "45 sec", "Advanced": "1 min"}, "unit": "duration",
     "good_for": ["weight_loss"],
     "avoid_if": ["back_pain"],
     "modification": "Bent knee hold instead",
     "modification_for": ["back_pain"],
     "lifestyle_priority": ["all"]},

    {"name": "Bird Dog", "category": "core",
     "reps": {"Beginner": 6, "Moderate": 8, "Advanced": 10}, "unit": "reps",
     "good_for": ["back_pain", "elderly", "postpartum", "hypertension"],
     "avoid_if": ["knee_pain"], "modification": None, "modification_for": [],
     "lifestyle_priority": ["elderly", "postpartum"]},

    {"name": "Dead Bug", "category": "core",
     "reps": {"Beginner": 6, "Moderate": 8, "Advanced": 10}, "unit": "reps",
     "good_for": ["back_pain", "postpartum", "elderly"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["postpartum", "elderly"]},

    # ── Strength ──
    {"name": "Bodyweight Squat", "category": "strength",
     "reps": {"Beginner": 8, "Moderate": 12, "Advanced": 15}, "unit": "reps",
     "good_for": ["weight_loss", "pcos", "diabetes", "fatty_liver"],
     "avoid_if": ["knee_pain"],
     "modification": "Wall squat — back against wall, slide down to 90 degrees",
     "modification_for": ["knee_pain"],
     "lifestyle_priority": ["all"]},

    {"name": "Wall Squat", "category": "strength",
     "reps": {"Beginner": "20 sec", "Moderate": "30 sec", "Advanced": "45 sec"}, "unit": "duration",
     "good_for": ["knee_pain", "elderly", "diabetes", "hypertension", "postpartum"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["elderly", "sedentary", "postpartum"]},

    {"name": "Glute Bridge", "category": "strength",
     "reps": {"Beginner": 10, "Moderate": 12, "Advanced": 15}, "unit": "reps",
     "good_for": ["knee_pain", "back_pain", "postpartum", "pcos", "elderly"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["postpartum", "elderly", "sedentary"]},

    {"name": "Push-Up", "category": "strength",
     "reps": {"Beginner": 5, "Moderate": 8, "Advanced": 12}, "unit": "reps",
     "good_for": ["weight_loss", "pcos", "fatty_liver"],
     "avoid_if": ["back_pain", "postpartum"],
     "modification": "Knee push-up — same movement, reduced load",
     "modification_for": ["back_pain", "postpartum"],
     "lifestyle_priority": ["moderately_active", "very_active"]},

    {"name": "Knee Push-Up", "category": "strength",
     "reps": {"Beginner": 5, "Moderate": 8, "Advanced": 10}, "unit": "reps",
     "good_for": ["weight_loss", "elderly", "postpartum"],
     "avoid_if": ["back_pain"],
     "modification": "Wall push-up instead",
     "modification_for": ["back_pain"],
     "lifestyle_priority": ["sedentary", "elderly", "postpartum"]},

    {"name": "Reverse Lunge", "category": "strength",
     "reps": {"Beginner": 6, "Moderate": 8, "Advanced": 10}, "unit": "reps",
     "good_for": ["weight_loss", "pcos", "diabetes"],
     "avoid_if": ["knee_pain", "back_pain"],
     "modification": "Step back without fully lowering the knee",
     "modification_for": ["knee_pain"],
     "lifestyle_priority": ["moderately_active"]},

    {"name": "Chair Squat (Sit to Stand)", "category": "strength",
     "reps": {"Beginner": 8, "Moderate": 10, "Advanced": 12}, "unit": "reps",
     "good_for": ["elderly", "knee_pain", "sedentary", "diabetes"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["elderly", "sedentary"]},

    # ── Flexibility ──
    {"name": "Cat-Cow Stretch", "category": "flexibility",
     "reps": {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}, "unit": "duration",
     "good_for": ["back_pain", "ibs", "postpartum", "elderly", "desk_job"],
     "avoid_if": ["knee_pain"],
     "modification": "Seated version on a chair — same spinal movement",
     "modification_for": ["knee_pain"],
     "lifestyle_priority": ["desk_job", "elderly", "postpartum"]},

    {"name": "Child's Pose", "category": "flexibility",
     "reps": {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}, "unit": "duration",
     "good_for": ["back_pain", "hypertension", "ibs", "pcos"],
     "avoid_if": ["knee_pain"],
     "modification": "Extended puppy pose — hips stay above knees",
     "modification_for": ["knee_pain"],
     "lifestyle_priority": ["desk_job", "physical_job"]},

    {"name": "Neck Rolls & Shoulder Circles", "category": "flexibility",
     "reps": {"Beginner": "30 sec", "Moderate": "45 sec", "Advanced": "1 min"}, "unit": "duration",
     "good_for": ["desk_job", "hypertension", "elderly"],
     "avoid_if": [], "modification": None, "modification_for": [],
     "lifestyle_priority": ["desk_job"]},

    {"name": "Supine Spinal Twist", "category": "flexibility",
     "reps": {"Beginner": "20 sec", "Moderate": "30 sec", "Advanced": "45 sec"}, "unit": "duration",
     "good_for": ["back_pain", "ibs", "pcos"],
     "avoid_if": ["postpartum"], "modification": None, "modification_for": [],
     "lifestyle_priority": ["desk_job", "physical_job"]},

    {"name": "Standing Quad Stretch", "category": "flexibility",
     "reps": {"Beginner": "20 sec", "Moderate": "30 sec", "Advanced": "45 sec"}, "unit": "duration",
     "good_for": ["knee_pain", "elderly", "physical_job"],
     "avoid_if": [],
     "modification": "Hold a wall for balance",
     "modification_for": ["elderly"],
     "lifestyle_priority": ["physical_job", "elderly"]},
]


LIFESTYLE_GUIDELINES = [
    # Always-on
    {"icon": "💧", "text": "Drink at least 2–3 litres of water daily. Start your morning with 2 glasses of warm water before anything else.", "highlight": True, "conditions": [], "lifestyle_tags": []},
    {"icon": "🥗", "text": "Eat slowly and chew your food very well — at least 20–30 times per bite. This aids digestion and prevents overeating.", "highlight": False, "conditions": [], "lifestyle_tags": []},
    {"icon": "⏰", "text": "Stick to fixed meal timings every day. Consistent eating windows support metabolism and hormonal balance.", "highlight": False, "conditions": [], "lifestyle_tags": []},
    {"icon": "😴", "text": "7–8 hours of quality sleep every night is non-negotiable. Poor sleep undermines fat loss, immunity, and hormonal health regardless of diet.", "highlight": True, "conditions": [], "lifestyle_tags": []},
    {"icon": "📱", "text": "No screens for at least 30 minutes before bedtime — blue light suppresses melatonin and ruins sleep quality.", "highlight": False, "conditions": [], "lifestyle_tags": []},
    {"icon": "🌙", "text": "Finish dinner 2–3 hours before bedtime to allow proper digestion and avoid night-time fat storage.", "highlight": False, "conditions": [], "lifestyle_tags": []},
    {"icon": "⏱️", "text": "Keep fixed sleeping and waking times every day — including weekends. Circadian consistency matters as much as sleep duration.", "highlight": False, "conditions": [], "lifestyle_tags": []},
    {"icon": "🌅", "text": "Get 15–20 minutes of natural sunlight daily (morning preferred) to support Vitamin D synthesis and set your circadian clock.", "highlight": False, "conditions": [], "lifestyle_tags": []},
    {"icon": "🛢️", "text": "Use only 3–4 tsp of good fat per day total — cold-pressed mustard oil, ghee, or olive oil. Always use a non-stick pan.", "highlight": False, "conditions": [], "lifestyle_tags": []},
    {"icon": "🚶", "text": "Walk for 10–15 minutes after every major meal. Even a short walk significantly blunts blood sugar spikes and aids digestion.", "highlight": True, "conditions": [], "lifestyle_tags": []},

    # PCOS
    {"icon": "🌀", "text": "PCOS: Consistency in sleep timing and stress management is critical — cortisol spikes directly worsen insulin resistance and hormonal imbalance.", "highlight": True, "conditions": ["pcos"], "lifestyle_tags": []},
    {"icon": "🧘", "text": "PCOS: Include 10 minutes of yoga, deep breathing, or meditation daily. Chronic stress elevates androgens and worsens PCOS symptoms.", "highlight": False, "conditions": ["pcos"], "lifestyle_tags": []},
    {"icon": "🍬", "text": "PCOS: Never skip meals — low blood sugar triggers cortisol release which directly worsens hormonal imbalance and drives cravings.", "highlight": False, "conditions": ["pcos"], "lifestyle_tags": []},
    {"icon": "☕", "text": "PCOS: Limit coffee to 1 cup per day. Excess caffeine raises cortisol and disrupts insulin sensitivity.", "highlight": False, "conditions": ["pcos"], "lifestyle_tags": []},
    {"icon": "🌿", "text": "PCOS: Include anti-inflammatory spices daily — turmeric, ginger, and cinnamon. Add to meals, warm water, or tea.", "highlight": False, "conditions": ["pcos"], "lifestyle_tags": []},

    # Diabetes
    {"icon": "🍽️", "text": "Diabetes: Never skip meals — fasting causes blood sugar to drop, then spike sharply at the next meal. Eat every 3–4 hours.", "highlight": True, "conditions": ["diabetes", "prediabetes"], "lifestyle_tags": []},
    {"icon": "🚶", "text": "Diabetes: Walk within 15 minutes of finishing a meal — even 10 minutes measurably reduces post-meal glucose spikes.", "highlight": True, "conditions": ["diabetes", "prediabetes"], "lifestyle_tags": []},
    {"icon": "📊", "text": "Diabetes: Track blood sugar at consistent times — fasting and 2 hours post-meal. Bring your log to every consultation.", "highlight": False, "conditions": ["diabetes"], "lifestyle_tags": []},
    {"icon": "👣", "text": "Diabetes: Check your feet daily for cuts, blisters, or skin changes — diabetic neuropathy reduces sensation and wounds can go unnoticed.", "highlight": False, "conditions": ["diabetes"], "lifestyle_tags": []},

    # Hypothyroidism
    {"icon": "💊", "text": "Thyroid (Hypo): Take thyroid medication on an empty stomach, 30–60 minutes before breakfast — every single day without exception.", "highlight": True, "conditions": ["hypothyroidism"], "lifestyle_tags": []},
    {"icon": "☕", "text": "Thyroid (Hypo): Avoid coffee, calcium, or iron supplements within 4 hours of taking thyroid medication — they significantly reduce absorption.", "highlight": False, "conditions": ["hypothyroidism"], "lifestyle_tags": []},
    {"icon": "🥦", "text": "Thyroid (Hypo): Eat cruciferous vegetables cooked, not raw. Limit to 2–3 times per week — raw cabbage, cauliflower, and broccoli in large amounts can suppress thyroid function.", "highlight": False, "conditions": ["hypothyroidism"], "lifestyle_tags": []},
    {"icon": "🌊", "text": "Thyroid (Hypo): Use iodised salt. Include selenium-rich foods weekly — sunflower seeds, lentils, brown rice, and walnuts.", "highlight": False, "conditions": ["hypothyroidism"], "lifestyle_tags": []},

    # Hyperthyroidism
    {"icon": "🧂", "text": "Thyroid (Hyper): Avoid excess iodine — limit seaweed, iodised salt in large amounts, and seafood as they worsen hyperthyroid symptoms.", "highlight": True, "conditions": ["hyperthyroidism"], "lifestyle_tags": []},
    {"icon": "☕", "text": "Thyroid (Hyper): Avoid caffeine and stimulants — they worsen the palpitations, anxiety, and tremors associated with hyperthyroidism.", "highlight": False, "conditions": ["hyperthyroidism"], "lifestyle_tags": []},
    {"icon": "🧘", "text": "Thyroid (Hyper): Prioritise low-intensity exercise — yoga, walking, stretching. Avoid high-intensity cardio and overheating the body.", "highlight": False, "conditions": ["hyperthyroidism"], "lifestyle_tags": []},

    # Hypertension
    {"icon": "🧂", "text": "Blood Pressure: Limit total sodium to under 2g/day — approximately 1 tsp of salt total, including salt in cooked food and condiments.", "highlight": True, "conditions": ["hypertension"], "lifestyle_tags": []},
    {"icon": "🧘", "text": "Blood Pressure: Practice 5–10 minutes of slow diaphragmatic breathing daily. Evidence shows this measurably lowers resting blood pressure.", "highlight": False, "conditions": ["hypertension"], "lifestyle_tags": []},
    {"icon": "🌡️", "text": "Blood Pressure: Monitor at home daily at the same time each morning, before medication. Keep a log and bring it to consultations.", "highlight": False, "conditions": ["hypertension"], "lifestyle_tags": []},
    {"icon": "☕", "text": "Blood Pressure: Limit caffeine to 1 cup per day and avoid it after 2pm — caffeine acutely raises blood pressure for several hours.", "highlight": False, "conditions": ["hypertension"], "lifestyle_tags": []},

    # Fatty liver
    {"icon": "🚫", "text": "Fatty Liver: Avoid alcohol completely — even small amounts worsen liver inflammation and fat accumulation. No safe minimum for NAFLD.", "highlight": True, "conditions": ["fatty_liver"], "lifestyle_tags": []},
    {"icon": "☕", "text": "Fatty Liver: Black coffee (no sugar, no milk) 1–2 cups/day has strong evidence for reducing liver fat and inflammation.", "highlight": False, "conditions": ["fatty_liver"], "lifestyle_tags": []},
    {"icon": "⚖️", "text": "Fatty Liver: A 7–10% reduction in body weight significantly reduces liver fat. Consistent, gradual loss is more effective than aggressive dieting.", "highlight": True, "conditions": ["fatty_liver"], "lifestyle_tags": []},
    {"icon": "🛑", "text": "Fatty Liver: Avoid fructose-heavy foods — fruit juices, packaged sweets, excess honey. Fructose is processed almost entirely by the liver.", "highlight": False, "conditions": ["fatty_liver"], "lifestyle_tags": []},

    # IBS
    {"icon": "🧘", "text": "IBS: Stress is a primary IBS trigger via the gut-brain axis. Build a daily 10-minute relaxation practice — deep breathing, yoga, or a quiet walk.", "highlight": True, "conditions": ["ibs"], "lifestyle_tags": []},
    {"icon": "📝", "text": "IBS: Keep a food-symptom diary for 2 weeks. Note what you ate and any symptoms 30 minutes to 4 hours later. Patterns beat guesswork.", "highlight": False, "conditions": ["ibs"], "lifestyle_tags": []},
    {"icon": "💧", "text": "IBS: Drink water between meals rather than with meals — excess fluid during eating can worsen bloating and urgency.", "highlight": False, "conditions": ["ibs"], "lifestyle_tags": []},
    {"icon": "🍽️", "text": "IBS: Eat smaller, more frequent meals rather than large ones. Large meals trigger stronger gut contractions.", "highlight": False, "conditions": ["ibs"], "lifestyle_tags": []},

    # Lifestyle-specific
    {"icon": "🪑", "text": "Desk Job: For every 45–60 minutes of sitting, stand up and move for 2–3 minutes. Prolonged sitting worsens insulin resistance even in people who exercise.", "highlight": False, "conditions": [], "lifestyle_tags": ["desk_job", "sedentary"]},
    {"icon": "💼", "text": "Physical Job: Your job counts as movement but it is repetitive, not therapeutic. Add 10 minutes of stretching after each shift to prevent injury.", "highlight": False, "conditions": [], "lifestyle_tags": ["physical_job"]},

    # Postpartum
    {"icon": "🤱", "text": "Postpartum: Prioritise sleep and recovery in the first 6 weeks. Milk supply, wound healing, and hormonal recovery all depend on rest above everything else.", "highlight": True, "conditions": [], "lifestyle_tags": ["postpartum"]},
    {"icon": "💪", "text": "Postpartum: Start with pelvic floor exercises (Kegels) and diaphragmatic breathing before any core or cardio work. Do not rush.", "highlight": False, "conditions": [], "lifestyle_tags": ["postpartum"]},

    # Elderly
    {"icon": "🦴", "text": "Balance: Practice standing on one leg (near a wall for safety) for 20–30 seconds daily — this significantly reduces fall risk over time.", "highlight": True, "conditions": [], "lifestyle_tags": ["elderly"]},
    {"icon": "☀️", "text": "Bone Health: Supplement Vitamin D3 + K2 if your levels are below 40 ng/mL — essential for bone density and muscle function.", "highlight": False, "conditions": [], "lifestyle_tags": ["elderly"]},
]


AVOID_ITEMS = [
    # Base — everyone
    {"name": "Maida & maida products (white bread, noodles, pasta)", "conditions": [], "diet_exclude": []},
    {"name": "Fried food (samosa, vada, pakoda, puri)", "conditions": [], "diet_exclude": []},
    {"name": "Sugar & sweets (mithai, desserts, sugar in tea/coffee)", "conditions": [], "diet_exclude": []},
    {"name": "Fruit juices — fresh or packaged (eat the whole fruit instead)", "conditions": [], "diet_exclude": []},
    {"name": "Bakery items (biscuits, cakes, pastries, white bread)", "conditions": [], "diet_exclude": []},
    {"name": "Packaged & instant food (chips, namkeen, instant noodles)", "conditions": [], "diet_exclude": []},
    {"name": "Packet soup & instant mixes", "conditions": [], "diet_exclude": []},
    {"name": "Cold drinks & soda (including diet soda)", "conditions": [], "diet_exclude": []},
    {"name": "Alcohol", "conditions": [], "diet_exclude": []},
    {"name": "Tobacco & smoking", "conditions": [], "diet_exclude": []},
    {"name": "Processed meat (sausages, salami, nuggets, hot dogs)", "conditions": [], "diet_exclude": ["Vegetarian", "Vegan", "Eggetarian"]},

    # Condition-specific
    {"name": "Pineapple in large amounts (high sugar, spikes insulin)", "conditions": ["diabetes", "pcos", "prediabetes"], "diet_exclude": []},
    {"name": "Raw papaya", "conditions": ["postpartum"], "diet_exclude": []},
    {"name": "Excess salt — more than 1 tsp/day total", "conditions": ["hypertension"], "diet_exclude": []},
    {"name": "Pickles, papad, and high-sodium condiments", "conditions": ["hypertension"], "diet_exclude": []},
    {"name": "Seaweed & excess seafood (very high iodine)", "conditions": ["hyperthyroidism"], "diet_exclude": ["Vegetarian", "Vegan"]},
    {"name": "Raw cruciferous veg in large amounts (cabbage, cauliflower, broccoli)", "conditions": ["hypothyroidism"], "diet_exclude": []},
    {"name": "Soy products in excess (tofu, soy milk, soya chunks)", "conditions": ["hypothyroidism"], "diet_exclude": []},
    {"name": "Excess honey & concentrated fructose (fruit juices, jaggery in large amounts)", "conditions": ["fatty_liver"], "diet_exclude": []},
    {"name": "Full-fat dairy in excess (malai, cream, excess paneer)", "conditions": ["pcos", "fatty_liver"], "diet_exclude": []},
    {"name": "High-GI fruits in large portions (mango, banana, grapes, chikoo)", "conditions": ["diabetes", "prediabetes"], "diet_exclude": []},
    {"name": "Excess red meat (limit to 1–2 times/week)", "conditions": ["hypertension", "fatty_liver"], "diet_exclude": ["Vegetarian", "Vegan", "Eggetarian"]},
    {"name": "Caffeine above 1 cup/day", "conditions": ["pcos", "hypertension", "hyperthyroidism", "ibs"], "diet_exclude": []},
    {"name": "Gas-forming foods in excess (beans, raw onion, carbonated drinks)", "conditions": ["ibs"], "diet_exclude": []},
    {"name": "Spicy food during flare-ups", "conditions": ["ibs"], "diet_exclude": []},
]


SNACK_OPTIONS = [
    {"name": "Roasted chana", "desc": "High protein, very low GI — stabilises blood sugar for hours", "conditions": ["pcos", "diabetes", "prediabetes", "weight_loss", "fatty_liver"], "veg": True},
    {"name": "Roasted makhana (fox nuts)", "desc": "Light, low calorie, low GI — excellent evening snack", "conditions": ["pcos", "diabetes", "weight_loss", "fatty_liver", "hypertension"], "veg": True},
    {"name": "Sprouted moong chaat", "desc": "High protein + fibre combo — blood-sugar friendly and filling", "conditions": ["pcos", "diabetes", "weight_loss", "hypothyroidism"], "veg": True},
    {"name": "Mixed nuts — small handful (walnuts, almonds, pistachios)", "desc": "Healthy fats + protein — supports hormonal health and satiety", "conditions": ["pcos", "hypothyroidism", "fatty_liver", "weight_loss"], "veg": True},
    {"name": "Apple with 1 tsp peanut butter", "desc": "Fibre + healthy fat — slows sugar absorption, satisfying snack", "conditions": ["pcos", "diabetes", "weight_loss"], "veg": True},
    {"name": "Cucumber & carrot sticks with hummus", "desc": "Low calorie, high fibre — great for weight loss and blood pressure", "conditions": ["diabetes", "hypertension", "weight_loss", "fatty_liver"], "veg": True},
    {"name": "Hard-boiled eggs (1–2)", "desc": "High protein, virtually zero carbs — excellent between-meal snack", "conditions": ["pcos", "diabetes", "weight_loss", "hypothyroidism"], "veg": False},
    {"name": "Plain Greek yoghurt (unsweetened)", "desc": "Probiotic + protein — supports gut health and satiety", "conditions": ["ibs", "weight_loss", "pcos", "diabetes"], "veg": True},
    {"name": "Bajra or jowar chilla (1 small)", "desc": "Complex carb, low GI — far more filling than wheat-based snacks", "conditions": ["pcos", "diabetes", "weight_loss"], "veg": True},
    {"name": "Pear or guava (1 medium)", "desc": "High fibre, lower GI than mango or grapes — better for blood sugar", "conditions": ["diabetes", "pcos", "weight_loss", "fatty_liver"], "veg": True},
    {"name": "Warm turmeric milk (haldi doodh, no sugar)", "desc": "Anti-inflammatory — good evening option, supports sleep quality", "conditions": ["pcos", "hypothyroidism", "fatty_liver", "hypertension", "ibs"], "veg": True},
    {"name": "Flaxseed stirred into yoghurt (1 tbsp ground)", "desc": "Omega-3 + probiotic combo — anti-inflammatory and hormone-supportive", "conditions": ["pcos", "hypothyroidism", "fatty_liver"], "veg": True},
    {"name": "Walnuts (4–5)", "desc": "Best nut for thyroid and brain health — rich in omega-3 and selenium", "conditions": ["hypothyroidism", "pcos", "fatty_liver"], "veg": True},
    {"name": "Homemade vegetable soup (no cream, low salt)", "desc": "Low calorie, filling — great for weight loss and liver health", "conditions": ["fatty_liver", "weight_loss", "hypertension", "ibs"], "veg": True},
    {"name": "Idli (2 small) with coconut chutney", "desc": "Fermented, easy to digest — good for gut health, light snack", "conditions": ["ibs", "weight_loss"], "veg": True},
    {"name": "Amla / Indian gooseberry (fresh or powder in water)", "desc": "Very high Vitamin C — supports liver detox and immunity", "conditions": ["fatty_liver", "diabetes", "pcos"], "veg": True},
    {"name": "Banana (small, 1 medium)", "desc": "Quick energy — best before exercise, not as a rest snack", "conditions": [], "veg": True},
    {"name": "Boiled sweet potato (small portion)", "desc": "Complex carb with fibre — more filling than biscuits, good pre-workout", "conditions": ["hypothyroidism", "elderly"], "veg": True},
    {"name": "Paneer cubes (30g, plain or lightly spiced)", "desc": "High protein, calcium — good vegetarian between-meal option", "conditions": ["pcos", "weight_loss", "elderly"], "veg": True},
    {"name": "Grilled chicken strips (small portion)", "desc": "Pure protein — best between-meal option for non-vegetarians", "conditions": ["weight_loss", "diabetes", "pcos"], "veg": False},
]
