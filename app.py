import streamlit as st
from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    TaskType, PetType
)
from ai_advisor import get_pet_recommendations

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+")

st.markdown(
    """
An intelligent pet care planner that generates optimized daily schedules and
AI-powered care recommendations grounded in a curated pet care knowledge base.
"""
)

# ============================================================================
# Session State Initialization
# ============================================================================

def initialize_session_state():
    if "owner" not in st.session_state:
        st.session_state.owner = None
    if "scheduler" not in st.session_state:
        st.session_state.scheduler = None


initialize_session_state()

# ============================================================================
# Sidebar: Owner Setup
# ============================================================================

st.sidebar.subheader("👤 Owner Setup")

owner_name = st.sidebar.text_input(
    "Owner name",
    value="Jordan" if st.session_state.owner is None else st.session_state.owner.name,
    key="owner_name_input"
)

available_hours = st.sidebar.slider(
    "Available hours per day",
    min_value=0.5,
    max_value=24.0,
    value=4.0 if st.session_state.owner is None else st.session_state.owner.daily_hours_available,
    step=0.5,
    key="hours_slider"
)

if st.sidebar.button("Create/Update Owner", key="create_owner_btn"):
    st.session_state.owner = Owner(
        name=owner_name,
        daily_hours_available=available_hours
    )
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)
    st.sidebar.success(f"Owner '{owner_name}' created!")

# ============================================================================
# Sidebar: Add Pets
# ============================================================================

if st.session_state.owner is not None:
    st.sidebar.divider()
    st.sidebar.subheader("🐶 Add Pets")

    pet_name = st.sidebar.text_input("Pet name", key="pet_name_input")
    pet_type = st.sidebar.selectbox(
        "Species",
        ["dog", "cat", "bird", "rabbit", "other"],
        key="pet_type_select"
    )
    pet_age = st.sidebar.number_input(
        "Age (years)",
        min_value=0,
        max_value=30,
        value=3,
        key="pet_age_input"
    )
    special_needs = st.sidebar.text_input(
        "Special needs (comma-separated)",
        placeholder="e.g., senior, diabetic, needs_exercise",
        key="special_needs_input"
    )

    if st.sidebar.button("Add Pet", key="add_pet_btn"):
        if pet_name:
            needs_list = [n.strip() for n in special_needs.split(",") if n.strip()]
            pet = Pet(
                name=pet_name,
                pet_type=PetType[pet_type.upper()],
                age=pet_age,
                special_needs=needs_list
            )
            st.session_state.scheduler.add_pet(pet)
            st.sidebar.success(f"Pet '{pet_name}' added!")
            st.rerun()

    if st.session_state.scheduler.pets:
        st.sidebar.markdown("**Your Pets:**")
        for pet in st.session_state.scheduler.pets:
            st.sidebar.markdown(f"- {pet.get_info()}")

# ============================================================================
# Main Content
# ============================================================================

if st.session_state.owner is not None and st.session_state.scheduler is not None:

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📋 Add Tasks", "📅 Daily Schedule", "⚙️ Manage Tasks", "📊 Analytics", "🤖 AI Advisor"]
    )

    # ========================================================================
    # TAB 1: Add Tasks
    # ========================================================================

    with tab1:
        st.subheader("Add a New Task")

        col1, col2 = st.columns(2)

        with col1:
            task_name = st.text_input("Task name", key="task_name_input")
            task_type = st.selectbox(
                "Task type",
                [t.value for t in TaskType],
                key="task_type_select"
            )
            duration = st.number_input(
                "Duration (minutes)",
                min_value=5,
                max_value=480,
                value=30,
                step=5,
                key="duration_input"
            )

        with col2:
            priority = st.slider(
                "Priority",
                min_value=1,
                max_value=5,
                value=3,
                key="priority_slider"
            )
            scheduled_time = st.text_input(
                "Scheduled time (HH:MM)",
                value="08:00",
                key="time_input",
                placeholder="08:00"
            )
            assigned_pet = st.selectbox(
                "Assign to pet",
                [p.name for p in st.session_state.scheduler.pets] + ["General"],
                key="pet_select"
            )

        description = st.text_area(
            "Description",
            placeholder="What is this task about?",
            key="description_input"
        )

        if st.button("Add Task", key="add_task_btn"):
            if task_name and assigned_pet:
                assign_pet = None if assigned_pet == "General" else assigned_pet
                task = Task(
                    name=task_name,
                    duration_minutes=duration,
                    priority=priority,
                    task_type=TaskType[task_type.upper()],
                    description=description,
                    assigned_pet=assign_pet,
                    scheduled_time=scheduled_time
                )
                if task.validate():
                    st.session_state.scheduler.add_task(task)
                    st.success(f"Task '{task_name}' added!")
                    st.rerun()
                else:
                    st.error("Invalid task. Check that duration > 0 and priority is 1-5.")

    # ========================================================================
    # TAB 2: Daily Schedule
    # ========================================================================

    with tab2:
        st.subheader("Today's Schedule")

        col1, col2 = st.columns([2, 1])

        with col1:
            plan = st.session_state.scheduler.generate_daily_plan()
            explanation = st.session_state.scheduler.explain_reasoning(plan)
            st.info(explanation)

        with col2:
            st.metric("Available Time", f"{st.session_state.owner.daily_hours_available:.1f} hrs")
            st.metric("Tasks Scheduled", len(plan))
            if plan:
                total_mins = st.session_state.scheduler.calculate_total_duration(plan)
                st.metric("Time Needed", f"{total_mins // 60}h {total_mins % 60}m")

        conflicts = st.session_state.scheduler.detect_conflicts()
        if conflicts:
            st.warning(f"{len(conflicts)} scheduling conflict(s) detected!")
            for task1, task2, time in conflicts:
                st.write(f"- **{task1.name}** and **{task2.name}** both scheduled at {time}")

        if plan:
            st.subheader("Scheduled Tasks")
            schedule_data = []
            for task in plan:
                schedule_data.append({
                    "Time": task.scheduled_time or "Unscheduled",
                    "Task": task.name,
                    "Pet": task.assigned_pet or "General",
                    "Duration": f"{task.duration_minutes} min",
                    "Priority": f"{task.priority}/5"
                })
            st.table(schedule_data)

    # ========================================================================
    # TAB 3: Manage Tasks
    # ========================================================================

    with tab3:
        st.subheader("Manage Tasks")

        col1, col2, col3 = st.columns(3)

        with col1:
            sort_by = st.radio("Sort by", ["Time", "Priority"], key="sort_radio")

        with col2:
            show_completed = st.checkbox(
                "Show completed tasks", value=False, key="show_completed_check"
            )

        with col3:
            filter_pet = st.selectbox(
                "Filter by pet",
                ["All"] + [p.name for p in st.session_state.scheduler.pets],
                key="filter_pet_select"
            )

        if show_completed:
            tasks = st.session_state.scheduler.tasks
        else:
            tasks = st.session_state.scheduler.get_incomplete_tasks()

        if filter_pet != "All":
            tasks = [t for t in tasks if t.assigned_pet == filter_pet]

        if sort_by == "Time":
            tasks = st.session_state.scheduler.sort_by_time(tasks)
        else:
            tasks = st.session_state.scheduler.sort_by_priority(tasks)

        if tasks:
            for i, task in enumerate(tasks):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.write(task.get_details())

                with col2:
                    if not task.is_completed:
                        if st.button("Complete", key=f"complete_{i}"):
                            task.mark_complete()
                            new_task = st.session_state.scheduler.handle_recurring_task(task)
                            if new_task:
                                st.success("Recurring task created for tomorrow")
                            st.rerun()
                    else:
                        if st.button("Undo", key=f"undo_{i}"):
                            task.mark_incomplete()
                            st.rerun()

                with col3:
                    if st.button("Delete", key=f"delete_{i}"):
                        st.session_state.scheduler.tasks.remove(task)
                        st.rerun()
        else:
            st.info("No tasks to display.")

    # ========================================================================
    # TAB 4: Analytics
    # ========================================================================

    with tab4:
        st.subheader("Schedule Analytics")

        all_tasks = st.session_state.scheduler.tasks
        incomplete = st.session_state.scheduler.get_incomplete_tasks()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Tasks", len(all_tasks))
        with col2:
            st.metric("Incomplete", len(incomplete))
        with col3:
            completed = len([t for t in all_tasks if t.is_completed])
            st.metric("Completed", completed)
        with col4:
            if all_tasks:
                rate = (completed / len(all_tasks)) * 100
                st.metric("Completion Rate", f"{rate:.0f}%")

        st.divider()

        if st.session_state.scheduler.pets:
            st.subheader("Tasks by Pet")
            for pet in st.session_state.scheduler.pets:
                pet_tasks = st.session_state.scheduler.get_tasks_for_pet(pet.name)
                st.write(f"**{pet.name}**: {len(pet_tasks)} incomplete task(s)")

        if incomplete:
            st.subheader("Time Needed by Priority")
            priority_time = {}
            for task in incomplete:
                priority_time[task.priority] = priority_time.get(task.priority, 0) + task.duration_minutes
            for p in sorted(priority_time.keys(), reverse=True):
                mins = priority_time[p]
                st.write(f"Priority {p}: {mins} minutes ({mins / 60:.1f} hours)")

    # ========================================================================
    # TAB 5: AI Advisor
    # ========================================================================

    with tab5:
        st.subheader("AI-Powered Care Recommendations")
        st.markdown(
            "Select a pet to get personalized care advice generated by Claude and grounded "
            "in the PawPal knowledge base using Retrieval-Augmented Generation (RAG)."
        )

        if not st.session_state.scheduler.pets:
            st.warning("Add at least one pet using the sidebar before using the AI Advisor.")
        else:
            pet_names = [p.name for p in st.session_state.scheduler.pets]
            selected_pet_name = st.selectbox(
                "Select a pet to advise",
                pet_names,
                key="advisor_pet_select"
            )

            selected_pet = next(
                (p for p in st.session_state.scheduler.pets if p.name == selected_pet_name),
                None
            )

            if selected_pet:
                st.markdown(f"**Pet profile:** {selected_pet.get_info()}")

                pet_tasks = st.session_state.scheduler.get_tasks_for_pet(selected_pet.name)
                if pet_tasks:
                    st.markdown(f"**Scheduled tasks:** {len(pet_tasks)} task(s) for today")
                else:
                    st.info("No tasks scheduled for this pet yet. Add tasks in the Add Tasks tab.")

                if st.button("Get AI Recommendations", key="get_advice_btn"):
                    with st.spinner("Retrieving relevant knowledge base context and generating advice..."):
                        recommendation, confidence = get_pet_recommendations(
                            owner=st.session_state.owner,
                            pet=selected_pet,
                            tasks=pet_tasks
                        )

                    st.divider()

                    conf_color = "green" if confidence >= 0.7 else "orange" if confidence >= 0.4 else "red"
                    st.markdown(
                        f"**Confidence score:** :{conf_color}[{confidence:.0%}]"
                    )

                    st.subheader("Recommendations")
                    st.markdown(recommendation)

                    with st.expander("View retrieved knowledge base context (RAG sources)"):
                        from rag_engine import retrieve_context
                        task_types = [t.task_type.value for t in pet_tasks]
                        context = retrieve_context(
                            pet_species=selected_pet.pet_type.value,
                            pet_age=selected_pet.age,
                            special_needs=selected_pet.special_needs,
                            task_types=task_types,
                        )
                        if context:
                            st.text(context)
                        else:
                            st.info("No knowledge base context retrieved for this pet profile.")

                st.divider()
                st.caption(
                    "Recommendations are generated by Gemini (gemini-2.0-flash) using context "
                    "retrieved from the PawPal knowledge base. Always verify medical advice "
                    "with a licensed veterinarian."
                )

else:
    st.warning("Create an owner profile in the sidebar to get started.")
