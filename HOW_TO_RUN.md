# NutriDesk — How to Run

## First time setup

Open Terminal and run:

```bash
pip install -r requirements.txt
```

## Launch the app

From inside the `nutridesk/` folder:

```bash
streamlit run app.py
```

Your browser will open automatically at: **http://localhost:8501**

## Workflow

1. **📋 New Client** — Complete all 4 sections of the intake form and save.
2. **🍽️ Meal Plan** — Select the client, click "Generate New Plan". Two options per lunch/dinner.
3. **📄 PDF Report** — On the Meal Plan page, click "Generate PDF Report" then "Download PDF".
4. **👥 Clients** — View, edit, and manage all clients.
5. **📈 Progress** — Log weekly weigh-ins and blood work (biomarkers).

## Files

```
nutridesk/
├── app.py                  Home dashboard
├── requirements.txt        Python dependencies
├── HOW_TO_RUN.md           This file
├── pages/
│   ├── 1_📋_Intake.py      New client intake form
│   ├── 2_🍽️_Meal_Plan.py   Meal plan generator + PDF export
│   ├── 3_👥_Clients.py      Client directory
│   └── 4_📈_Progress.py    Weight & biomarker tracking
├── utils/
│   ├── database.py         SQLite client storage
│   ├── calculations.py     BMR / TDEE / macro calculations
│   ├── meal_planner.py     Recipe selection algorithm
│   └── pdf_generator.py    PDF report generation
└── data/
    └── clients.db          Auto-created on first run
```

The recipe library (`recipe_library.json`) is read from the parent `Nutritionist/` folder.
