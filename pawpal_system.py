"""
PawPal+ System Design
Core logic layer with Owner, Pet, Task, and Scheduler classes
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta


class TaskType(Enum):
    """Types of pet care tasks"""
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    TRAINING = "training"


class PetType(Enum):
    """Types of pets"""
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    OTHER = "other"


@dataclass
class Task:
    """Represents a pet care task"""
    name: str
    duration_minutes: int
    priority: int  # 1-5 scale, 5 being highest
    task_type: TaskType
    description: str = ""
    repeat_frequency: str = "daily"  # "daily", "weekly", "as-needed"
    assigned_pet: Optional[str] = None  # Pet name or None if for all pets
    scheduled_time: Optional[str] = None  # Time as "HH:MM" format
    is_completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def validate(self) -> bool:
        """Ensure task has valid attributes"""
        if self.duration_minutes <= 0:
            return False
        if self.priority < 1 or self.priority > 5:
            return False
        if self.repeat_frequency not in ["daily", "weekly", "as-needed"]:
            return False
        return True
    
    def get_details(self) -> str:
        """Return task details as a string"""
        time_str = f" @ {self.scheduled_time}" if self.scheduled_time else ""
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.name} ({self.duration_minutes}min, Priority {self.priority}){time_str}"
    
    def mark_complete(self) -> None:
        """Mark task as completed"""
        self.is_completed = True
    
    def mark_incomplete(self) -> None:
        """Mark task as incomplete"""
        self.is_completed = False


@dataclass
class Pet:
    """Represents a pet"""
    name: str
    pet_type: PetType
    age: int  # In years
    special_needs: List[str] = field(default_factory=list)  # e.g., ["diabetic", "senior"]
    tasks: List[Task] = field(default_factory=list)
    
    def get_info(self) -> str:
        """Return a description of the pet"""
        needs_str = f", Special needs: {', '.join(self.special_needs)}" if self.special_needs else ""
        return f"{self.name} ({self.pet_type.value}, {self.age} years old){needs_str}"
    
    def has_constraint(self, constraint: str) -> bool:
        """Check if pet has a specific constraint"""
        return constraint.lower() in [need.lower() for need in self.special_needs]
    
    def add_task(self, task: Task) -> None:
        """Add a task to the pet"""
        self.tasks.append(task)
    
    def get_tasks(self) -> List[Task]:
        """Get all tasks for this pet"""
        return self.tasks
    
    def get_task_count(self) -> int:
        """Get the number of tasks for this pet"""
        return len(self.tasks)


@dataclass
class Owner:
    """Represents a pet owner"""
    name: str
    daily_hours_available: float  # Hours available per day (e.g., 4.5)
    preferences: dict = field(default_factory=dict)  # Custom preferences
    pets: List[Pet] = field(default_factory=list)
    
    def set_availability(self, hours: float) -> None:
        """Set the owner's available hours per day"""
        if hours > 0:
            self.daily_hours_available = hours
    
    def get_preferences(self) -> dict:
        """Retrieve owner preferences"""
        return self.preferences
    
    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's collection"""
        self.pets.append(pet)
    
    def get_pets(self) -> List[Pet]:
        """Get all pets for this owner"""
        return self.pets
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks across all pets"""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks


@dataclass
class Scheduler:
    """Main scheduler that creates daily plans"""
    owner: Owner
    pets: List[Pet] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize scheduler with owner's pets and their tasks"""
        self.pets = self.owner.get_pets()
        self.tasks = self.owner.get_all_tasks()
    
    def add_pet(self, pet: Pet) -> None:
        """Add a pet to be scheduled for"""
        if pet not in self.pets:
            self.pets.append(pet)
        self.owner.add_pet(pet)
    
    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler"""
        if task.validate() and task not in self.tasks:
            self.tasks.append(task)
            # Also add to the appropriate pet if assigned
            if task.assigned_pet:
                for pet in self.pets:
                    if pet.name == task.assigned_pet:
                        pet.add_task(task)
    
    def get_incomplete_tasks(self) -> List[Task]:
        """Get all incomplete tasks"""
        return [task for task in self.tasks if not task.is_completed]
    
    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """Get all tasks for a specific pet"""
        return [task for task in self.tasks 
                if task.assigned_pet == pet_name and not task.is_completed]
    
    def sort_by_priority(self, task_list: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks by priority (highest first)"""
        tasks = task_list or self.get_incomplete_tasks()
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
    
    def sort_by_time(self, task_list: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks by scheduled time (earliest first)"""
        tasks = task_list or self.get_incomplete_tasks()
        return sorted(tasks, key=lambda t: t.scheduled_time or "23:59")
    
    def generate_daily_plan(self) -> List[Task]:
        """Create an optimized schedule for today"""
        # Get incomplete tasks
        incomplete = self.get_incomplete_tasks()
        
        if not incomplete:
            return []
        
        # Sort by priority first
        sorted_tasks = self.sort_by_priority(incomplete)
        
        # Calculate total time needed
        total_minutes = sum(task.duration_minutes for task in sorted_tasks)
        available_minutes = int(self.owner.daily_hours_available * 60)
        
        # If everything fits, return all tasks sorted by priority
        if total_minutes <= available_minutes:
            return sorted_tasks
        
        # Otherwise, fit in as many high-priority tasks as possible
        plan = []
        time_used = 0
        for task in sorted_tasks:
            if time_used + task.duration_minutes <= available_minutes:
                plan.append(task)
                time_used += task.duration_minutes
        
        return plan
    
    def explain_reasoning(self, plan: List[Task]) -> str:
        """Explain why tasks were scheduled in this order"""
        if not plan:
            return "No tasks to schedule today."
        
        explanation = f"Daily Schedule for {self.owner.name} ({len(plan)} tasks):\n"
        explanation += f"Available time: {self.owner.daily_hours_available} hours\n"
        explanation += "—" * 40 + "\n"
        
        total_time = 0
        for i, task in enumerate(plan, 1):
            pet_str = f" ({task.assigned_pet})" if task.assigned_pet else ""
            explanation += f"{i}. {task.name}{pet_str}\n"
            explanation += f"   Duration: {task.duration_minutes} min | Priority: {task.priority}/5\n"
            total_time += task.duration_minutes
        
        explanation += "—" * 40 + "\n"
        explanation += f"Total time needed: {total_time} minutes ({total_time/60:.1f} hours)\n"
        
        available_minutes = int(self.owner.daily_hours_available * 60)
        if total_time <= available_minutes:
            explanation += f"Status: ✓ All tasks fit within available time!"
        else:
            explanation += f"⚠ Warning: Tasks exceed available time by {total_time - available_minutes} minutes"
        
        return explanation
    
    def calculate_total_duration(self, plan: List[Task]) -> int:
        """Calculate total time needed for a plan (in minutes)"""
        return sum(task.duration_minutes for task in plan)
    
    def detect_conflicts(self) -> List[Tuple[Task, Task, str]]:
        """Detect tasks scheduled at the same time"""
        conflicts = []
        tasks_with_time = [t for t in self.tasks if t.scheduled_time and not t.is_completed]
        
        for i, task1 in enumerate(tasks_with_time):
            for task2 in tasks_with_time[i+1:]:
                if task1.scheduled_time == task2.scheduled_time:
                    conflicts.append((task1, task2, task1.scheduled_time))
        
        return conflicts
    
    def check_pet_conflicts(self, pet_name: str) -> List[Tuple[Task, Task, str]]:
        """Detect conflicts for a specific pet"""
        pet_tasks = self.get_tasks_for_pet(pet_name)
        tasks_with_time = [t for t in pet_tasks if t.scheduled_time]
        
        conflicts = []
        for i, task1 in enumerate(tasks_with_time):
            for task2 in tasks_with_time[i+1:]:
                if task1.scheduled_time == task2.scheduled_time:
                    conflicts.append((task1, task2, task1.scheduled_time))
        
        return conflicts
    
    def handle_recurring_task(self, completed_task: Task) -> Optional[Task]:
        """Create a new task for tomorrow if this is a recurring task"""
        if completed_task.repeat_frequency == "daily":
            new_task = Task(
                name=completed_task.name,
                duration_minutes=completed_task.duration_minutes,
                priority=completed_task.priority,
                task_type=completed_task.task_type,
                description=completed_task.description,
                repeat_frequency=completed_task.repeat_frequency,
                assigned_pet=completed_task.assigned_pet,
                scheduled_time=completed_task.scheduled_time
            )
            self.add_task(new_task)
            return new_task
        
        return None
