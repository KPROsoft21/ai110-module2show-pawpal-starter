from pawpal_system import Task, Pet, Owner, Scheduler

# --- Setup owner ---
owner = Owner(name="Jordan", available_minutes=90)

# --- Create pets ---
mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")

# --- Add tasks to Mochi (dog) ---
mochi.add_task(Task(title="Morning walk",    duration_minutes=30, priority="high",   category="walk"))
mochi.add_task(Task(title="Breakfast",       duration_minutes=10, priority="high",   category="feeding"))
mochi.add_task(Task(title="Flea medication", duration_minutes=5,  priority="medium", category="medication"))
mochi.add_task(Task(title="Fetch session",   duration_minutes=20, priority="low",    category="enrichment"))

# --- Add tasks to Luna (cat) ---
luna.add_task(Task(title="Breakfast",        duration_minutes=5,  priority="high",   category="feeding"))
luna.add_task(Task(title="Litter box clean", duration_minutes=10, priority="medium", category="grooming"))
luna.add_task(Task(title="Laser play",       duration_minutes=15, priority="low",    category="enrichment"))

# --- Register pets with owner ---
owner.add_pet(mochi)
owner.add_pet(luna)

# --- Run scheduler ---
scheduler = Scheduler(owner=owner)
scheduler.build_plan()

# --- Print results ---
print("=" * 50)
print("         TODAY'S SCHEDULE")
print("=" * 50)
print(scheduler.explain_plan())
print("=" * 50)
