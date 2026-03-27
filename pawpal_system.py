from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import combinations
from typing import Optional
import json

PRIORITY_ORDER  = {"high": 3, "medium": 2, "low": 1}
PRIORITY_EMOJI  = {"high": "🔴", "medium": "🟡", "low": "🟢"}
CATEGORY_EMOJI  = {
    "walk": "🚶", "feeding": "🍖", "medication": "💊",
    "grooming": "✂️", "enrichment": "🎾",
}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str          # "low", "medium", "high"
    category: str          # "walk", "feeding", "medication", "grooming", "enrichment"
    completed: bool = False
    start_time: Optional[str] = None   # "HH:MM" — when the task is meant to begin
    frequency: str = "once"            # "once", "daily", "weekly"
    due_date: Optional[date] = None    # date this occurrence is due

    def mark_complete(self) -> Optional["Task"]:
        """Mark complete; return the next occurrence if recurring, else None."""
        self.completed = True
        if self.frequency == "daily":
            next_due = (self.due_date or date.today()) + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = (self.due_date or date.today()) + timedelta(weeks=1)
        else:
            return None
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            due_date=next_due,
        )

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"

    def to_dict(self) -> dict:
        """Return a display-ready dictionary with emoji indicators for priority and category."""
        return {
            "priority": f"{PRIORITY_EMOJI.get(self.priority, '')} {self.priority}",
            "title": f"{CATEGORY_EMOJI.get(self.category, '')} {self.title}",
            "duration_min": self.duration_minutes,
            "category": self.category,
            "start_time": self.start_time or "—",
            "frequency": self.frequency,
            "due_date": str(self.due_date) if self.due_date else "—",
            "completed": "✅" if self.completed else "⬜",
        }

    def to_json_dict(self) -> dict:
        """Return a serialisation-safe dictionary (no emoji, no sentinel strings)."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "completed": self.completed,
            "start_time": self.start_time,
            "frequency": self.frequency,
            "due_date": str(self.due_date) if self.due_date else None,
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

    def save_to_json(self, path: str = "data.json") -> None:
        """Serialise the owner, all pets, and all tasks to a JSON file."""
        payload = {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "preferences": self.preferences,
            "pets": [
                {
                    "name": pet.name,
                    "species": pet.species,
                    "tasks": [t.to_json_dict() for t in pet.tasks],
                }
                for pet in self.pets
            ],
        }
        with open(path, "w") as fh:
            json.dump(payload, fh, indent=2)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Deserialise an Owner (with pets and tasks) from a JSON file."""
        with open(path) as fh:
            data = json.load(fh)
        owner = cls(
            name=data["name"],
            available_minutes=data["available_minutes"],
            preferences=data.get("preferences", {}),
        )
        for pet_data in data.get("pets", []):
            pet = Pet(name=pet_data["name"], species=pet_data["species"])
            for t in pet_data.get("tasks", []):
                raw_date = t.get("due_date")
                pet.add_task(Task(
                    title=t["title"],
                    duration_minutes=t["duration_minutes"],
                    priority=t["priority"],
                    category=t["category"],
                    completed=t.get("completed", False),
                    start_time=t.get("start_time"),
                    frequency=t.get("frequency", "once"),
                    due_date=date.fromisoformat(raw_date) if raw_date else None,
                ))
            owner.add_pet(pet)
        return owner


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.scheduled_tasks: list[tuple[str, Task]] = []  # (pet_name, task)
        self.skipped_tasks: list[tuple[str, Task]] = []    # (pet_name, task)

    # ------------------------------------------------------------------
    # Core planning
    # ------------------------------------------------------------------

    def build_plan(self) -> list[tuple[str, Task]]:
        """Sort all pet tasks by priority and greedily schedule those that fit the time budget."""
        self.scheduled_tasks = []
        self.skipped_tasks = []

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

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self) -> list[tuple[str, Task]]:
        """Return scheduled_tasks sorted by start_time (HH:MM); tasks with no time sort last."""
        return sorted(
            self.scheduled_tasks,
            key=lambda pair: pair[1].start_time or "99:99"
        )

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[tuple[str, Task]]:
        """Filter all tasks by pet name and/or completion status; pass None to skip a filter."""
        results = self.owner.get_all_tasks()
        if pet_name is not None:
            results = [(pn, t) for pn, t in results if pn.lower() == pet_name.lower()]
        if completed is not None:
            results = [(pn, t) for pn, t in results if t.completed == completed]
        return results

    # ------------------------------------------------------------------
    # Recurring task completion
    # ------------------------------------------------------------------

    def complete_task(self, pet_name: str, task_title: str) -> Optional[Task]:
        """Mark a task complete and auto-schedule its next occurrence if it recurs."""
        for pet in self.owner.pets:
            if pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if task.title.lower() == task_title.lower() and not task.completed:
                    next_task = task.mark_complete()
                    if next_task:
                        pet.add_task(next_task)
                    return next_task
        return None

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def find_conflicts(self) -> list[tuple[tuple[str, Task], tuple[str, Task]]]:
        """Return pairs of scheduled tasks whose time windows overlap."""
        timed = [(pn, t) for pn, t in self.scheduled_tasks if t.start_time is not None]
        return [pair for pair in combinations(timed, 2) if _overlaps(*pair)]

    def find_next_slot(
        self,
        duration_minutes: int,
        day_start: str = "07:00",
        day_end: str = "21:00",
    ) -> Optional[str]:
        """Return the earliest free HH:MM slot that fits a task of the given duration.

        Scans the gaps between already-scheduled timed tasks from day_start to
        day_end. Returns None if no gap is large enough.
        """
        start = _time_to_minutes(day_start)
        end   = _time_to_minutes(day_end)

        # Collect timed tasks sorted chronologically
        timed = sorted(
            [(pn, t) for pn, t in self.scheduled_tasks if t.start_time],
            key=lambda pair: _time_to_minutes(pair[1].start_time),
        )

        cursor = start
        for _, task in timed:
            task_start = _time_to_minutes(task.start_time)
            if task_start - cursor >= duration_minutes:
                return _minutes_to_time(cursor)
            cursor = max(cursor, task_start + task.duration_minutes)

        # Check the gap after the last scheduled task
        if end - cursor >= duration_minutes:
            return _minutes_to_time(cursor)

        return None

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def explain_plan(self) -> str:
        """Return a formatted summary of scheduled and skipped tasks; call after build_plan()."""
        if not self.scheduled_tasks and not self.skipped_tasks:
            return "No plan built yet — call build_plan() first."

        lines = [f"Plan for {self.owner.name}  |  budget: {self.owner.available_minutes} min\n"]

        if self.scheduled_tasks:
            lines.append("Scheduled:")
            for pet_name, task in self.scheduled_tasks:
                time_tag = f" @ {task.start_time}" if task.start_time else ""
                lines.append(
                    f"  [{task.priority.upper():6}] {task.title} ({pet_name})"
                    f"{time_tag} — {task.duration_minutes} min  [{task.frequency}]"
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


# ------------------------------------------------------------------
# Module-level helper
# ------------------------------------------------------------------

def _time_to_minutes(hhmm: str) -> int:
    """Convert an 'HH:MM' string to an integer count of minutes since midnight."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_time(minutes: int) -> str:
    """Convert an integer minute-offset since midnight to an 'HH:MM' string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _overlaps(a: tuple, b: tuple) -> bool:
    """Return True if two (pet_name, Task) pairs have overlapping time windows.

    Uses the standard interval-overlap test: [start_a, end_a) overlaps
    [start_b, end_b) when start_a < end_b AND start_b < end_a.
    """
    start_a = _time_to_minutes(a[1].start_time)
    start_b = _time_to_minutes(b[1].start_time)
    return start_a < start_b + b[1].duration_minutes and start_b < start_a + a[1].duration_minutes
