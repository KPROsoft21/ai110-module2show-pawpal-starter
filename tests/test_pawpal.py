from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Helpers — reusable setup so each test stays short
# ---------------------------------------------------------------------------

def make_owner(minutes: int = 120) -> Owner:
    owner = Owner(name="Jordan", available_minutes=minutes)
    return owner


def make_scheduler_with_tasks(*tasks_with_pet) -> Scheduler:
    """Create a Scheduler pre-loaded with (pet_name, Task) pairs and a built plan."""
    owner = make_owner()
    pets: dict[str, Pet] = {}
    for pet_name, task in tasks_with_pet:
        if pet_name not in pets:
            pets[pet_name] = Pet(name=pet_name, species="dog")
            owner.add_pet(pets[pet_name])
        pets[pet_name].add_task(task)
    scheduler = Scheduler(owner=owner)
    scheduler.build_plan()
    return scheduler


# ---------------------------------------------------------------------------
# Existing tests (kept)
# ---------------------------------------------------------------------------

def test_mark_complete_changes_task_status():
    """Calling mark_complete() should set completed to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high", category="walk")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list by one."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", category="feeding"))

    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks added out of order should come back sorted earliest start_time first."""
    scheduler = make_scheduler_with_tasks(
        ("Mochi", Task("Evening walk", 30, "medium", "walk",      start_time="18:00")),
        ("Mochi", Task("Breakfast",    10, "high",   "feeding",   start_time="07:30")),
        ("Mochi", Task("Midday meds",   5, "high",   "medication",start_time="12:00")),
    )

    sorted_tasks = scheduler.sort_by_time()
    times = [task.start_time for _, task in sorted_tasks]

    assert times == ["07:30", "12:00", "18:00"]


def test_sort_by_time_tasks_without_start_time_go_last():
    """Tasks with no start_time should appear at the end of the sorted list."""
    scheduler = make_scheduler_with_tasks(
        ("Mochi", Task("Evening walk", 30, "medium", "walk",    start_time="18:00")),
        ("Mochi", Task("Anytime task", 10, "low",    "grooming")),          # no start_time
        ("Mochi", Task("Breakfast",    10, "high",   "feeding", start_time="07:30")),
    )

    sorted_tasks = scheduler.sort_by_time()
    last_pet_name, last_task = sorted_tasks[-1]

    assert last_task.title == "Anytime task"


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------

def test_daily_task_creates_next_occurrence_due_tomorrow():
    """Completing a daily task should return a new Task due one day later."""
    today = date.today()
    task = Task("Breakfast", 10, "high", "feeding", frequency="daily", due_date=today)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_weekly_task_creates_next_occurrence_due_in_seven_days():
    """Completing a weekly task should return a new Task due seven days later."""
    today = date.today()
    task = Task("Grooming", 15, "medium", "grooming", frequency="weekly", due_date=today)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_once_task_returns_none_on_complete():
    """Completing a one-time task should return None (no next occurrence)."""
    task = Task("Vet visit", 60, "high", "medication", frequency="once")

    next_task = task.mark_complete()

    assert next_task is None


def test_complete_task_auto_adds_recurrence_to_pet():
    """Scheduler.complete_task() should add the next occurrence to the pet's task list."""
    owner = make_owner()
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Breakfast", 10, "high", "feeding", frequency="daily", due_date=date.today()))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.build_plan()
    scheduler.complete_task("Mochi", "Breakfast")

    titles = [t.title for t in pet.tasks]
    assert titles.count("Breakfast") == 2   # original (completed) + new occurrence


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_find_conflicts_flags_overlapping_tasks():
    """Two tasks whose time windows overlap should appear as a conflict pair."""
    scheduler = make_scheduler_with_tasks(
        ("Mochi", Task("Walk",     30, "high", "walk",    start_time="08:00")),
        ("Mochi", Task("Grooming", 20, "high", "grooming",start_time="08:15")),  # starts inside Walk
    )

    conflicts = scheduler.find_conflicts()

    assert len(conflicts) == 1


def test_find_conflicts_ignores_non_overlapping_tasks():
    """Two tasks that do not overlap should produce no conflicts."""
    scheduler = make_scheduler_with_tasks(
        ("Mochi", Task("Walk",      30, "high", "walk",    start_time="08:00")),
        ("Mochi", Task("Breakfast", 10, "high", "feeding", start_time="09:00")),  # starts after Walk ends
    )

    conflicts = scheduler.find_conflicts()

    assert len(conflicts) == 0


def test_find_conflicts_returns_empty_when_no_start_times():
    """Tasks without start_time set should never trigger a conflict."""
    scheduler = make_scheduler_with_tasks(
        ("Mochi", Task("Walk",      30, "high", "walk")),
        ("Mochi", Task("Breakfast", 10, "high", "feeding")),
    )

    conflicts = scheduler.find_conflicts()

    assert conflicts == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_scheduler_with_no_tasks_produces_empty_plan():
    """A scheduler built with no tasks should have empty scheduled and skipped lists."""
    owner = make_owner()
    owner.add_pet(Pet(name="Mochi", species="dog"))   # pet exists but has no tasks
    scheduler = Scheduler(owner=owner)
    scheduler.build_plan()

    assert scheduler.scheduled_tasks == []
    assert scheduler.skipped_tasks == []


def test_task_exceeding_budget_goes_to_skipped():
    """A task longer than available_minutes should land in skipped_tasks, not scheduled_tasks."""
    owner = Owner(name="Jordan", available_minutes=10)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Long walk", 60, "high", "walk"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.build_plan()

    assert len(scheduler.scheduled_tasks) == 0
    assert len(scheduler.skipped_tasks) == 1


def test_build_plan_is_idempotent():
    """Calling build_plan() twice should produce the same result, not double the tasks."""
    owner = make_owner()
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Breakfast", 10, "high", "feeding"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)
    scheduler.build_plan()
    scheduler.build_plan()   # second call

    assert len(scheduler.scheduled_tasks) == 1
