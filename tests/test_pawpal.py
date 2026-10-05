from pawpal_system import CareTask, DailyPlan, Pet


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
