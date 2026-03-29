"""
PawPal+ Test Suite
Tests for Task, Pet, Owner, and Scheduler classes
"""

import pytest
from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    TaskType, PetType
)


# ============================================================================
# Task Tests
# ============================================================================

class TestTask:
    """Test suite for Task class"""
    
    def test_task_creation(self):
        """Test that a task can be created with valid attributes"""
        task = Task(
            name="Walk",
            duration_minutes=30,
            priority=5,
            task_type=TaskType.WALK
        )
        assert task.name == "Walk"
        assert task.duration_minutes == 30
        assert task.priority == 5
        assert task.is_completed is False
    
    def test_task_validation_success(self):
        """Test that a valid task passes validation"""
        task = Task(
            name="Feed",
            duration_minutes=10,
            priority=3,
            task_type=TaskType.FEEDING
        )
        assert task.validate() is True
    
    def test_task_validation_fails_invalid_duration(self):
        """Test that a task with zero duration fails validation"""
        task = Task(
            name="Feed",
            duration_minutes=0,
            priority=3,
            task_type=TaskType.FEEDING
        )
        assert task.validate() is False
    
    def test_task_validation_fails_invalid_priority(self):
        """Test that a task with invalid priority fails validation"""
        task = Task(
            name="Feed",
            duration_minutes=10,
            priority=6,  # Out of range
            task_type=TaskType.FEEDING
        )
        assert task.validate() is False
    
    def test_task_mark_complete(self):
        """Test marking a task as complete"""
        task = Task(
            name="Walk",
            duration_minutes=30,
            priority=5,
            task_type=TaskType.WALK
        )
        assert task.is_completed is False
        task.mark_complete()
        assert task.is_completed is True
    
    def test_task_mark_incomplete(self):
        """Test marking a completed task as incomplete"""
        task = Task(
            name="Walk",
            duration_minutes=30,
            priority=5,
            task_type=TaskType.WALK,
            is_completed=True
        )
        task.mark_incomplete()
        assert task.is_completed is False
    
    def test_task_get_details(self):
        """Test that task details are formatted correctly"""
        task = Task(
            name="Morning Walk",
            duration_minutes=30,
            priority=5,
            task_type=TaskType.WALK,
            scheduled_time="07:00"
        )
        details = task.get_details()
        assert "Morning Walk" in details
        assert "30" in details
        assert "07:00" in details


# ============================================================================
# Pet Tests
# ============================================================================

class TestPet:
    """Test suite for Pet class"""
    
    def test_pet_creation(self):
        """Test that a pet can be created"""
        pet = Pet(
            name="Mochi",
            pet_type=PetType.DOG,
            age=3
        )
        assert pet.name == "Mochi"
        assert pet.pet_type == PetType.DOG
        assert pet.age == 3
    
    def test_pet_with_special_needs(self):
        """Test creating a pet with special needs"""
        pet = Pet(
            name="Whiskers",
            pet_type=PetType.CAT,
            age=5,
            special_needs=["senior", "takes_medication"]
        )
        assert len(pet.special_needs) == 2
        assert pet.has_constraint("senior") is True
    
    def test_pet_has_constraint(self):
        """Test checking pet constraints"""
        pet = Pet(
            name="Mochi",
            pet_type=PetType.DOG,
            age=3,
            special_needs=["needs_exercise"]
        )
        assert pet.has_constraint("needs_exercise") is True
        assert pet.has_constraint("diabetic") is False
    
    def test_pet_get_info(self):
        """Test getting pet information string"""
        pet = Pet(
            name="Mochi",
            pet_type=PetType.DOG,
            age=3,
            special_needs=["senior"]
        )
        info = pet.get_info()
        assert "Mochi" in info
        assert "dog" in info
        assert "3 years" in info
        assert "senior" in info
    
    def test_pet_add_task(self):
        """Test adding a task to a pet"""
        pet = Pet(
            name="Mochi",
            pet_type=PetType.DOG,
            age=3
        )
        task = Task(
            name="Walk",
            duration_minutes=30,
            priority=5,
            task_type=TaskType.WALK,
            assigned_pet="Mochi"
        )
        pet.add_task(task)
        assert pet.get_task_count() == 1
        assert task in pet.get_tasks()
    
    def test_pet_get_task_count(self):
        """Test counting tasks for a pet"""
        pet = Pet(
            name="Mochi",
            pet_type=PetType.DOG,
            age=3
        )
        assert pet.get_task_count() == 0
        
        task1 = Task("Walk", 30, 5, TaskType.WALK, assigned_pet="Mochi")
        task2 = Task("Feed", 10, 5, TaskType.FEEDING, assigned_pet="Mochi")
        
        pet.add_task(task1)
        pet.add_task(task2)
        
        assert pet.get_task_count() == 2


# ============================================================================
# Owner Tests
# ============================================================================

class TestOwner:
    """Test suite for Owner class"""
    
    def test_owner_creation(self):
        """Test that an owner can be created"""
        owner = Owner(
            name="Jordan",
            daily_hours_available=4.0
        )
        assert owner.name == "Jordan"
        assert owner.daily_hours_available == 4.0
    
    def test_owner_set_availability(self):
        """Test setting owner availability"""
        owner = Owner(
            name="Jordan",
            daily_hours_available=4.0
        )
        owner.set_availability(5.5)
        assert owner.daily_hours_available == 5.5
    
    def test_owner_add_pet(self):
        """Test adding a pet to owner"""
        owner = Owner(name="Jordan", daily_hours_available=4.0)
        pet = Pet(name="Mochi", pet_type=PetType.DOG, age=3)
        
        owner.add_pet(pet)
        assert len(owner.get_pets()) == 1
        assert pet in owner.get_pets()
    
    def test_owner_get_all_tasks(self):
        """Test getting all tasks across owner's pets"""
        owner = Owner(name="Jordan", daily_hours_available=4.0)
        
        pet1 = Pet(name="Mochi", pet_type=PetType.DOG, age=3)
        pet2 = Pet(name="Whiskers", pet_type=PetType.CAT, age=5)
        
        task1 = Task("Walk", 30, 5, TaskType.WALK, assigned_pet="Mochi")
        task2 = Task("Feed", 10, 5, TaskType.FEEDING, assigned_pet="Whiskers")
        
        pet1.add_task(task1)
        pet2.add_task(task2)
        
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        
        all_tasks = owner.get_all_tasks()
        assert len(all_tasks) == 2
        assert task1 in all_tasks
        assert task2 in all_tasks


# ============================================================================
# Scheduler Tests
# ============================================================================

class TestScheduler:
    """Test suite for Scheduler class"""
    
    @pytest.fixture
    def scheduler(self):
        """Create a scheduler with sample data"""
        owner = Owner(name="Jordan", daily_hours_available=4.0)
        
        mochi = Pet(name="Mochi", pet_type=PetType.DOG, age=3)
        whiskers = Pet(name="Whiskers", pet_type=PetType.CAT, age=5)
        
        owner.add_pet(mochi)
        owner.add_pet(whiskers)
        
        scheduler = Scheduler(owner=owner)
        
        # Add tasks
        task1 = Task("Walk", 30, 5, TaskType.WALK, 
                    assigned_pet="Mochi", scheduled_time="07:00")
        task2 = Task("Feed", 10, 5, TaskType.FEEDING, 
                    assigned_pet="Mochi", scheduled_time="07:30")
        task3 = Task("Medication", 5, 5, TaskType.MEDICATION, 
                    assigned_pet="Whiskers", scheduled_time="08:00")
        
        scheduler.add_task(task1)
        scheduler.add_task(task2)
        scheduler.add_task(task3)
        
        return scheduler
    
    def test_scheduler_creation(self, scheduler):
        """Test that a scheduler is created with owner"""
        assert scheduler.owner.name == "Jordan"
        assert len(scheduler.pets) == 2
    
    def test_scheduler_add_task(self, scheduler):
        """Test adding a task to scheduler"""
        initial_count = len(scheduler.tasks)
        
        task = Task("Groom", 20, 3, TaskType.GROOMING, 
                   assigned_pet="Mochi", scheduled_time="10:00")
        scheduler.add_task(task)
        
        assert len(scheduler.tasks) == initial_count + 1
    
    def test_scheduler_get_incomplete_tasks(self, scheduler):
        """Test getting only incomplete tasks"""
        incomplete = scheduler.get_incomplete_tasks()
        assert len(incomplete) == 3
        
        # Mark one as complete
        incomplete[0].mark_complete()
        
        incomplete_after = scheduler.get_incomplete_tasks()
        assert len(incomplete_after) == 2
    
    def test_scheduler_get_tasks_for_pet(self, scheduler):
        """Test filtering tasks by pet"""
        mochi_tasks = scheduler.get_tasks_for_pet("Mochi")
        whiskers_tasks = scheduler.get_tasks_for_pet("Whiskers")
        
        assert len(mochi_tasks) == 2
        assert len(whiskers_tasks) == 1
    
    def test_scheduler_sort_by_priority(self, scheduler):
        """Test sorting tasks by priority"""
        sorted_tasks = scheduler.sort_by_priority()
        
        # All first two tasks have priority 5, third has priority 5
        assert sorted_tasks[0].priority == 5
        assert sorted_tasks[1].priority == 5
    
    def test_scheduler_sort_by_time(self, scheduler):
        """Test sorting tasks by scheduled time"""
        sorted_tasks = scheduler.sort_by_time()
        
        times = [t.scheduled_time for t in sorted_tasks]
        assert times == ["07:00", "07:30", "08:00"]
    
    def test_scheduler_generate_daily_plan(self, scheduler):
        """Test generating a daily plan"""
        plan = scheduler.generate_daily_plan()
        
        assert len(plan) > 0
        # All tasks should fit (85 minutes < 4 hours)
        total_time = scheduler.calculate_total_duration(plan)
        available_minutes = int(scheduler.owner.daily_hours_available * 60)
        assert total_time <= available_minutes
    
    def test_scheduler_calculate_total_duration(self, scheduler):
        """Test calculating plan duration"""
        plan = scheduler.generate_daily_plan()
        total = scheduler.calculate_total_duration(plan)
        
        # Should be 30 + 10 + 5 = 45 minutes
        assert total == 45
    
    def test_scheduler_detect_conflicts(self):
        """Test detecting time conflicts"""
        owner = Owner(name="Jordan", daily_hours_available=4.0)
        pet = Pet(name="Mochi", pet_type=PetType.DOG, age=3)
        owner.add_pet(pet)
        
        scheduler = Scheduler(owner=owner)
        
        # Add conflicting tasks
        task1 = Task("Walk", 30, 5, TaskType.WALK, 
                    assigned_pet="Mochi", scheduled_time="07:00")
        task2 = Task("Training", 20, 4, TaskType.TRAINING, 
                    assigned_pet="Mochi", scheduled_time="07:00")
        
        scheduler.add_task(task1)
        scheduler.add_task(task2)
        
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0][2] == "07:00"  # Time of conflict
    
    def test_scheduler_handle_recurring_task(self, scheduler):
        """Test creating new task from recurring task"""
        task = scheduler.tasks[0]  # Get first task
        task.repeat_frequency = "daily"
        
        initial_task_count = len(scheduler.tasks)
        
        task.mark_complete()
        new_task = scheduler.handle_recurring_task(task)
        
        assert new_task is not None
        assert new_task.name == task.name
        assert len(scheduler.tasks) == initial_task_count + 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the full system"""
    
    def test_full_workflow(self):
        """Test a complete workflow from owner to scheduled plan"""
        # Create owner and pets
        owner = Owner(name="Jordan", daily_hours_available=3.0)
        
        mochi = Pet(name="Mochi", pet_type=PetType.DOG, age=3,
                   special_needs=["needs_exercise"])
        whiskers = Pet(name="Whiskers", pet_type=PetType.CAT, age=5,
                      special_needs=["senior"])
        
        owner.add_pet(mochi)
        owner.add_pet(whiskers)
        
        # Create scheduler
        scheduler = Scheduler(owner=owner)
        
        # Add tasks
        tasks = [
            Task("Walk", 30, 5, TaskType.WALK, assigned_pet="Mochi", 
                scheduled_time="07:00"),
            Task("Feed Mochi", 10, 5, TaskType.FEEDING, assigned_pet="Mochi",
                scheduled_time="07:30"),
            Task("Medication", 5, 5, TaskType.MEDICATION, assigned_pet="Whiskers",
                scheduled_time="08:00"),
            Task("Feed Whiskers", 5, 4, TaskType.FEEDING, assigned_pet="Whiskers",
                scheduled_time="08:05"),
        ]
        
        for task in tasks:
            scheduler.add_task(task)
        
        # Generate plan
        plan = scheduler.generate_daily_plan()
        
        # Verify plan
        assert len(plan) == 4
        assert scheduler.calculate_total_duration(plan) == 50  # 30+10+5+5
        
        # Verify no conflicts
        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 0
