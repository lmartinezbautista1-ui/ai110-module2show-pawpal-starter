"""PawPal+ domain model.

This version adds the missing relationships that the starter design needed:
- owner owns many pets
- pet has many tasks
- daily plan references tasks for a pet
- app keeps indexed lookups so scheduling logic stays efficient
"""

from datetime import date as _date, timedelta
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

    def time_bounds(self) -> Optional[tuple]:
        """Return (start, end) in minutes-from-midnight, or None if unscheduled.

        ``end`` = preferred_time + duration_minutes. Tasks without a duration
        occupy just their start minute.
        """
        if not self.preferred_time:
            return None
        try:
            h, m = map(int, self.preferred_time.split(":"))
        except (ValueError, AttributeError):
            return None  # malformed time string -> treat as unscheduled
        start = h * 60 + m
        return (start, start + max(self.duration_minutes, 0))

    def create_next_occurrence(self, next_day: _date) -> "CareTask":
        """Create a fresh CareTask instance for the next daily occurrence.

        The clone copies all scheduling details (description, duration,
        priority, preferred time) and gets a new id derived from this task's
        base id plus the target date, e.g. ``task-001@2026-10-07``. The base id
        is recovered by stripping any existing ``@date`` suffix so completing
        the clone generates the following day's task id the same way.
        """
        base_id = self.task_id.split("@", 1)[0]
        clone = CareTask(
            f"{base_id}@{next_day.isoformat()}",
            self.pet_id,
            self.description,
            self.frequency,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            preferred_time=self.preferred_time,
        )
        # Carry over optional scheduling extras (e.g. weekday for weekly tasks).
        for attr in ("weekday",):
            value = getattr(self, attr, None)
            if value is not None:
                setattr(clone, attr, value)
        return clone

    def is_due_on(self, when: _date) -> bool:
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

    @staticmethod
    def _intervals_overlap(a: tuple, b: tuple) -> bool:
        """True when half-open intervals [a_start, a_end) and [b_start, b_end) intersect."""
        return a[0] < b[1] and b[0] < a[1]

    def overlapping(self, tasks: Optional[List[CareTask]] = None) -> List[tuple]:
        """Find pairs of tasks in this plan whose time slots conflict.

        Tasks conflict when their (preferred_time + duration) intervals
        intersect. Unscheduled tasks (no preferred_time) are ignored. Returns a
        list of ``(task_a, task_b)`` tuples, each pair ordered by start time;
        every conflicting pair appears once. Pass ``tasks`` to check an
        arbitrary list instead of this plan's tasks (used by App to detect
        conflicts across different pets' plans).
        """
        scheduled = [
            (task.time_bounds(), task)
            for task in (tasks if tasks is not None else self.tasks)
        ]
        scheduled = [(bounds, t) for bounds, t in scheduled if bounds is not None]
        scheduled.sort(key=lambda item: item[0])

        conflicts: List[tuple] = []
        for i, (bounds_a, task_a) in enumerate(scheduled):
            for bounds_b, task_b in scheduled[i + 1:]:
                if bounds_b[0] >= bounds_a[1]:
                    break  # sorted by start: no later task can overlap task_a
                conflicts.append((task_a, task_b))
        return conflicts

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
        self._tasks_by_id: Dict[str, CareTask] = {}
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
            self._tasks_by_id.pop(task.task_id, None)
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
        self._tasks_by_id[task.task_id] = task

        pet = self.load_pet(task.pet_id)
        if pet is not None:
            pet.add_task(task)

        existing = self._tasks_by_pet_id.setdefault(task.pet_id, [])
        if task not in existing:
            existing.append(task)

    def delete_task(self, task_id: str) -> None:
        """Remove a task by id from the store, its pet and any plans."""
        task = self._tasks_by_id.pop(task_id, None)
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
        return self._tasks_by_id.get(task_id)

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
        plan_date: Union[str, _date],
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
            if task.is_due_on(_date.fromisoformat(plan_date))
        ]
        plan = DailyPlan(plan_date, pet_id, tasks=due)
        self.save_plan(plan)
        return plan

    def build_owner_plan(self, plan_date: Union[str, _date], owner_id: str) -> List[CareTask]:
        """Build/refresh plans for every pet of an owner and return all due tasks.

        Tasks are returned sorted by preferred time (then priority), across all
        the owner's pets — ready to display as one combined day schedule.
        """
        if isinstance(plan_date, _date):
            plan_date = plan_date.isoformat()

        owner = self.load_owner(owner_id)
        if owner is None:
            return []

        combined: List[CareTask] = []
        for pet in owner.pets:
            combined.extend(self.build_plan(plan_date, pet.pet_id).tasks)

        return self.sort_by_time(combined, priority_tiebreak=True)

    def complete_task(
        self,
        plan_date: str,
        pet_id: str,
        task_id: str,
        complete: bool = True,
    ) -> Optional[CareTask]:
        """Mark a task complete in the plan for (date, pet) and return its clone.

        If the task is 'daily' and ``complete`` is True, a new CareTask
        instance is automatically created for the next calendar day and saved
        via ``save_task`` (which also registers it on its pet). Unmarking a
        task (``complete=False``) does not create an occurrence. Returns the
        generated next-day CareTask, or None when none was created.
        """
        plan = self.load_plan(plan_date, pet_id)
        if plan is None:
            plan = self.build_plan(plan_date, pet_id)
        plan.mark_complete(task_id, complete)
        if not complete:
            return None

        task = self.load_task(task_id)
        if task is None or (task.frequency or "daily").lower() != "daily":
            return None

        next_day = _date.fromisoformat(plan_date) + timedelta(days=1)
        base_id = task.task_id.split("@", 1)[0]
        next_id = f"{base_id}@{next_day.isoformat()}"
        if self.load_task(next_id) is not None:
            return None  # already generated for tomorrow

        occurrence = task.create_next_occurrence(next_day)
        self.save_task(occurrence)
        return occurrence

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[CareTask]:
        """Return stored tasks filtered by pet name and/or completion status.

        ``pet_name`` matches case-insensitively against the pet's name.
        ``completed`` filters by completion: True keeps only tasks marked done
        in a plan, False only tasks not yet done. A task's completion state is
        looked up from the most recent plan (by date) that contains it; a task
        in no plan counts as not completed. Passing both filters requires the
        task to satisfy both. With no arguments, all stored tasks are returned.
        """
        completion_by_task: Dict[str, bool] = {}
        for plan in sorted(self.plans, key=lambda p: p.date):
            for tid in plan.task_ids:
                completion_by_task[tid] = plan.completion_status.get(tid, False)

        needle = pet_name.lower() if pet_name else None
        result: List[CareTask] = []
        for task in self.tasks:
            if needle is not None:
                pet = self.load_pet(task.pet_id)
                if pet is None or pet.name.lower() != needle:
                    continue
            if completed is not None and completion_by_task.get(task.task_id, False) != completed:
                continue
            result.append(task)
        return self.sort_by_time(result)

    def find_conflicts(self, plan_date: Union[str, _date], owner_id: str) -> List[tuple]:
        """Find time conflicts across all of an owner's pets for a given day.

        Merges every pet's plan for ``plan_date`` into one task list and reports
        overlapping (preferred_time, duration) intervals — both tasks on the
        same pet and tasks on different pets (e.g. two feedings at 08:00).
        Returns ``(task_a, task_b)`` pairs sorted by start time; empty list if
        there are no conflicts.
        """
        if isinstance(plan_date, _date):
            plan_date = plan_date.isoformat()

        owner = self.load_owner(owner_id)
        if owner is None:
            return []

        combined: List[CareTask] = []
        for pet in owner.pets:
            combined.extend(self.build_plan(plan_date, pet.pet_id).tasks)
        if not combined:
            return []
        return DailyPlan(plan_date, owner.pets[0].pet_id, tasks=combined).overlapping()

    def conflict_warnings(self, plan_date: Union[str, _date], owner_id: str) -> List[str]:
        """Return human-readable warnings for scheduling conflicts on a day.

        A lightweight, never-raises companion to ``find_conflicts``: every
        step tolerates bad input (missing owner/pets, malformed or missing
        times, bad dates, missing plan objects) by skipping the problem task
        or returning an empty list instead of crashing. Each warning is a
        ready-to-print string like "⚠ 08:00-08:10: 'Feed' (Buddy) overlaps
        'Meds' (Luna)".
        """
        warnings: List[str] = []
        try:
            if isinstance(plan_date, _date):
                plan_date = plan_date.isoformat()
            _date.fromisoformat(plan_date)  # validate early
        except (ValueError, TypeError):
            return warnings

        owner = self.load_owner(owner_id)
        if owner is None:
            return warnings

        scheduled: List[tuple] = []
        for pet in owner.pets:
            plan = self.load_plan(plan_date, pet.pet_id) or self.build_plan(
                plan_date, pet.pet_id
            )
            if plan is None:
                continue
            for task in plan.tasks:
                bounds = task.time_bounds()
                if bounds is not None:
                    scheduled.append((bounds, task, pet.name))

        scheduled.sort(key=lambda item: item[0])
        for i, (bounds_a, task_a, name_a) in enumerate(scheduled):
            for bounds_b, task_b, name_b in scheduled[i + 1:]:
                if bounds_b[0] >= bounds_a[1]:
                    break

                def fmt(minutes: int) -> str:
                    return f"{minutes // 60:02d}:{minutes % 60:02d}"

                warnings.append(
                    f"⚠ {fmt(bounds_a[0])}-{fmt(bounds_a[1])}: "
                    f"'{task_a.description}' ({name_a}) overlaps "
                    f"'{task_b.description}' ({name_b})"
                )
        return warnings

    @staticmethod
    def sort_by_time(
        tasks: List[CareTask], priority_tiebreak: bool = False
    ) -> List[CareTask]:
        """Return CareTask objects sorted by their time attribute (preferred_time).

        Sorting is numeric on (hour, minute) so it is independent of string
        formatting. Tasks without a preferred_time sort last. If
        ``priority_tiebreak`` is True, equal times are ordered high -> low
        priority.
        """
        priority_order = {"high": 0, "medium": 1, "low": 2}

        def key(task: CareTask):
            if task.preferred_time:
                h, m = map(int, task.preferred_time.split(":"))
            else:  # no time yet -> end of the day
                h, m = 24, 0
            tie = priority_order.get(task.priority, 3) if priority_tiebreak else 0
            return (h, m, tie)

        return sorted(tasks, key=key)
