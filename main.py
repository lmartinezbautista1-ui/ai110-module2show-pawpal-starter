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

    # Create at least three tasks at different times for the pets.
    pawpal.save_task(
        CareTask(
            "task-001",
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
            "task-002",
            luna.pet_id,
            "Give medication",
            "daily",
            duration_minutes=5,
            priority="high",
            preferred_time="09:00",
        )
    )
    pawpal.save_task(
        CareTask(
            "task-003",
            buddy.pet_id,
            "Afternoon walk",
            "daily",
            duration_minutes=30,
            priority="medium",
            preferred_time="15:30",
        )
    )
    pawpal.save_task(
        CareTask(
            "task-004",
            luna.pet_id,
            "Evening feeding",
            "daily",
            duration_minutes=10,
            priority="medium",
            preferred_time="18:00",
        )
    )

    today = date.today()
    print(f"Today's Schedule - {today.isoformat()}")
    print(f"Owner: {owner.name}")
    print("=" * 45)

    all_tasks = []
    for pet in owner.pets:
        plan = pawpal.build_plan(today, pet.pet_id)
        all_tasks.extend((task.preferred_time or "99:99", pet, task) for task in plan.tasks)

    # Display every pet's task in time order.
    for task_time, pet, task in sorted(all_tasks, key=lambda item: item[0]):
        print(
            f"{task_time} - {pet.name}: {task.description} "
            f"({task.duration_minutes} minutes, {task.priority} priority)"
        )

    if not all_tasks:
        print("No care tasks are scheduled for today.")


if __name__ == "__main__":
    main()