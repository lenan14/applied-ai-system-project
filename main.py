"""
PawPal+ Demo Script
Demonstrates the core functionality of the PawPal+ scheduling system
"""

from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    TaskType, PetType
)


def print_separator(title: str = ""):
    """Print a formatted separator line"""
    if title:
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"{'='*50}\n")
    else:
        print(f"\n{'-'*50}\n")


def main():
    """Run the PawPal+ demo"""
    
    print_separator("🐾 PawPal+ Demo")
    
    # Step 1: Create an Owner
    print("1️⃣  Creating Owner...")
    owner = Owner(
        name="Jordan",
        daily_hours_available=4.0,
        preferences={"morning_person": True, "prefer_walks_early": True}
    )
    print(f"   Owner: {owner.name}, Available: {owner.daily_hours_available} hours/day")
    
    # Step 2: Create Pets
    print_separator("Creating Pets")
    
    mochi = Pet(
        name="Mochi",
        pet_type=PetType.DOG,
        age=3,
        special_needs=["needs_exercise"]
    )
    print(f"   Created: {mochi.get_info()}")
    
    whiskers = Pet(
        name="Whiskers",
        pet_type=PetType.CAT,
        age=5,
        special_needs=["senior", "takes_medication"]
    )
    print(f"   Created: {whiskers.get_info()}")
    
    owner.add_pet(mochi)
    owner.add_pet(whiskers)
    
    # Step 3: Create Tasks
    print_separator("Creating Tasks")
    
    tasks = [
        Task(
            name="Morning Walk",
            duration_minutes=30,
            priority=5,
            task_type=TaskType.WALK,
            description="Energetic walk in the park",
            assigned_pet="Mochi",
            scheduled_time="07:00"
        ),
        Task(
            name="Feed Mochi",
            duration_minutes=10,
            priority=5,
            task_type=TaskType.FEEDING,
            description="Breakfast",
            assigned_pet="Mochi",
            scheduled_time="07:30"
        ),
        Task(
            name="Give Whiskers Medication",
            duration_minutes=5,
            priority=5,
            task_type=TaskType.MEDICATION,
            description="Morning dose",
            assigned_pet="Whiskers",
            scheduled_time="08:00"
        ),
        Task(
            name="Feed Whiskers",
            duration_minutes=5,
            priority=4,
            task_type=TaskType.FEEDING,
            description="Wet food",
            assigned_pet="Whiskers",
            scheduled_time="08:05"
        ),
        Task(
            name="Play/Enrichment with Mochi",
            duration_minutes=15,
            priority=4,
            task_type=TaskType.ENRICHMENT,
            description="Fetch or puzzle toy",
            assigned_pet="Mochi",
            scheduled_time="09:00"
        ),
        Task(
            name="Groom Mochi",
            duration_minutes=20,
            priority=3,
            task_type=TaskType.GROOMING,
            description="Brush and check paws",
            assigned_pet="Mochi",
            scheduled_time="10:00"
        ),
    ]
    
    for task in tasks:
        if task.validate():
            print(f"   ✓ {task.name} ({task.duration_minutes}min, Priority {task.priority})")
        else:
            print(f"   ✗ {task.name} - INVALID")
    
    # Step 4: Create Scheduler and add everything
    print_separator("Initializing Scheduler")
    
    scheduler = Scheduler(owner=owner)
    print(f"   Scheduler initialized for {owner.name}")
    print(f"   Pets: {len(scheduler.pets)}")
    
    for task in tasks:
        if task.validate():
            scheduler.add_task(task)
    
    print(f"   Tasks loaded: {len(scheduler.tasks)}")
    
    # Step 5: Display today's schedule with explanation
    print_separator("📅 Daily Plan")
    
    plan = scheduler.generate_daily_plan()
    explanation = scheduler.explain_reasoning(plan)
    print(explanation)
    
    # Step 6: Display tasks by priority
    print_separator("Tasks by Priority")
    priority_sorted = scheduler.sort_by_priority()
    for task in priority_sorted:
        print(f"   {task.get_details()}")
    
    # Step 7: Display tasks by time
    print_separator("Tasks by Time")
    time_sorted = scheduler.sort_by_time()
    for task in time_sorted:
        print(f"   {task.get_details()}")
    
    # Step 8: Detect conflicts
    print_separator("Conflict Detection")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print(f"   ⚠ Found {len(conflicts)} conflict(s):")
        for task1, task2, time in conflicts:
            print(f"      - {task1.name} vs {task2.name} @ {time}")
    else:
        print("   ✓ No conflicts detected!")
    
    # Step 9: Check pet-specific tasks
    print_separator("Pet-Specific Tasks")
    
    for pet in scheduler.pets:
        pet_tasks = scheduler.get_tasks_for_pet(pet.name)
        print(f"\n   {pet.name}: {len(pet_tasks)} tasks")
        for task in pet_tasks:
            print(f"      - {task.get_details()}")
    
    # Step 10: Mark a task complete and demonstrate recurrence
    print_separator("Task Completion & Recurrence")
    
    if plan:
        completed_task = plan[0]
        print(f"   Marking '{completed_task.name}' as complete...")
        completed_task.mark_complete()
        print(f"   Status: {completed_task.get_details()}")
        
        if completed_task.repeat_frequency == "daily":
            new_task = scheduler.handle_recurring_task(completed_task)
            if new_task:
                print(f"   ✓ Created recurring task for tomorrow")
                print(f"   New task: {new_task.get_details()}")
    
    print_separator("✅ Demo Complete")
    print(f"Total tasks in system: {len(scheduler.tasks)}")
    print(f"Incomplete tasks: {len(scheduler.get_incomplete_tasks())}")


if __name__ == "__main__":
    main()
