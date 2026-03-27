import os
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, PRIORITY_EMOJI, CATEGORY_EMOJI

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

DATA_FILE = "data.json"

# ---------------------------------------------------------------------------
# Session state — load from disk on first run
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            st.session_state.owner = Owner.load_from_json(DATA_FILE)
        except Exception:
            st.session_state.owner = None
    else:
        st.session_state.owner = None


def save():
    """Persist current owner state to data.json."""
    if st.session_state.owner:
        st.session_state.owner.save_to_json(DATA_FILE)


# ---------------------------------------------------------------------------
# Section A: Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner Info")

with st.form("owner_form"):
    owner_name    = st.text_input("Your name",
                                  value=st.session_state.owner.name if st.session_state.owner else "Jordan")
    avail_minutes = st.number_input("Minutes available today", min_value=10, max_value=480,
                                    value=st.session_state.owner.available_minutes if st.session_state.owner else 90)
    submitted_owner = st.form_submit_button("Save owner")

if submitted_owner:
    existing_pets = st.session_state.owner.pets if st.session_state.owner else []
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(avail_minutes))
    for pet in existing_pets:
        st.session_state.owner.add_pet(pet)
    save()
    st.success(f"Saved: {owner_name} ({avail_minutes} min available)")

if st.session_state.owner is None:
    st.info("Fill in your name and available time above, then click Save owner.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section B: Pets
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Pets")

with st.form("pet_form"):
    pet_name      = st.text_input("Pet name", value="Mochi")
    pet_species   = st.selectbox("Species", ["dog", "cat", "other"])
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    existing_names = [p.name.lower() for p in owner.pets]
    if pet_name.lower() in existing_names:
        st.warning(f"A pet named '{pet_name}' already exists.")
    else:
        owner.add_pet(Pet(name=pet_name, species=pet_species))
        save()
        st.success(f"Added {pet_name} the {pet_species}!")

if owner.pets:
    for pet in owner.pets:
        st.write(f"- **{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------------------
# Section C: Tasks
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Tasks")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("task_form"):
        col1, col2 = st.columns(2)
        with col1:
            target_pet = st.selectbox("Assign to pet", [p.name for p in owner.pets])
            task_title = st.text_input("Task title", value="Morning walk")
            duration   = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            priority   = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col2:
            category   = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
            start_time = st.text_input("Start time (HH:MM, optional)", value="")
            frequency  = st.selectbox("Frequency", ["once", "daily", "weekly"])
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        pet = next(p for p in owner.pets if p.name == target_pet)
        pet.add_task(Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
            start_time=start_time.strip() or None,
            frequency=frequency,
        ))
        save()
        st.success(f"Added '{CATEGORY_EMOJI.get(category, '')} {task_title}' to {target_pet}!")

    all_rows = owner.get_all_tasks()
    if all_rows:
        st.write("**All tasks:**")
        st.table([{"pet": pn, **t.to_dict()} for pn, t in all_rows])
    else:
        st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Section D: Today's Schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Today's Schedule")

if st.button("Generate schedule", type="primary"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner=owner)
        scheduler.build_plan()

        st.subheader(f"{owner.name}'s plan — {owner.available_minutes} min available")

        # ── Conflict warnings ──
        conflicts = scheduler.find_conflicts()
        if conflicts:
            st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected.")
            with st.expander("See conflicts"):
                for (pn_a, ta), (pn_b, tb) in conflicts:
                    st.error(
                        f"**{CATEGORY_EMOJI.get(ta.category,'')} {ta.title}** "
                        f"({pn_a} @ {ta.start_time}, {ta.duration_minutes} min)  ↔  "
                        f"**{CATEGORY_EMOJI.get(tb.category,'')} {tb.title}** "
                        f"({pn_b} @ {tb.start_time}, {tb.duration_minutes} min)"
                    )

        # ── Scheduled tasks (chronological) ──
        if scheduler.scheduled_tasks:
            st.success(
                f"✅ {len(scheduler.scheduled_tasks)} task(s) scheduled — "
                f"{scheduler.total_scheduled_time()} of {owner.available_minutes} min used"
            )
            sorted_plan = scheduler.sort_by_time()
            st.write("**Schedule (chronological order):**")
            st.table([{"pet": pn, **t.to_dict()} for pn, t in sorted_plan])
        else:
            st.error("No tasks could fit in the available time.")

        # ── Next available slot suggestion ──
        slot_duration = st.number_input(
            "Find next free slot for a task of this duration (min):",
            min_value=5, max_value=120, value=15, key="slot_input"
        )
        next_slot = scheduler.find_next_slot(int(slot_duration))
        if next_slot:
            st.info(f"🕐 Next free {slot_duration}-min slot: **{next_slot}**")
        else:
            st.warning(f"No free {slot_duration}-min slot found between 07:00 and 21:00.")

        # ── Skipped tasks ──
        if scheduler.skipped_tasks:
            with st.expander(f"⏭️ Skipped ({len(scheduler.skipped_tasks)} tasks — not enough time)"):
                st.table([{"pet": pn, **t.to_dict()} for pn, t in scheduler.skipped_tasks])

        # ── Filter: incomplete tasks by pet ──
        if owner.pets:
            st.divider()
            st.write("**Filter: incomplete tasks by pet**")
            selected_pet = st.selectbox("Pet", [p.name for p in owner.pets], key="filter_pet")
            incomplete = scheduler.filter_tasks(pet_name=selected_pet, completed=False)
            if incomplete:
                st.table([{"pet": pn, **t.to_dict()} for pn, t in incomplete])
            else:
                st.info(f"No incomplete tasks for {selected_pet}.")

        # ── Full explanation ──
        with st.expander("Full explanation"):
            st.text(scheduler.explain_plan())

# ---------------------------------------------------------------------------
# Sidebar: data management
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("💾 Data")
    if os.path.exists(DATA_FILE):
        st.success(f"Auto-saved to {DATA_FILE}")
        if st.button("🗑️ Clear saved data"):
            os.remove(DATA_FILE)
            st.session_state.owner = None
            st.rerun()
    else:
        st.info("No saved data yet.")
