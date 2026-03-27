from datetime import date
from tabulate import tabulate
from pawpal_system import Task, Pet, Owner, Scheduler, PRIORITY_EMOJI, CATEGORY_EMOJI

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog")
luna  = Pet(name="Luna",  species="cat")

mochi.add_task(Task("Evening walk",    30, "medium", "walk",       start_time="18:00", frequency="daily",  due_date=date.today()))
mochi.add_task(Task("Breakfast",       10, "high",   "feeding",    start_time="07:30", frequency="daily",  due_date=date.today()))
mochi.add_task(Task("Flea medication",  5, "high",   "medication", start_time="08:00", frequency="weekly", due_date=date.today()))
mochi.add_task(Task("Fetch session",   20, "low",    "enrichment", start_time="16:00"))
mochi.add_task(Task("Grooming",        15, "medium", "grooming",   start_time="08:00"))  # conflict with Flea meds

luna.add_task(Task("Breakfast",         5, "high",   "feeding",    start_time="07:45", frequency="daily",  due_date=date.today()))
luna.add_task(Task("Litter box clean", 10, "medium", "grooming",   start_time="09:00"))
luna.add_task(Task("Laser play",       15, "low",    "enrichment", start_time="17:30"))
luna.add_task(Task("Outdoor time",     20, "medium", "enrichment", start_time="07:30"))  # conflict with Mochi Breakfast

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner=owner)
scheduler.build_plan()


def _row(pet_name, task):
    pri = f"{PRIORITY_EMOJI.get(task.priority, '')} {task.priority}"
    cat = f"{CATEGORY_EMOJI.get(task.category, '')} {task.category}"
    return [pet_name, pri, task.title, task.duration_minutes, task.start_time or "—", task.frequency]


HEADERS = ["pet", "priority", "title", "min", "start", "freq"]

# ---------------------------------------------------------------------------
# 1. Priority-ordered plan
# ---------------------------------------------------------------------------
print("\n" + "═" * 62)
print("  TODAY'S SCHEDULE  (priority order)")
print("═" * 62)
print(tabulate([_row(pn, t) for pn, t in scheduler.scheduled_tasks], headers=HEADERS, tablefmt="rounded_outline"))
print(f"\n  ✅ {scheduler.total_scheduled_time()} / {owner.available_minutes} min used")

# ---------------------------------------------------------------------------
# 2. Chronological sort
# ---------------------------------------------------------------------------
print("\n" + "═" * 62)
print("  SORTED BY START TIME")
print("═" * 62)
print(tabulate([_row(pn, t) for pn, t in scheduler.sort_by_time()], headers=HEADERS, tablefmt="rounded_outline"))

# ---------------------------------------------------------------------------
# 3. Next available slot (Challenge 1)
# ---------------------------------------------------------------------------
print("\n" + "═" * 62)
print("  NEXT AVAILABLE SLOT")
print("═" * 62)
for mins in (10, 20, 45):
    slot = scheduler.find_next_slot(mins)
    result = f"🕐 {slot}" if slot else "none found"
    print(f"  {mins:3d}-min task → {result}")

# ---------------------------------------------------------------------------
# 4. Conflicts
# ---------------------------------------------------------------------------
print("\n" + "═" * 62)
print("  CONFLICT DETECTION")
print("═" * 62)
conflicts = scheduler.find_conflicts()
if conflicts:
    print(f"  ⚠️  {len(conflicts)} conflict(s):\n")
    for (pn_a, ta), (pn_b, tb) in conflicts:
        print(f"  • {ta.title} ({pn_a} @ {ta.start_time}, {ta.duration_minutes} min)")
        print(f"    overlaps {tb.title} ({pn_b} @ {tb.start_time}, {tb.duration_minutes} min)\n")
else:
    print("  No conflicts.")

# ---------------------------------------------------------------------------
# 5. Recurring task + filter
# ---------------------------------------------------------------------------
print("\n" + "═" * 62)
print("  RECURRING: complete Mochi's Breakfast")
print("═" * 62)
next_task = scheduler.complete_task("Mochi", "Breakfast")
if next_task:
    print(f"  Next occurrence → due {next_task.due_date}")

print("\n  Mochi's remaining incomplete tasks:")
rows = [[t.title, t.priority, t.start_time or "—"] for _, t in scheduler.filter_tasks("Mochi", completed=False)]
print(tabulate(rows, headers=["title", "priority", "start"], tablefmt="simple"))

# ---------------------------------------------------------------------------
# 6. JSON persistence (Challenge 2)
# ---------------------------------------------------------------------------
print("\n" + "═" * 62)
print("  JSON PERSISTENCE")
print("═" * 62)
owner.save_to_json("data.json")
print("  Saved → data.json")

restored = Owner.load_from_json("data.json")
print(f"  Loaded → {restored.name}, {len(restored.pets)} pet(s), "
      f"{sum(len(p.tasks) for p in restored.pets)} task(s)")
print("═" * 62)
