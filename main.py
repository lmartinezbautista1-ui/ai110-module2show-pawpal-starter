"""Simple terminal demo for the PawPal+ domain classes."""

from datetime import date

from pawpal_system import App, CareTask, Owner, Pet


def main() -> None:
    # Create the application service and an owner.
    pawpal = App()
    owner = Owner("owner-001", "Luis Martinez", "luis@example.com")
    pawpal.save_owner(owner)

    # Create and register two pets for the owner.
    buddy = Pet("pet-001", owner.owner_id, "Buddy", "Dog", "Golden Retriever", 4)
    luna = Pet("pet-002", owner.owner_id, "Luna", "Cat", "Siamese", 2)
    pawpal.save_pet(buddy)
    pawpal.save_pet(luna)

    # Create tasks deliberately out of time order so sorting has to do work.
    pawpal.save_task(
        CareTask(
            "task-001",
            buddy.pet_id,
            "Evening feeding",
            "daily",
            duration_minutes=10,
            priority="medium",
            preferred_time="18:00",
        )
    )
    pawpal.save_task(
        CareTask(
            "task-002",
            luna.pet_id,
            "Afternoon walk",
            "daily",
            duration_minutes=30,
            priority="medium",
            preferred_time="15:30",
        )
    )
    pawpal.save_task(
        CareTask(
            "task-003",
            buddy.pet_id,
            "Morning feeding",
            "daily",
            duration_minutes=10,
            priority="high",
            preferred_time="08:00",
        )
    )
    pawpal.save_task(
        CareTask(
            "task-004",
            luna.pet_id,
            "Give medication",
            "daily",
            duration_minutes=5,
            priority="high",
            preferred_time="09:00",
        )
    )
    # Two extra tasks: one unscheduled (no preferred_time) and one that makes
    # the 08:00 slot collide, to exercise the tie-break and end-of-day sorting.
    pawpal.save_task(
        CareTask(
            "task-005",
            buddy.pet_id,
            "Brush fur",
            "daily",
            duration_minutes=15,
            priority="low",
            preferred_time="08:00",
        )
    )
    pawpal.save_task(
        CareTask(
            "task-006",
            luna.pet_id,
            "Trim nails",
            "weekly",
            duration_minutes=20,
            priority="low",
        )
    )

    # Two tasks deliberately placed at the same time (12:00) so the plan
    # detects a scheduling conflict and a warning is printed below.
    pawpal.save_task(
        CareTask(
            "task-007",
            buddy.pet_id,
            "Midday feeding",
            "daily",
            duration_minutes=20,
            priority="medium",
            preferred_time="12:00",
        )
    )
    pawpal.save_task(
        CareTask(
            "task-008",
            luna.pet_id,
            "Vet appointment",
            "weekly",
            duration_minutes=30,
            priority="high",
            preferred_time="12:00",
        )
    )

    today = date.today()
    pets_by_id = {pet.pet_id: pet for pet in owner.pets}

    def show(title: str, tasks) -> None:
        print(title)
        print("=" * 45)
        if not tasks:
            print("(none)")
        for task in tasks:
            pet = pets_by_id[task.pet_id]
            print(
                f"{task.preferred_time or '--:--'} - {pet.name}: {task.description} "
                f"({task.duration_minutes} minutes, {task.priority} priority)"
            )
        print()

    # Build every pet's plan, then show the combined schedule sorted by time.
    all_tasks = pawpal.build_owner_plan(today, owner.owner_id)
    show(f"Today's Schedule - {today.isoformat()} | Owner: {owner.name}", all_tasks)

    # Detect scheduling conflicts and print a warning for each overlapping pair.
    conflicts = pawpal.find_conflicts(today, owner.owner_id)
    if conflicts:
        print(f"WARNING: {len(conflicts)} scheduling conflict(s) detected!")
        for task_a, task_b in conflicts:
            pet_a = pets_by_id[task_a.pet_id]
            pet_b = pets_by_id[task_b.pet_id]
            print(
                f"  - {task_a.preferred_time}: '{task_a.description}' ({pet_a.name}) "
                f"overlaps with '{task_b.description}' ({pet_b.name})"
            )
        print()

    # Mark one task done so the completion filter has something to find.
    plan = pawpal.load_plan(today.isoformat(), buddy.pet_id)
    plan.mark_complete("task-003")

    show("Filter: tasks for Luna", pawpal.filter_tasks(pet_name="lUnA"))
    show("Filter: incomplete tasks (all pets)", pawpal.filter_tasks(completed=False))
    show("Filter: completed tasks", pawpal.filter_tasks(completed=True))
    show(
        "Filter: Buddy + incomplete",
        pawpal.filter_tasks(pet_name="Buddy", completed=False),
    )


if __name__ == "__main__":
    main()