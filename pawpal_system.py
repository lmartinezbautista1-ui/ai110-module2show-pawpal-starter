"""PawPal+ domain model.

This version adds the missing relationships that the starter design needed:
- owner owns many pets
- pet has many tasks
- daily plan references tasks for a pet
- app keeps indexed lookups so scheduling logic stays efficient
"""

from collections import defaultdict
from datetime import date as _date
from typing import Dict, List, Optional, Union


class Owner:
    """A pet owner with basic contact info."""

    def __init__(self, owner_id: str, name: str, contact_info: str):
        """Initialize an owner with id, name and contact info; pets start empty."""
        self.owner_id = owner_id
        self.name = name
        self.contact_info = contact_info
        self.pets: List["Pet"] = []

    def add_pet(self, pet: "Pet") -> None:
        """Associate this owner with a pet."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: "Pet") -> None:
        """Disassociate a pet from this owner."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_pet(self, pet_id: str) -> Optional["Pet"]:
        """Return one of this owner's pets by id, or None."""
        for pet in self.pets:
            if pet.pet_id == pet_id:
                return pet
        return None


class Pet:
    """A pet owned by an owner; has care tasks scheduled for it."""

    def __init__(self, pet_id: str, owner_id: str, name: str, species: str, breed: str, age: int):
        """Initialize a pet with identifying info and no owner link or tasks yet."""
        self.pet_id = pet_id
        self.owner_id = owner_id
        self.name = name
        self.species = species
        self.breed = breed
        self.age = age
        self.owner: Optional[Owner] = None
        self.tasks: List["CareTask"] = []

    def add_task(self, task: "CareTask") -> None:
        """Associate this pet with a care task."""
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: "CareTask") -> None:
        """Disassociate a care task from this pet."""
        if task in self.tasks:
            self.tasks.remove(task)

    def tasks_by_priority(self) -> List["CareTask"]:
        """Return this pet's tasks sorted high -> low priority, then by preferred time."""
        order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            self.tasks,
            key=lambda t: (order.get(t.priority, 3), t.preferred_time or "99:99"),
        )


class CareTask:
    """A single care task for a pet (e.g. feeding, walk, medication)."""

    def __init__(
        self,
        task_id: str,
        pet_id: str,
        description: str,
        frequency: str,
        duration_minutes: int = 0,
        priority: str = "medium",
        preferred_time: Optional[str] = None,
    ):
        """Initialize a care task with schedule, duration and priority details."""
        self.task_id = task_id
        self.pet_id = pet_id
        self.description = description
        self.frequency = frequency
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.preferred_time = preferred_time

    def is_due_on(self, when: "date") -> bool:
        """Return True if this task should appear on a plan for the given day.

        Supported frequencies: 'daily', 'weekly' (due on the weekday stored in
        ``self.weekday`` or its preferred_time day), 'once'. Unknown frequencies
        are treated as daily.
        """
        freq = (self.frequency or "daily").lower()
        if freq in ("daily", "once"):
            return True
        if freq == "weekly":
            target = getattr(self, "weekday", None)
            if target is None:
                return True
            if isinstance(target, str):
                names = [
                    "monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday",
                ]
                target = names.index(target.lower()) if target.lower() in names else None
            if target is None:
                return True
            return when.weekday() == target
        return True


class DailyPlan:
    """A plan for one day: which tasks are scheduled and their completion status."""

    def __init__(
        self,
        date: str,
        pet_id: str,
        tasks: Optional[List[Union[str, CareTask]]] = None,
        completion_status: Optional[Dict[str, bool]] = None,
    ):
        """Initialize a plan for a date and pet, seeding tasks and completion flags."""
        self.date = date
        self.pet_id = pet_id
        self.tasks: List[CareTask] = []
        self.completion_status: Dict[str, bool] = {}
        self._extra_task_ids: List[str] = []  # task ids given without a CareTask object

        if tasks is not None:
            for task in tasks:
                if isinstance(task, CareTask):
                    self.add_task(task)
                else:
                    self._extra_task_ids.append(task)

        if completion_status is not None:
            self.completion_status.update(completion_status)
        for task in self.tasks:
            self.completion_status.setdefault(task.task_id, False)
        for task_id in self._extra_task_ids:
            self.completion_status.setdefault(task_id, False)

    @property
    def task_ids(self) -> List[str]:
        """All task ids in the plan: real task objects plus bare ids."""
        return [task.task_id for task in self.tasks] + list(self._extra_task_ids)

    def add_task(self, task: CareTask) -> None:
        """Add a task to the plan and initialize its completion flag."""
        if task not in self.tasks:
            self.tasks.append(task)
        self.completion_status.setdefault(task.task_id, False)

    def mark_complete(self, task_id: str, complete: bool = True) -> None:
        """Set completion state for a task in this plan."""
        self.completion_status[task_id] = complete

    def is_complete(self) -> bool:
        """True when every task id in the plan is marked done."""
        ids = self.task_ids
        return bool(ids) and all(self.completion_status.get(tid, False) for tid in ids)

    def progress(self) -> float:
        """Fraction of tasks completed (0.0 - 1.0); 0.0 for an empty plan."""
        ids = self.task_ids
        if not ids:
            return 0.0
        done = sum(1 for tid in ids if self.completion_status.get(tid, False))
        return done / len(ids)


class App:
    """Top-level application: stores owners, pets, tasks and plans."""

    def __init__(self):
        """Initialize the app with empty stores and lookup indexes."""
        self.owners: List[Owner] = []
        self.pets: List[Pet] = []
        self.tasks: List[CareTask] = []
        self.plans: List[DailyPlan] = []

        self._owners_by_id: Dict[str, Owner] = {}
        self._pets_by_id: Dict[str, Pet] = {}
        self._tasks_by_pet_id: Dict[str, List[CareTask]] = {}
        self._plans_by_key: Dict[str, DailyPlan] = {}

    def save_owner(self, owner: Owner) -> None:
        """Store an owner in the owners list and index by id."""
        self._owners_by_id[owner.owner_id] = owner
        if owner not in self.owners:
            self.owners.append(owner)

    def delete_owner(self, owner_id: str) -> None:
        """Remove an owner (and its back-references) by id."""
        owner = self._owners_by_id.pop(owner_id, None)
        if owner is None:
            return
        if owner in self.owners:
            self.owners.remove(owner)
        for pet in list(owner.pets):
            pet.owner = None

    def load_owner(self, owner_id: str) -> Optional[Owner]:
        """Look up an owner by id; return the Owner or None."""
        return self._owners_by_id.get(owner_id)

    def save_pet(self, pet: Pet) -> None:
        """Store a pet in the pets list and link it to its owner."""
        self._pets_by_id[pet.pet_id] = pet
        if pet not in self.pets:
            self.pets.append(pet)

        # Detach the pet from a previous owner if it changed hands.
        if pet.owner is not None and pet.owner.owner_id != pet.owner_id:
            pet.owner.remove_pet(pet)
            pet.owner = None

        owner = self.load_owner(pet.owner_id)
        if owner is not None:
            pet.owner = owner
            owner.add_pet(pet)

    def delete_pet(self, pet_id: str) -> None:
        """Remove a pet and all of its tasks and plans by id."""
        pet = self._pets_by_id.pop(pet_id, None)
        if pet is None:
            return
        if pet in self.pets:
            self.pets.remove(pet)
        if pet.owner is not None:
            pet.owner.remove_pet(pet)
            pet.owner = None
        for task in list(self._tasks_by_pet_id.get(pet_id, [])):
            if task in self.tasks:
                self.tasks.remove(task)
        self._tasks_by_pet_id.pop(pet_id, None)
        for key in [k for k in self._plans_by_key if k.endswith(f":{pet_id}")]:
            plan = self._plans_by_key.pop(key)
            if plan in self.plans:
                self.plans.remove(plan)

    def load_pet(self, pet_id: str) -> Optional[Pet]:
        """Look up a pet by id."""
        return self._pets_by_id.get(pet_id)

    def save_task(self, task: CareTask) -> None:
        """Store a care task in the tasks list and attach it to its pet."""
        self.tasks = [existing for existing in self.tasks if existing.task_id != task.task_id]
        self.tasks.append(task)

        pet = self.load_pet(task.pet_id)
        if pet is not None:
            pet.add_task(task)

        existing = self._tasks_by_pet_id.setdefault(task.pet_id, [])
        if task not in existing:
            existing.append(task)

    def delete_task(self, task_id: str) -> None:
        """Remove a task by id from the store, its pet and any plans."""
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if task is None:
            return
        self.tasks.remove(task)
        pet = self.load_pet(task.pet_id)
        if pet is not None:
            pet.remove_task(task)
        bucket = self._tasks_by_pet_id.get(task.pet_id)
        if bucket is not None:
            if task in bucket:
                bucket.remove(task)
            if not bucket:
                del self._tasks_by_pet_id[task.pet_id]
        for plan in self.plans:
            if task in plan.tasks:
                plan.tasks.remove(task)
            plan.completion_status.pop(task_id, None)

    def load_tasks(self, pet_id: str) -> List[CareTask]:
        """Return all care tasks belonging to the given pet."""
        return list(self._tasks_by_pet_id.get(pet_id, []))

    def load_task(self, task_id: str) -> Optional[CareTask]:
        """Look up a single care task by id."""
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def save_plan(self, plan: DailyPlan) -> None:
        """Store a daily plan in the plans list."""
        key = f"{plan.date}:{plan.pet_id}"
        self._plans_by_key[key] = plan
        if plan not in self.plans:
            self.plans.append(plan)

        for task in plan.tasks:
            self.save_task(task)

    def delete_plan(self, plan_date: str, pet_id: str) -> None:
        """Remove the stored plan for a given date and pet."""
        key = f"{plan_date}:{pet_id}"
        plan = self._plans_by_key.pop(key, None)
        if plan is not None and plan in self.plans:
            self.plans.remove(plan)

    def load_plan(self, date: str, pet_id: str) -> Optional[DailyPlan]:
        """Look up the plan for a given date and pet; return the DailyPlan or None."""
        return self._plans_by_key.get(f"{date}:{pet_id}")

    def build_plan(
        self,
        plan_date: Union[str, "date"],
        pet_id: str,
    ) -> DailyPlan:
        """Create (or replace) a DailyPlan for a pet, seeded with its due tasks.

        Tasks are added in priority order (high first), ties broken by preferred
        time. The plan is stored in the app's index and returned.
        """
        if isinstance(plan_date, _date):
            plan_date = plan_date.isoformat()

        existing = self.load_plan(plan_date, pet_id)
        if existing is not None:
            self.delete_plan(plan_date, pet_id)

        due = [
            task
            for task in self.load_tasks(pet_id)
            if task.is_due_on(plan_date if isinstance(plan_date, str) else plan_date)
        ]
        plan = DailyPlan(plan_date, pet_id, tasks=due)
        self.save_plan(plan)
        return plan
