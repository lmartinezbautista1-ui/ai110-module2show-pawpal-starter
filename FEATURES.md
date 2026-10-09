# PawPal+ — Features

Domain model: `pawpal_system.py` · UI: `app.py` (Streamlit)

## Scheduling & planning

- **Daily plan generation** — `App.build_plan(date, pet_id)` selects only the tasks
  that are actually due on a given day (`CareTask.is_due_on` handles `daily`,
  `weekly` via weekday matching, and `once` frequencies), stores them in a
  `DailyPlan`, and indexes it by `(date, pet_id)`.
- **Combined multi-pet schedule** — `App.build_owner_plan(date, owner_id)` builds a
  plan for every pet an owner has and merges them into one day view, ready to
  display.
- **Time sorting** — `App.sort_by_time(tasks, priority_tiebreak=True)` orders tasks
  numerically on (hour, minute) so `8:30` and `08:30` sort identically; tasks
  without a preferred time sort last; equal times are broken by priority
  (high → medium → low). `Pet.tasks_by_priority()` does the same ordering
  within a single pet's task list.

## Conflict detection

- **Interval overlap algorithm** — `CareTask.time_bounds()` converts a task's
  preferred time + duration into a half-open minutes-from-midnight interval;
  `DailyPlan.overlapping()` sorts tasks by start time and reports every pair
  whose intervals intersect, with an early `break` once a later task can no
  longer overlap (sorted-start optimization).
- **Cross-pet conflict detection** — `App.find_conflicts(date, owner_id)` merges
  all of an owner's pets' plans into one task list and applies the same
  overlap algorithm, so it catches e.g. two feedings at 08:00 even when the
  tasks belong to different pets.
- **Human-readable conflict warnings** — `App.conflict_warnings(date, owner_id)`
  turns each conflicting pair into a printable string like
  `⚠ 08:00-08:10: 'Feed' (Buddy) overlaps 'Meds' (Luna)`; it's a
  never-raises companion that tolerates missing owners, malformed times, and
  bad dates. The Streamlit schedule view surfaces `DailyPlan.overlapping()`
  results as an inline `st.warning`.

## Recurrence

- **Daily recurrence with automatic next-day generation** — completing a daily
  task via `App.complete_task` calls `CareTask.create_next_occurrence(next_day)`,
  which clones the task (description, duration, priority, preferred time) with
  a new id like `task-001@2026-10-07`. Base ids are recovered by stripping any
  existing `@date` suffix, so recurring clones chain correctly day after day,
  and duplicate next-day occurrences are suppressed.
- **Weekly recurrence** — tasks with `frequency='weekly'` are due only on the
  weekday stored on the task (`CareTask.is_due_on`), with graceful fallback
  when the weekday is missing or unrecognized.

## Completion tracking

- **Per-plan completion state** — `DailyPlan.completion_status` tracks each task
  id, seeded to `False` on task add; `mark_complete` / `progress` /
  `is_complete` expose fraction-done and all-done states.
- **Completion-aware filtering** — `App.filter_tasks(pet_name, completed)` looks
  up a task's done/undone state from the most recent plan (by date) that
  contains it, and filters by pet name (case-insensitive) at the same time.
- **Progress bar & celebration UI** — the schedule view shows a
  `st.progress` bar driven by `plan.progress()`, strikethrough for done tasks,
  toggle buttons calling `plan.mark_complete`, and an "all done" message when
  `plan.is_complete()` is true.

## Data management

- **Indexed lookups** — `App` maintains private dictionaries
  (`_owners_by_id`, `_pets_by_id`, `_tasks_by_id`, `_tasks_by_pet_id`,
  `_plans_by_key`) so saves, loads and deletes are O(1) instead of scanning
  collections.
- **Consistent relationships** — `App.save_pet` / `save_task` attach objects to
  their owner/pet back-references (`owner.pets`, `pet.tasks`), and deletes
  cascade: `delete_pet` removes the pet's tasks and plans, `delete_task`
  removes the task from every plan, `delete_owner` detaches its pets.
- **Interactive filter controls** — the Streamlit task list offers filter-by-pet
  and filter-by-status selectors that feed `App.filter_tasks`, then re-sort
  with `App.sort_by_time`, with priority icons (🔴 🟡 🟢) per task.
