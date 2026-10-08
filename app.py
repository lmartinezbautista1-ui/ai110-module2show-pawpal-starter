from datetime import date

import streamlit as st

from pawpal_system import App, CareTask, DailyPlan, Owner, Pet

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ demo app.

The UI below is connected to the domain classes in `pawpal_system.py`.
Add pets and care tasks, then generate a daily schedule.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

Add your pet and its tasks below, then build a plan for today.
"""
    )

st.divider()

# --- Session-state "vault": create the App and Owner once per session --------
if "pawpal" not in st.session_state:
    st.session_state.pawpal = App()

if "owner" not in st.session_state:
    st.session_state.owner = Owner("owner-001", "Jordan", "jordan@example.com")
    st.session_state.pawpal.save_owner(st.session_state.owner)

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None


# --- Add a Pet ---------------------------------------------------------------
st.subheader("Add a Pet")

col1, col2, col3, col4 = st.columns(4)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    breed = st.text_input("Breed", value="Shiba Inu")
with col4:
    age = st.number_input("Age (years)", min_value=0, max_value=40, value=2)

if st.button("Add pet"):
    pet_id = f"pet-{len(st.session_state.pawpal.pets) + 1:03d}"
    pet = Pet(pet_id, st.session_state.owner.owner_id, pet_name, species, breed, int(age))
    st.session_state.pawpal.save_pet(pet)
    st.success(f"Saved pet **{pet.name}** ({pet.pet_id}) for owner {st.session_state.owner.name}.")

# Show the pets actually stored in the App (via the owner relationship).
owner = st.session_state.owner
if owner.pets:
    st.write("Current pets:")
    st.table(
        [{"pet_id": p.pet_id, "name": p.name, "species": p.species, "breed": p.breed, "age": p.age}
         for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Schedule a Task ----------------------------------------------------------
st.subheader("Schedule a Task")
st.caption("Tasks are saved with `App.save_task` and attached to the chosen pet.")

pets = st.session_state.pawpal.pets
if not pets:
    st.info("Add a pet first, then you can schedule its tasks.")
    st.subheader("Build Schedule")
    st.caption("Available once you've added a pet and at least one task.")
else:
    pet_options = {f"{p.name} ({p.pet_id})": p for p in pets}

    col1, col2 = st.columns(2)
    with col1:
        pet_choice = st.selectbox("Pet", list(pet_options.keys()))
    with col2:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

    task_title = st.text_input("Task title", value="Morning walk")

    col1, col2, col3 = st.columns(3)
    with col1:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col2:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        preferred_time = st.text_input("Preferred time (HH:MM)", value="08:00")

    if st.button("Add task"):
        pet = pet_options[pet_choice]
        task_id = f"task-{len(st.session_state.pawpal.tasks) + 1:03d}"
        task = CareTask(
            task_id,
            pet.pet_id,
            task_title,
            frequency,
            duration_minutes=int(duration),
            priority=priority,
            preferred_time=preferred_time or None,
        )
        st.session_state.pawpal.save_task(task)
        st.success(f"Saved task **{task.description}** for {pet.name}.")

    # Show the tasks actually stored in the App.
    if st.session_state.pawpal.tasks:
        st.write("Current tasks:")
        st.table(
            [
                {
                    "task_id": t.task_id,
                    "pet": (pet.name if (pet := st.session_state.pawpal.load_pet(t.pet_id)) else t.pet_id),
                    "description": t.description,
                    "frequency": t.frequency,
                    "duration_minutes": t.duration_minutes,
                    "priority": t.priority,
                    "preferred_time": t.preferred_time,
                }
                for t in st.session_state.pawpal.tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

    st.divider()

    # --- Build the Daily Plan -------------------------------------------------
    st.subheader("Build Schedule")
    st.caption("This calls `App.build_plan` and displays the resulting DailyPlan.")

    selected_pet = pet_options[pet_choice]

    if st.button("Generate schedule"):
        plan = st.session_state.pawpal.build_plan(date.today(), selected_pet.pet_id)
        st.session_state.last_plan = plan

    plan: DailyPlan | None = st.session_state.last_plan
    if plan is not None:
        pet = st.session_state.pawpal.load_pet(plan.pet_id)
        st.markdown(f"### Schedule for **{pet.name}** — {plan.date}")
        st.progress(plan.progress(), text=f"{int(plan.progress() * 100)}% complete")

        if plan.tasks:
            ordered = sorted(plan.tasks, key=lambda t: t.preferred_time or "99:99")
            for task in ordered:
                done = plan.completion_status.get(task.task_id, False)
                cols = st.columns([1, 4, 3, 2, 1])
                cols[0].write(task.preferred_time or "—")
                cols[1].write(f"~~{task.description}~~" if done else task.description)
                cols[2].write(f"{task.duration_minutes} min · {task.priority} priority")
                cols[3].write(f"_{task.frequency}_")
                if cols[4].button("✅" if not done else "↩️", key=f"done-{task.task_id}"):
                    plan.mark_complete(task.task_id, not done)
                    st.rerun()
            st.caption(f"Task count: {len(plan.tasks)} — sorted by preferred time.")
        else:
            st.warning("No care tasks are due today for this pet.")
