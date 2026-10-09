# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:
luis0330@MacBookAir ai110-module2show-pawpal-starter % /opt/homebrew/bin/python3
 /Users/luis0330/ai110-module2show-pawpal-starter/main.py
Today's Schedule - 2026-10-04
Owner: Luis Martinez
=============================================
08:00 - Buddy: Morning feeding (10 minutes, high priority)
09:00 - Luna: Give medication (5 minutes, high priority)
15:30 - Buddy: Afternoon walk (30 minutes, medium priority)
18:00 - Luna: Evening feeding (10 minutes, medium priority)

```
# Paste your pytest output here
(.venv) luis0330@MacBookAir ai110-module2show-pawpal-starter % python -m pytest
========================== test session starts ==========================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/luis0330/ai110-module2show-pawpal-starter
configfile: pytest.ini
plugins: anyio-4.15.1
collected 20 items                                                      

tests/test_model_relationships.py .                               [  5%]
tests/test_pawpal.py ...................                          [100%]

========================== 20 passed in 0.02s ===========================

My 20 tests check task and pet relationships, schedule sorting, daily and weekly due dates, recurring task creation, completion tracking, and time-conflict detection within and across pets. They also check edge cases, such as adjacent tasks not conflicting, unscheduled tasks being ignored, and duplicate recurring tasks not being created. Give myself a 4 stars on "Confidence Level" for this one.
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | App.sort_by_time() | Orders tasks by preferred time, with an optional priority tiebreaker |
| Filtering | App.filter_tasks() | Filters tasks by pet name, completion status, or both |
| Conflict detection | DailyPlan.overlapping() | Finds tasks with overlapping time intervals |
| Recurring tasks | CareTask.is_due_on() | Checks whether a task is due on a particular date. When the daily task is completed, App.complete_task() uses CareTask.create_next_occurrence() to create the next day’s task and avoids duplicates |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. Start the web UI with streamlit run app.py (or the terminal demo with python main.py). The domain logic lives in pawpal_system.py; both entry points use the same classes.
2. Add a Pet — a form (name, species, breed, age) that saves via App.save_pet and lists current pets in an st.table.
3. Schedule a Task — pick a pet, frequency (daily/weekly/once), title, duration, priority, and preferred time; saves via App.save_task
4. Filterable task list — two st.selectbox controls (by pet, by completion status) feed App.filter_tasks, then App.sort_by_time; results render in an st.table with priority icons 🔴🟡🟢 and an st.success summary.
5. Build Schedule — a button calls App.build_plan(date.today(), pet_id) for the selected pet and displays the resulting DailyPlan.
6. Add pet Mochi (dog) → "Saved pet Mochi (pet-001)" confirmation.
7. Schedule a task for Mochi: "Morning walk", daily, 20 min, high priority, 08:00 → saved and attached to Mochi.
8. Add a second task colliding at 08:00 (e.g. "Feed", 10 min) → saved.
9. Click Generate schedule → today's plan for Mochi appears.
10. Sorting by time — the plan renders via App.sort_by_time(tasks, priority_tiebreak=True): tasks order by (hour, minute), equal times broken high → low priority, untimed tasks last.
11. Conflict warnings — plan.overlapping() detects half-open intervals that collide (08:00–08:20 walk vs 08:00–08:10 feed); an st.warning lists each pair.
12. Completion tracking — an st.progress bar shows plan.progress(); ✅/↩️ buttons call plan.mark_complete, done tasks get strikethrough, and an "all done" message appears when plan.is_complete().
13. Recurrence — completing a daily task auto-generates tomorrow's clone (task-00X@YYYY-MM-DD id) via CareTask.create_next_occurrence; weekly tasks are due only on their stored weekday.
14. Running python main.py registers owner Luis Martinez with two pets (Buddy, Luna), eight tasks deliberately out of order — including an untimed task, an 08:00 tie, and two 12:00 collisions — then prints the sorted schedule, conflict warnings, and filter results:
Today's Schedule - 2026-10-09 | Owner: Luis Martinez
=============================================
08:00 - Buddy: Morning feeding (10 minutes, high priority)
08:00 - Buddy: Brush fur (15 minutes, low priority)
09:00 - Luna: Give medication (5 minutes, high priority)
12:00 - Luna: Vet appointment (30 minutes, high priority)
12:00 - Buddy: Midday feeding (20 minutes, medium priority)
15:30 - Luna: Afternoon walk (30 minutes, medium priority)
18:00 - Buddy: Evening feeding (10 minutes, medium priority)
--:-- - Luna: Trim nails (20 minutes, low priority)
WARNING: 2 scheduling conflict(s) detected!
  - 08:00: 'Morning feeding' (Buddy) overlaps with 'Brush fur' (Buddy)
  - 12:00: 'Midday feeding' (Buddy) overlaps with 'Vet appointment' (Luna)
Filter: tasks for Luna
=============================================
09:00 - Luna: Give medication (5 minutes, high priority)
12:00 - Luna: Vet appointment (30 minutes, high priority)
15:30 - Luna: Afternoon walk (30 minutes, medium priority)
--:-- - Luna: Trim nails (20 minutes, low priority)
Filter: incomplete tasks (all pets)
=============================================
08:00 - Buddy: Brush fur (15 minutes, low priority)
09:00 - Luna: Give medication (5 minutes, high priority)
12:00 - Buddy: Midday feeding (20 minutes, medium priority)
12:00 - Luna: Vet appointment (30 minutes, high priority)
15:30 - Luna: Afternoon walk (30 minutes, medium priority)
18:00 - Buddy: Evening feeding (10 minutes, medium priority)
--:-- - Luna: Trim nails (20 minutes, low priority)
Filter: completed tasks
=============================================
08:00 - Buddy: Morning feeding (10 minutes, high priority)
Filter: Buddy + incomplete
=============================================
08:00 - Buddy: Brush fur (15 minutes, low priority)
12:00 - Buddy: Midday feeding (20 minutes, medium priority)
18:00 - Buddy: Evening feeding (10 minutes, medium priority)

15. What the output demonstrates, step by step: the combined two-pet schedule is sorted by time (the 08:00 tie shows "high priority first on ties" — Morning feeding before Brush fur); the untimed "Trim nails" sorts last as --:--; the two 12:00 tasks are flagged as conflicts across different pets (Buddy + Luna); "Morning feeding" was marked complete, so the completed filter shows only it while the incomplete filters exclude it — all from App.filter_tasks re-sorted by App.sort_by_time.


**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
