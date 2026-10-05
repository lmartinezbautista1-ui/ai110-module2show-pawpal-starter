from pawpal_system import App, CareTask, DailyPlan, Owner, Pet


def test_app_tracks_related_objects():
    app = App()
    owner = Owner("o-1", "Jordan", "jordan@example.com")
    pet = Pet("p-1", "o-1", "Mochi", "dog", "Labrador", 3)
    task = CareTask(
        "t-1",
        "p-1",
        "Morning walk",
        "daily",
        duration_minutes=30,
        priority="high",
        preferred_time="08:00",
    )

    app.save_owner(owner)
    app.save_pet(pet)
    app.save_task(task)

    assert app.load_owner("o-1") is owner
    assert pet in owner.pets
    assert app.load_tasks("p-1") == [task]

    plan = DailyPlan("2026-09-28", "p-1", [task])
    app.save_plan(plan)

    assert app.load_plan("2026-09-28", "p-1") is plan
    assert plan.completion_status["t-1"] is False
