"""
Evaluation harness for PawPal+ AI recommendations.

Runs predefined test scenarios through the full pipeline (RAG retrieval,
input validation guardrails, scheduling, and optionally the Gemini API)
and prints a structured pass/fail summary with confidence scores.

Usage:
    python eval_harness.py           # full run including Gemini API calls
    python eval_harness.py --no-api  # skip API calls, test RAG + guardrails only
"""

import sys
from typing import List, Tuple

from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, PetType
from ai_advisor import get_pet_recommendations, validate_pet_input
from rag_engine import retrieve_context

TestResult = Tuple[str, bool, str]


# ============================================================================
# Scenario builders
# ============================================================================

def scenario_senior_dog() -> Tuple[Owner, Pet, List[Task], str]:
    """Senior dog with arthritis and a medication task."""
    owner = Owner(name="Alex", daily_hours_available=3.0)
    pet = Pet(name="Biscuit", pet_type=PetType.DOG, age=9,
              special_needs=["senior", "arthritis"])
    tasks = [
        Task("Morning medication", 5, 5, TaskType.MEDICATION,
             assigned_pet="Biscuit", scheduled_time="08:00"),
        Task("Short walk", 20, 4, TaskType.WALK,
             assigned_pet="Biscuit", scheduled_time="09:00"),
    ]
    owner.add_pet(pet)
    return owner, pet, tasks, "Senior dog with arthritis and medication"


def scenario_diabetic_cat() -> Tuple[Owner, Pet, List[Task], str]:
    """Diabetic cat requiring insulin paired with feeding."""
    owner = Owner(name="Sam", daily_hours_available=2.0)
    pet = Pet(name="Luna", pet_type=PetType.CAT, age=6,
              special_needs=["diabetic"])
    tasks = [
        Task("Insulin injection", 5, 5, TaskType.MEDICATION,
             assigned_pet="Luna", scheduled_time="08:00"),
        Task("Morning feeding", 10, 5, TaskType.FEEDING,
             assigned_pet="Luna", scheduled_time="08:05"),
    ]
    owner.add_pet(pet)
    return owner, pet, tasks, "Diabetic cat needing insulin"


def scenario_rabbit() -> Tuple[Owner, Pet, List[Task], str]:
    """Young rabbit with enrichment and feeding tasks."""
    owner = Owner(name="Chris", daily_hours_available=4.0)
    pet = Pet(name="Pebbles", pet_type=PetType.RABBIT, age=2,
              special_needs=[])
    tasks = [
        Task("Free roam time", 60, 4, TaskType.ENRICHMENT,
             assigned_pet="Pebbles", scheduled_time="10:00"),
        Task("Hay refill", 5, 5, TaskType.FEEDING,
             assigned_pet="Pebbles", scheduled_time="08:00"),
    ]
    owner.add_pet(pet)
    return owner, pet, tasks, "Young rabbit with enrichment and feeding"


def scenario_invalid_age() -> Tuple[Owner, Pet, List[Task], str]:
    """Pet with an impossible age - guardrail should reject this input."""
    owner = Owner(name="Test", daily_hours_available=2.0)
    pet = Pet(name="Ghost", pet_type=PetType.DOG, age=99, special_needs=[])
    owner.add_pet(pet)
    return owner, pet, [], "Invalid pet age guardrail test"


def scenario_bird() -> Tuple[Owner, Pet, List[Task], str]:
    """Bird with out-of-cage enrichment and daily water change."""
    owner = Owner(name="Morgan", daily_hours_available=2.0)
    pet = Pet(name="Kiwi", pet_type=PetType.BIRD, age=3, special_needs=[])
    tasks = [
        Task("Out-of-cage time", 90, 4, TaskType.ENRICHMENT,
             assigned_pet="Kiwi", scheduled_time="10:00"),
        Task("Fresh water change", 5, 5, TaskType.FEEDING,
             assigned_pet="Kiwi", scheduled_time="08:00"),
    ]
    owner.add_pet(pet)
    return owner, pet, tasks, "Bird with enrichment and daily care"


def scenario_overloaded_schedule() -> Tuple[Owner, Pet, List[Task], str]:
    """Owner with 1 hour but tasks totaling 3 hours - scheduler must trim."""
    owner = Owner(name="Jordan", daily_hours_available=1.0)
    pet = Pet(name="Max", pet_type=PetType.DOG, age=4, special_needs=[])
    tasks = [
        Task("Long walk", 90, 3, TaskType.WALK, assigned_pet="Max"),
        Task("Training", 60, 2, TaskType.TRAINING, assigned_pet="Max"),
        Task("Feeding", 10, 5, TaskType.FEEDING, assigned_pet="Max"),
    ]
    owner.add_pet(pet)
    return owner, pet, tasks, "Overloaded schedule trimming test"


# ============================================================================
# Individual check functions
# ============================================================================

def check_rag_retrieves_relevant_context(pet: Pet, tasks: List[Task]) -> TestResult:
    """RAG must return non-empty context that mentions the species or a special need."""
    task_types = [t.task_type.value for t in tasks]
    context = retrieve_context(
        pet_species=pet.pet_type.value,
        pet_age=pet.age,
        special_needs=pet.special_needs,
        task_types=task_types,
    )
    if not context:
        return "RAG retrieval", False, "Returned empty context"
    species = pet.pet_type.value.lower()
    needs = [n.lower().replace("_", " ") for n in pet.special_needs]
    ctx_lower = context.lower()
    if species not in ctx_lower and not any(n in ctx_lower for n in needs):
        return "RAG retrieval", False, f"Context does not mention '{species}' or special needs"
    return "RAG retrieval", True, f"Retrieved {len(context)} chars of relevant context"


def check_guardrail_blocks_invalid(pet: Pet) -> TestResult:
    """Input validation must reject a pet with an out-of-range age."""
    is_valid, msg = validate_pet_input(pet)
    if is_valid:
        return "Input guardrail", False, "Guardrail accepted an invalid pet (should have rejected)"
    return "Input guardrail", True, f"Correctly blocked: {msg}"


def check_schedule_fits_time(owner: Owner, pet: Pet, tasks: List[Task]) -> TestResult:
    """Scheduler must produce a plan that fits within available time."""
    scheduler = Scheduler(owner=owner)
    scheduler.add_pet(pet)
    for task in tasks:
        scheduler.add_task(task)
    plan = scheduler.generate_daily_plan()
    total = scheduler.calculate_total_duration(plan)
    available = int(owner.daily_hours_available * 60)
    if total > available:
        return "Schedule time fit", False, f"{total} min scheduled but only {available} min available"
    return "Schedule time fit", True, f"{len(plan)} tasks, {total}/{available} min used"


def check_recommendation_quality(recommendation: str, confidence: float) -> TestResult:
    """Recommendation must be non-trivial and confidence must be in [0, 1]."""
    if len(recommendation.strip()) < 30:
        return "Recommendation quality", False, "Response is too short to be useful"
    if not (0.0 <= confidence <= 1.0):
        return "Recommendation quality", False, f"Confidence {confidence} is outside [0, 1]"
    return "Recommendation quality", True, (
        f"Response length={len(recommendation)} chars, confidence={confidence:.2f}"
    )


def check_schedule_trimmed_when_overloaded(
    owner: Owner, pet: Pet, tasks: List[Task]
) -> TestResult:
    """When tasks exceed available time, scheduler must drop lower-priority tasks."""
    scheduler = Scheduler(owner=owner)
    scheduler.add_pet(pet)
    for task in tasks:
        scheduler.add_task(task)
    plan = scheduler.generate_daily_plan()
    available = int(owner.daily_hours_available * 60)
    total_all = sum(t.duration_minutes for t in tasks)
    total_plan = scheduler.calculate_total_duration(plan)
    if total_all <= available:
        return "Schedule trimming", False, "Tasks already fit; trimming was not exercised"
    if total_plan > available:
        return "Schedule trimming", False, f"Plan still exceeds time: {total_plan} > {available} min"
    if len(plan) >= len(tasks):
        return "Schedule trimming", False, "No tasks were dropped despite overflow"
    return "Schedule trimming", True, (
        f"Dropped {len(tasks) - len(plan)} low-priority task(s); plan={total_plan}/{available} min"
    )


# ============================================================================
# Harness runner
# ============================================================================

def run_harness(use_api: bool = True) -> None:
    """Execute all scenarios and print a pass/fail summary."""
    sep = "=" * 62
    print(sep)
    print("  PawPal+ Evaluation Harness")
    print(sep)

    all_results: List[TestResult] = []

    def add(label: str, results: List[TestResult]) -> None:
        print(f"\n[{label}]")
        for name, ok, msg in results:
            marker = "PASS" if ok else "FAIL"
            print(f"  [{marker}] {name}: {msg}")
        all_results.extend(results)

    # Scenario 1: senior dog
    o1, p1, t1, lbl1 = scenario_senior_dog()
    s1_results: List[TestResult] = [
        check_rag_retrieves_relevant_context(p1, t1),
        check_schedule_fits_time(o1, p1, t1),
    ]
    if use_api:
        rec1, conf1 = get_pet_recommendations(o1, p1, t1)
        s1_results.append(check_recommendation_quality(rec1, conf1))
    add(lbl1, s1_results)

    # Scenario 2: diabetic cat
    o2, p2, t2, lbl2 = scenario_diabetic_cat()
    s2_results: List[TestResult] = [
        check_rag_retrieves_relevant_context(p2, t2),
        check_schedule_fits_time(o2, p2, t2),
    ]
    if use_api:
        rec2, conf2 = get_pet_recommendations(o2, p2, t2)
        s2_results.append(check_recommendation_quality(rec2, conf2))
    add(lbl2, s2_results)

    # Scenario 3: rabbit
    o3, p3, t3, lbl3 = scenario_rabbit()
    s3_results: List[TestResult] = [
        check_rag_retrieves_relevant_context(p3, t3),
        check_schedule_fits_time(o3, p3, t3),
    ]
    if use_api:
        rec3, conf3 = get_pet_recommendations(o3, p3, t3)
        s3_results.append(check_recommendation_quality(rec3, conf3))
    add(lbl3, s3_results)

    # Scenario 4: guardrail
    o4, p4, t4, lbl4 = scenario_invalid_age()
    add(lbl4, [check_guardrail_blocks_invalid(p4)])

    # Scenario 5: bird
    o5, p5, t5, lbl5 = scenario_bird()
    s5_results: List[TestResult] = [
        check_rag_retrieves_relevant_context(p5, t5),
        check_schedule_fits_time(o5, p5, t5),
    ]
    if use_api:
        rec5, conf5 = get_pet_recommendations(o5, p5, t5)
        s5_results.append(check_recommendation_quality(rec5, conf5))
    add(lbl5, s5_results)

    # Scenario 6: overloaded schedule
    o6, p6, t6, lbl6 = scenario_overloaded_schedule()
    add(lbl6, [check_schedule_trimmed_when_overloaded(o6, p6, t6)])

    # Summary
    print("\n" + sep)
    print("  RESULTS SUMMARY")
    print(sep)
    passed = sum(1 for _, ok, _ in all_results if ok)
    total = len(all_results)
    for name, ok, msg in all_results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {msg}")

    pct = passed / total * 100 if total else 0
    print(f"\n  Score: {passed}/{total} tests passed ({pct:.0f}%)")

    if pct >= 80:
        verdict = "RELIABLE"
    elif pct >= 60:
        verdict = "NEEDS IMPROVEMENT"
    else:
        verdict = "UNRELIABLE"
    print(f"  System verdict: {verdict}")
    print(sep)


if __name__ == "__main__":
    use_api = "--no-api" not in sys.argv
    if not use_api:
        print("Running in --no-api mode: Gemini API calls are skipped.\n")
    run_harness(use_api=use_api)