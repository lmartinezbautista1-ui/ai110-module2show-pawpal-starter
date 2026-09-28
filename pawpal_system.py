"""
PawPal+ — class skeletons generated from class_diagram.mmd.

Attributes and method signatures follow the UML; all method bodies are stubs (no logic yet).
"""

from typing import Dict, List, Optional


class Owner:
    """A pet owner with basic contact info."""

    def __init__(self, owner_id: str, name: str, contact_info: str):
        self.owner_id = owner_id
        self.name = name
        self.contact_info = contact_info


class Pet:
    """A pet owned by an owner; has care tasks scheduled for it."""

    def __init__(self, pet_id: str, owner_id: str, name: str, species: str, breed: str, age: int):
        self.pet_id = pet_id
        self.owner_id = owner_id
        self.name = name
        self.species = species
        self.breed = breed
        self.age = age


class CareTask:
    """A single care task for a pet (e.g. feeding, walk, medication)."""

    def __init__(self, task_id: str, pet_id: str, description: str, frequency: str):
        self.task_id = task_id
        self.pet_id = pet_id
        self.description = description
        self.frequency = frequency


class DailyPlan:
    """A plan for one day: which tasks are scheduled and their completion status."""

    def __init__(self, date: str, pet_id: str, task_ids: List[str], completion_status: Dict[str, str]):
        self.date = date
        self.pet_id = pet_id
        self.task_ids = task_ids
        self.completion_status = completion_status


class App:
    """Top-level application: stores owners, pets, tasks and plans."""

    def __init__(self):
        self.owners: List[Owner] = []
        self.pets: List[Pet] = []
        self.tasks: List[CareTask] = []
        self.plans: List[DailyPlan] = []

    def save_owner(self, owner: Owner) -> None:
        """Store an owner in the owners list."""
        pass

    def load_owner(self, owner_id: str) -> Optional[Owner]:
        """Look up an owner by id; return the Owner or None."""
        pass

    def save_pet(self, pet: Pet) -> None:
        """Store a pet in the pets list."""
        pass

    def save_task(self, task: CareTask) -> None:
        """Store a care task in the tasks list."""
        pass

    def load_tasks(self, pet_id: str) -> List[CareTask]:
        """Return all care tasks belonging to the given pet."""
        pass

    def save_plan(self, plan: DailyPlan) -> None:
        """Store a daily plan in the plans list."""
        pass

    def load_plan(self, date: str, pet_id: str) -> Optional[DailyPlan]:
        """Look up the plan for a given date and pet; return the DailyPlan or None."""
        pass
