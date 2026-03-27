from dataclasses import dataclass, field
from typing import Optional

PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    category: str  # "walk", "feeding", "medication", "grooming", "enrichment"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "completed": self.completed,
        }


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the first task whose title matches (case-insensitive)."""
        self.tasks = [t for t in self.tasks if t.title.lower() != title.lower()]

    def get_tasks_by_priority(self) -> list[Task]:
        """Return the task list sorted from high to low priority."""
        return sorted(self.tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 0), reverse=True)


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: Optional[dict] = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences or {}
        self.pets: list[Pet] = []

    def set_availability(self, minutes: int) -> None:
        """Update how many minutes the owner has available today."""
        self.available_minutes = minutes

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name (case-insensitive)."""
        self.pets = [p for p in self.pets if p.name.lower() != name.lower()]

    def get_all_tasks(self) -> list[tuple[str, Task]]:
        """Return every task across all pets as (pet_name, task) pairs."""
        return [(pet.name, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.scheduled_tasks: list[tuple[str, Task]] = []  # (pet_name, task)
        self.skipped_tasks: list[tuple[str, Task]] = []    # (pet_name, task)

    def build_plan(self) -> list[tuple[str, Task]]:
        """Sort all pet tasks by priority and greedily schedule those that fit the time budget."""
        self.scheduled_tasks = []
        self.skipped_tasks = []

        # Collect and sort all tasks across every pet by priority
        all_tasks = self.owner.get_all_tasks()
        all_tasks.sort(key=lambda pair: PRIORITY_ORDER.get(pair[1].priority, 0), reverse=True)

        remaining = self.owner.available_minutes
        for pet_name, task in all_tasks:
            if task.duration_minutes <= remaining:
                self.scheduled_tasks.append((pet_name, task))
                remaining -= task.duration_minutes
            else:
                self.skipped_tasks.append((pet_name, task))

        return self.scheduled_tasks

    def explain_plan(self) -> str:
        """Return a formatted summary of scheduled and skipped tasks; call after build_plan()."""
        if not self.scheduled_tasks and not self.skipped_tasks:
            return "No plan built yet — call build_plan() first."

        lines = [
            f"Plan for {self.owner.name}  |  budget: {self.owner.available_minutes} min\n"
        ]

        if self.scheduled_tasks:
            lines.append("Scheduled:")
            for pet_name, task in self.scheduled_tasks:
                lines.append(
                    f"  [{task.priority.upper():6}] {task.title} ({pet_name}) — {task.duration_minutes} min"
                )
            lines.append(f"\n  Total time used: {self.total_scheduled_time()} min")
        else:
            lines.append("  No tasks could fit in the available time.")

        if self.skipped_tasks:
            lines.append("\nSkipped (insufficient time remaining):")
            for pet_name, task in self.skipped_tasks:
                lines.append(
                    f"  - {task.title} ({pet_name}) — {task.duration_minutes} min, {task.priority} priority"
                )

        return "\n".join(lines)

    def total_scheduled_time(self) -> int:
        """Return the total duration in minutes of all scheduled tasks."""
        return sum(task.duration_minutes for _, task in self.scheduled_tasks)
