from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog")
luna  = Pet(name="Luna",  species="cat")

# Add tasks OUT OF ORDER intentionally to demo sort_by_time()
mochi.add_task(Task("Evening walk",    30, "medium", "walk",      start_time="18:00", frequency="daily",  due_date=date.today()))
mochi.add_task(Task("Breakfast",       10, "high",   "feeding",   start_time="07:30", frequency="daily",  due_date=date.today()))
mochi.add_task(Task("Flea medication",  5, "high",   "medication",start_time="08:00", frequency="weekly", due_date=date.today()))
mochi.add_task(Task("Fetch session",   20, "low",    "enrichment",start_time="16:00"))
# Deliberate conflict: grooming starts at 08:00, same window as Flea medication (08:00–08:05)
mochi.add_task(Task("Grooming",        15, "medium", "grooming",  start_time="08:00"))

luna.add_task(Task("Breakfast",        5,  "high",   "feeding",   start_time="07:45", frequency="daily",  due_date=date.today()))
# Deliberate conflict: outdoor time starts at 07:30, overlaps Mochi's Breakfast (07:30–07:40)
luna.add_task(Task("Outdoor time",     20, "medium", "enrichment",start_time="07:30"))
luna.add_task(Task("Litter box clean", 10, "medium", "grooming",  start_time="09:00"))
luna.add_task(Task("Laser play",       15, "low",    "enrichment",start_time="17:30"))

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner=owner)
scheduler.build_plan()

# ---------------------------------------------------------------------------
# 1. Scheduled plan (priority order)
# ---------------------------------------------------------------------------
print("=" * 55)
print("  TODAY'S SCHEDULE  (priority order)")
print("=" * 55)
print(scheduler.explain_plan())

# ---------------------------------------------------------------------------
# 2. Sort by start_time
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  SORTED BY START TIME")
print("=" * 55)
for pet_name, task in scheduler.sort_by_time():
    print(f"  {task.start_time}  {task.title} ({pet_name})  — {task.duration_minutes} min")

# ---------------------------------------------------------------------------
# 3. Filter: incomplete tasks for Mochi only
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  FILTER: Mochi's incomplete tasks")
print("=" * 55)
for pet_name, task in scheduler.filter_tasks(pet_name="Mochi", completed=False):
    print(f"  [ ] {task.title} — {task.priority} priority")

# ---------------------------------------------------------------------------
# 4. Recurring task — complete Mochi's Breakfast, auto-schedule next
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  RECURRING TASK: complete Mochi's Breakfast")
print("=" * 55)
next_task = scheduler.complete_task("Mochi", "Breakfast")
if next_task:
    print(f"  Next occurrence created: '{next_task.title}' due {next_task.due_date}")
else:
    print("  One-time task — no next occurrence.")

# Confirm the original is now marked done
for pet_name, task in scheduler.filter_tasks(pet_name="Mochi"):
    if task.title == "Breakfast":
        print(f"  Original completed={task.completed}  due={task.due_date}")

# ---------------------------------------------------------------------------
# 5. Conflict detection
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  CONFLICT DETECTION")
print("=" * 55)
conflicts = scheduler.find_conflicts()
if conflicts:
    print(f"  WARNING: {len(conflicts)} scheduling conflict(s) found!\n")
    for (pn_a, ta), (pn_b, tb) in conflicts:
        end_a = f"{ta.start_time} + {ta.duration_minutes} min"
        end_b = f"{tb.start_time} + {tb.duration_minutes} min"
        print(f"  ⚠  '{ta.title}' ({pn_a} @ {end_a})")
        print(f"     overlaps")
        print(f"     '{tb.title}' ({pn_b} @ {end_b})")
        print()
else:
    print("  No time conflicts detected.")
print("=" * 55)
