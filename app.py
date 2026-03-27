import streamlit as st

# Step 1: import the logic layer
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Step 2: initialise session state — runs only on the very first page load
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None          # Owner object, set when form is submitted

# ---------------------------------------------------------------------------
# Section A: Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner Info")

with st.form("owner_form"):
    owner_name      = st.text_input("Your name", value="Jordan")
    avail_minutes   = st.number_input("Minutes available today", min_value=10, max_value=480, value=90)
    submitted_owner = st.form_submit_button("Save owner")

if submitted_owner:
    # Create a fresh Owner and carry over any pets that already existed
    existing_pets = st.session_state.owner.pets if st.session_state.owner else []
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(avail_minutes))
    for pet in existing_pets:
        st.session_state.owner.add_pet(pet)
    st.success(f"Owner saved: {owner_name} ({avail_minutes} min available)")

if st.session_state.owner is None:
    st.info("Fill in your name and available time above, then click Save owner.")
    st.stop()   # nothing else can work without an owner

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section B: Add a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Pets")

with st.form("pet_form"):
    pet_name        = st.text_input("Pet name", value="Mochi")
    pet_species     = st.selectbox("Species", ["dog", "cat", "other"])
    submitted_pet   = st.form_submit_button("Add pet")

if submitted_pet:
    # Avoid duplicate pet names
    existing_names = [p.name.lower() for p in owner.pets]
    if pet_name.lower() in existing_names:
        st.warning(f"A pet named '{pet_name}' already exists.")
    else:
        owner.add_pet(Pet(name=pet_name, species=pet_species))
        st.success(f"Added {pet_name} the {pet_species}!")

if owner.pets:
    st.write("**Your pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.name} ({pet.species}) — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------------------
# Section C: Add a task to a pet
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Tasks")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("task_form"):
        target_pet  = st.selectbox("Assign to pet", [p.name for p in owner.pets])
        task_title  = st.text_input("Task title", value="Morning walk")
        duration    = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority    = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        category    = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        pet = next(p for p in owner.pets if p.name == target_pet)
        pet.add_task(Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
        ))
        st.success(f"Added '{task_title}' to {target_pet}!")

    # Show all tasks grouped by pet
    all_rows = owner.get_all_tasks()
    if all_rows:
        st.write("**All tasks:**")
        st.table([
            {"pet": pet_name, **task.to_dict()}
            for pet_name, task in all_rows
        ])
    else:
        st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Section D: Generate the schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Today's Schedule")

if st.button("Generate schedule", type="primary"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=owner)
        scheduler.build_plan()
        st.subheader(f"Plan for {owner.name}  —  {owner.available_minutes} min available")

        if scheduler.scheduled_tasks:
            st.success(f"Scheduled {len(scheduler.scheduled_tasks)} task(s) "
                       f"({scheduler.total_scheduled_time()} min used)")
            st.table([
                {"pet": pname, **task.to_dict()}
                for pname, task in scheduler.scheduled_tasks
            ])
        else:
            st.error("No tasks could fit in the available time.")

        if scheduler.skipped_tasks:
            with st.expander("Skipped tasks (not enough time)"):
                st.table([
                    {"pet": pname, **task.to_dict()}
                    for pname, task in scheduler.skipped_tasks
                ])

        with st.expander("Full explanation"):
            st.text(scheduler.explain_plan())
