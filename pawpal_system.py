from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    category: str  # "walk", "feeding", "medication", "grooming", "enrichment"
    completed: bool = False

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        pass

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by title from this pet's task list."""
        pass

    def get_tasks_by_priority(self) -> list[Task]:
        """Return the task list sorted from high to low priority."""
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: Optional[dict] = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences or {}

    def set_availability(self, minutes: int) -> None:
        """Update how many minutes the owner has available today."""
        pass


class Scheduler:
    def __init__(self, pet: Pet, owner: Owner):
        self.pet = pet
        self.available_minutes = owner.available_minutes
        self.scheduled_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []

    def build_plan(self) -> list[Task]:
        """Select and order tasks that fit within available_minutes.

        Higher-priority tasks should be scheduled first. Tasks that don't
        fit in the remaining time are added to skipped_tasks.
        """
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the schedule.

        Should describe which tasks were included and why others were skipped.
        """
        pass

    def total_scheduled_time(self) -> int:
        """Return the total duration in minutes of all scheduled tasks."""
        pass
