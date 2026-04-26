"""
AI Advisor module for PawPal+.
Combines RAG retrieval with the Gemini API to generate pet-specific
care recommendations grounded in the knowledge base.
"""

import logging
import os
import re
from typing import List, Optional, Tuple

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

from pawpal_system import Owner, Pet, Task
from rag_engine import retrieve_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are PawPal AI, a knowledgeable and caring pet care assistant. "
    "Your role is to provide specific, evidence-based care recommendations for pet owners. "
    "You use retrieved knowledge base context to ground your advice in reliable guidelines.\n\n"
    "When giving recommendations:\n"
    "- Be specific to the pet's species, age, and special needs\n"
    "- Explain WHY each high-priority task matters medically or behaviorally\n"
    "- Flag any health concerns that need veterinary attention\n"
    "- Keep responses concise and actionable (2 to 4 sentences per point)\n"
    "- End your response with exactly this line: CONFIDENCE: <score> "
    "where <score> is a decimal between 0.0 and 1.0 reflecting how confident "
    "you are that the advice is accurate and complete for this pet profile."
)

MAX_PROMPT_LENGTH = 2500
ALLOWED_SPECIES = {"dog", "cat", "bird", "rabbit", "other"}
MAX_PET_AGE = 50
GEMINI_MODEL = "gemini-2.0-flash"


def validate_pet_input(pet: Pet) -> Tuple[bool, str]:
    """Check that pet data is safe to send to the AI.

    Returns (is_valid, error_message). An empty error_message means valid.
    """
    if not pet.name or not pet.name.strip():
        return False, "Pet name cannot be empty."
    if pet.pet_type.value not in ALLOWED_SPECIES:
        return False, f"Unrecognised species: {pet.pet_type.value}"
    if pet.age < 0 or pet.age > MAX_PET_AGE:
        return False, f"Pet age {pet.age} is outside the valid range (0 to {MAX_PET_AGE})."
    return True, ""


def _build_prompt(owner: Owner, pet: Pet, tasks: List[Task], rag_context: str) -> str:
    """Assemble the user-facing prompt from pet profile, tasks, and retrieved context."""
    task_lines = "\n".join(
        f"  - {t.name} ({t.task_type.value}, {t.duration_minutes} min, priority {t.priority}/5)"
        for t in tasks[:10]
    )
    needs_str = ", ".join(pet.special_needs) if pet.special_needs else "none"
    context_block = rag_context if rag_context else "No specific guidelines retrieved."

    prompt = (
        f"Pet Profile:\n"
        f"  Name: {pet.name}\n"
        f"  Species: {pet.pet_type.value}\n"
        f"  Age: {pet.age} years\n"
        f"  Special needs: {needs_str}\n"
        f"  Owner available time: {owner.daily_hours_available} hours/day\n\n"
        f"Scheduled tasks for today:\n"
        f"{task_lines if task_lines else '  No tasks scheduled yet.'}\n\n"
        f"Relevant care guidelines retrieved from the knowledge base:\n"
        f"{context_block}\n\n"
        f"Please provide specific care recommendations for {pet.name} based on the "
        f"profile and tasks above. Explain why the highest-priority tasks matter for "
        f"this specific pet. End with: CONFIDENCE: <score>"
    )

    if len(prompt) > MAX_PROMPT_LENGTH:
        prompt = prompt[:MAX_PROMPT_LENGTH] + "\n[Context truncated]"

    return prompt


def _extract_confidence(text: str) -> float:
    """Parse the CONFIDENCE score from the model response. Defaults to 0.5."""
    match = re.search(r"CONFIDENCE:\s*([01](?:\.\d+)?|\.\d+)", text)
    if match:
        try:
            return max(0.0, min(1.0, float(match.group(1))))
        except ValueError:
            pass
    return 0.5


def _rule_based_fallback(pet: Pet, tasks: List[Task], rag_context: str = "") -> str:
    """Generate care reminders without the Gemini API. Uses RAG context when available."""
    lines = [f"Care guidelines for {pet.name} ({pet.pet_type.value}, age {pet.age}):"]

    if pet.age >= 7:
        lines.append("  - Senior pet: schedule veterinary checkups every 6 months.")
    if any(t.task_type.value == "medication" for t in tasks) or "diabetic" in [
        n.lower() for n in pet.special_needs
    ]:
        lines.append("  - Medication tasks detected: maintain consistent daily timing.")
    if any(t.task_type.value == "walk" for t in tasks) or "needs_exercise" in [
        n.lower() for n in pet.special_needs
    ]:
        lines.append("  - Exercise is important: ensure walks occur at regular intervals.")
    if len(lines) == 1:
        lines.append("  - Keep up with scheduled feeding and enrichment tasks.")

    if rag_context:
        lines.append("\n**Relevant guidelines from the PawPal knowledge base:**")
        lines.append(rag_context)

    return "\n".join(lines)


def get_pet_recommendations(
    owner: Owner,
    pet: Pet,
    tasks: List[Task],
    api_key: Optional[str] = None,
) -> Tuple[str, float]:
    """Generate AI-powered care recommendations for a specific pet.

    Uses RAG to retrieve relevant knowledge base context, then calls the
    Gemini API to produce grounded, pet-specific advice. Falls back to a
    rule-based message if the API key is missing or a network error occurs.

    Args:
        owner: The Owner object (used for available hours context).
        pet: The Pet object to generate advice for.
        tasks: List of Task objects currently in the schedule.
        api_key: Optional API key override. Reads GOOGLE_API_KEY env var if None.

    Returns:
        (recommendation_text, confidence_score) tuple.
        confidence_score is 0.0 on validation failure, 0.3-0.4 on fallback,
        and 0.5-1.0 for live API responses.
    """
    is_valid, error_msg = validate_pet_input(pet)
    if not is_valid:
        logger.warning("Input validation failed: %s", error_msg)
        return f"Input validation failed: {error_msg}", 0.0

    task_types = [t.task_type.value for t in tasks]
    rag_context = retrieve_context(
        pet_species=pet.pet_type.value,
        pet_age=pet.age,
        special_needs=pet.special_needs,
        task_types=task_types,
    )

    key = api_key or os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        logger.warning("GOOGLE_API_KEY not set; using rule-based fallback.")
        return _rule_based_fallback(pet, tasks, rag_context), 0.4

    user_prompt = _build_prompt(owner, pet, tasks, rag_context)

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(user_prompt)
        raw = response.text
        confidence = _extract_confidence(raw)
        clean = re.sub(r"\n?CONFIDENCE:\s*[0-9.]+", "", raw).strip()
        logger.info("Recommendation generated. Confidence=%.2f", confidence)
        return clean, confidence

    except Exception as exc:
        error_type = type(exc).__name__
        if "API_KEY" in str(exc).upper() or "PERMISSION" in str(exc).upper() or "AUTH" in str(exc).upper():
            logger.error("Invalid API key: %s", str(exc))
            return "API authentication failed. Check your GOOGLE_API_KEY.", 0.0
        if "QUOTA" in str(exc).upper() or "RESOURCE_EXHAUSTED" in str(exc).upper():
            logger.warning("Rate limit hit; using fallback.")
            fallback = _rule_based_fallback(pet, tasks, rag_context)
            return fallback + "\n\n(Rate limit reached; using rule-based fallback)", 0.3
        logger.error("Gemini API error: %s", str(exc))
        fallback = _rule_based_fallback(pet, tasks, rag_context)
        return fallback + f"\n\n(AI unavailable: {error_type})", 0.3