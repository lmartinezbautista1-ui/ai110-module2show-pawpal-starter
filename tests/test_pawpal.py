from datetime import date

from pawpal_system import App, CareTask, DailyPlan, Owner, Pet


def test_mark_complete_changes_status():
    task = CareTask("t-1", "p-1", "Morning walk", "daily", preferred_time="08:00")
    plan = DailyPlan("2026-10-04", "p-1", [task])

    assert plan.completion_status["t-1"] is False
    assert plan.is_complete() is False

    plan.mark_complete("t-1", True)

    assert plan.completion_status["t-1"] is True
    assert plan.is_complete() is True


def test_add_task_increases_pet_task_count():
    pet = Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3)
    assert len(pet.tasks) == 0

    pet.add_task(CareTask("t-1", "p-1", "Morning walk", "daily", preferred_time="08:00"))
    assert len(pet.tasks) == 1

    pet.add_task(CareTask("t-2", "p-1", "Evening feeding", "daily", preferred_time="18:00"))
    assert len(pet.tasks) == 2


def _owner_with_pets(*pets):
    """Build an App with an owner who owns the given pets, saving each task."""
    app = App()
    owner = Owner("o-1", "Lu", "lu@example.com")
    app.save_owner(owner)
    for pet in pets:
        app.save_pet(pet)
    return app, owner


# --- Sorting Correctness ------------------------------------------------------


def test_sort_by_time_chronological_order():
    """Tasks come back ordered by time numerically, not by string format."""
    tasks = [
        CareTask("t-3", "p-1", "Evening feeding", "daily", preferred_time="18:00"),
        CareTask("t-1", "p-1", "Morning walk", "daily", preferred_time="8:00"),
        CareTask("t-2", "p-1", "Midnight snack", "daily", preferred_time="00:15"),
        CareTask("t-4", "p-1", "Unscheduled", "daily"),  # no preferred_time
    ]
    ordered = App.sort_by_time(tasks)

    assert [t.task_id for t in ordered] == ["t-2", "t-1", "t-3", "t-4"]


def test_sort_by_time_priority_tiebreak():
    """Same time + priority_tiebreak=True orders high -> medium -> low."""
    tasks = [
        CareTask("t-low", "p-1", "Low", "daily", priority="low", preferred_time="09:00"),
        CareTask("t-high", "p-1", "High", "daily", priority="high", preferred_time="09:00"),
        CareTask("t-med", "p-1", "Med", "daily", priority="medium", preferred_time="09:00"),
    ]
    ordered = App.sort_by_time(tasks, priority_tiebreak=True)

    assert [t.task_id for t in ordered] == ["t-high", "t-med", "t-low"]


def test_build_owner_plan_sorts_across_pets():
    """build_owner_plan returns every pet's due tasks in one sorted schedule."""
    app, owner = _owner_with_pets(
        Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3),
        Pet("p-2", "o-1", "Bean", "cat", "Tabby", 2),
    )
    app.save_task(CareTask("t-b", "p-1", "Dog walk", "daily", preferred_time="10:00"))
    app.save_task(CareTask("t-a", "p-2", "Cat feed", "daily", preferred_time="07:30"))

    schedule = app.build_owner_plan("2026-10-08", owner.owner_id)

    assert [t.task_id for t in schedule] == ["t-a", "t-b"]


def test_tasks_by_priority_high_first():
    pet = Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3)
    pet.add_task(CareTask("t-low", "p-1", "Low", "daily", priority="low", preferred_time="07:00"))
    pet.add_task(CareTask("t-high", "p-1", "High", "daily", priority="high", preferred_time="09:00"))

    assert [t.task_id for t in pet.tasks_by_priority()] == ["t-high", "t-low"]


# --- Recurrence Logic ---------------------------------------------------------


def test_complete_daily_task_creates_next_occurrence():
    """Marking a daily task complete saves a fresh task for the next day."""
    app, owner = _owner_with_pets(Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3))
    app.save_task(CareTask("t-1", "p-1", "Morning walk", "daily", preferred_time="08:00"))

    occurrence = app.complete_task("2026-10-08", "p-1", "t-1")

    assert occurrence is not None
    assert occurrence.task_id == "t-1@2026-10-09"
    assert occurrence.preferred_time == "08:00"
    assert app.load_task("t-1@2026-10-09") is occurrence
    # The pet picked up the new occurrence too.
    assert any(t.task_id == "t-1@2026-10-09" for t in app.load_pet("p-1").tasks)


def test_complete_daily_task_id_chains_across_days():
    """Completing a dated occurrence strips the @date suffix and rolls forward."""
    app, owner = _owner_with_pets(Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3))
    base = CareTask("t-1", "p-1", "Morning walk", "daily", preferred_time="08:00")
    app.save_task(base)
    first = base.create_next_occurrence(date(2026, 10, 8))
    app.save_task(first)

    occurrence = app.complete_task("2026-10-08", "p-1", first.task_id)

    assert occurrence.task_id == "t-1@2026-10-09"


def test_unmark_complete_does_not_create_occurrence():
    app, owner = _owner_with_pets(Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3))
    app.save_task(CareTask("t-1", "p-1", "Morning walk", "daily", preferred_time="08:00"))

    assert app.complete_task("2026-10-08", "p-1", "t-1", complete=False) is None
    assert app.load_task("t-1@2026-10-09") is None


def test_complete_task_does_not_duplicate_next_occurrence():
    """Completing the same daily task twice on one day yields one occurrence."""
    app, owner = _owner_with_pets(Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3))
    app.save_task(CareTask("t-1", "p-1", "Morning walk", "daily", preferred_time="08:00"))

    first = app.complete_task("2026-10-08", "p-1", "t-1")
    second = app.complete_task("2026-10-08", "p-1", "t-1")

    assert first is not None
    assert second is None  # t-1@2026-10-09 already exists


def test_complete_non_daily_task_creates_no_occurrence():
    app, owner = _owner_with_pets(Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3))
    app.save_task(CareTask("t-once", "p-1", "Vet visit", "once", preferred_time="14:00"))

    assert app.complete_task("2026-10-08", "p-1", "t-once") is None
    assert app.load_task("t-once@2026-10-09") is None


def test_create_next_occurrence_is_independent_clone():
    """The clone copies scheduling details but mutating it leaves the base alone."""
    base = CareTask("t-1", "p-1", "Morning walk", "daily", priority="high", preferred_time="08:00")
    base.weekday = "monday"

    clone = base.create_next_occurrence(date(2026, 10, 9))
    clone.preferred_time = "09:30"
    clone.weekday = "friday"

    assert base.preferred_time == "08:00"
    assert base.weekday == "monday"
    assert clone.preferred_time == "09:30"
    assert clone.weekday == "friday"
    assert clone.description == base.description
    assert clone.priority == "high"


def test_is_due_on_weekly():
    """A weekly task is due only on its weekday and rolls to the next week."""
    task = CareTask("t-1", "p-1", "Bath", "weekly", preferred_time="10:00")
    task.weekday = "monday"

    assert task.is_due_on(date(2026, 10, 5)) is True   # a Monday
    assert task.is_due_on(date(2026, 10, 6)) is False  # a Tuesday
    assert task.is_due_on(date(2026, 10, 12)) is True  # next Monday


def test_is_due_on_unknown_frequency_treated_as_daily():
    task = CareTask("t-1", "p-1", "Mystery", "biweekly", preferred_time="10:00")
    assert task.is_due_on(date(2026, 10, 8)) is True


# --- Conflict Detection -------------------------------------------------------


def test_overlapping_flags_duplicate_times():
    """Two tasks at the same preferred_time are reported as one conflict pair."""
    a = CareTask("t-a", "p-1", "Feed Mochi", "daily", 30, preferred_time="08:00")
    b = CareTask("t-b", "p-1", "Feed Bean", "daily", 15, preferred_time="08:00")
    plan = DailyPlan("2026-10-08", "p-1", [a, b])

    conflicts = plan.overlapping()

    assert len(conflicts) == 1
    assert {conflicts[0][0].task_id, conflicts[0][1].task_id} == {"t-a", "t-b"}


def test_overlapping_adjacent_slots_do_not_conflict():
    """A task ending at 08:30 and one starting at 08:30 do not overlap."""
    a = CareTask("t-a", "p-1", "Walk", "daily", 30, preferred_time="08:00")
    b = CareTask("t-b", "p-1", "Feed", "daily", 15, preferred_time="08:30")
    plan = DailyPlan("2026-10-08", "p-1", [a, b])

    assert plan.overlapping() == []


def test_overlapping_ignores_unscheduled_tasks():
    plan = DailyPlan(
        "2026-10-08",
        "p-1",
        [
            CareTask("t-a", "p-1", "Unscheduled", "daily"),
            CareTask("t-b", "p-1", "Also unscheduled", "daily"),
        ],
    )

    assert plan.overlapping() == []


def test_find_conflicts_across_pets():
    """Same-time tasks on different pets are caught at owner level."""
    app, owner = _owner_with_pets(
        Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3),
        Pet("p-2", "o-1", "Bean", "cat", "Tabby", 2),
    )
    app.save_task(CareTask("t-a", "p-1", "Dog feed", "daily", 30, preferred_time="08:00"))
    app.save_task(CareTask("t-b", "p-2", "Cat feed", "daily", 15, preferred_time="08:00"))

    conflicts = app.find_conflicts("2026-10-08", owner.owner_id)

    assert len(conflicts) == 1
    assert {conflicts[0][0].task_id, conflicts[0][1].task_id} == {"t-a", "t-b"}


def test_find_conflicts_empty_when_no_overlap():
    app, owner = _owner_with_pets(Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3))
    app.save_task(CareTask("t-a", "p-1", "Walk", "daily", 30, preferred_time="08:00"))
    app.save_task(CareTask("t-b", "p-1", "Feed", "daily", 15, preferred_time="18:00"))

    assert app.find_conflicts("2026-10-08", owner.owner_id) == []
