# Model Card and Reflection: PawPal+ Applied AI System

---

## System Overview

**Model used:** Gemini 2.0 Flash (`gemini-2.0-flash`) via the Google Generative AI Python SDK

**Task:** Generate pet-specific care recommendations grounded in a curated knowledge base
using Retrieval-Augmented Generation (RAG).

**Input:** Pet profile (species, age, special needs), scheduled tasks, and retrieved
knowledge base context.

**Output:** 3 to 6 sentences of actionable care advice with a self-reported confidence score
between 0.0 and 1.0.

---

## AI Collaboration During Development

### How AI was used in this project

Claude Code was used throughout development for help with complicated code, debugging, and difficult design
decisions. Specific uses included generating the initial structure for `rag_engine.py`,
suggesting the paragraph-level chunking strategy for the knowledge base, and drafting
the system prompt for `ai_advisor.py`.

Beyond some code generation, Claude was used conversationally to reason through architectural
tradeoffs, such as whether to use vector embeddings or keyword frequency scoring for
retrieval, and whether `gemini-2.0-flash` or `gemini-1.5-pro` was more appropriate
for this use case.

### One instance where the AI suggestion was helpful

When asked how to handle the case where the Gemini API is unavailable, Claude Code suggested
implementing a rule-based fallback function that generates basic care reminders without
any API call. I didn't think of it at first, and this was pretty helpful because it made the system more robust and improved the user experience significantly. Without a fallback, the app would display an unhelpful error message whenever the API key was missing or the rate limit was hit.

The fallback approach was adopted exactly as suggested and is now part of `ai_advisor.py`.

### One instance where the AI suggestion was flawed

Claude initially suggested using `chromadb` as the vector store for RAG retrieval. This
was a poor fit for this project for two reasons: it added a heavy external dependency that
required a separate installation step, and it was significantly more complex to set up
than the task required. A simple keyword frequency scoring approach works well for
structured pet profile queries, requires no external dependencies beyond the standard
library, and is much easier for another student to understand and reproduce. The
`chromadb` suggestion was rejected and replaced with the `score_chunk` function in
`rag_engine.py`. This was a case where the AI defaulted to a more technically impressive
solution when a simpler one was clearly more appropriate.

---

## Limitations and Biases

### Knowledge base coverage

The knowledge base covers five document categories: dogs, cats, senior pets, medications,
and birds/rabbits. It does not cover exotic pets such as reptiles, fish, or rodents. A
user who adds a hamster or a gecko will receive generic advice rather than species-specific
guidance. This is a significant gap if the app were deployed to a general audience.

### Model knowledge cutoff

Gemini's training data has a knowledge cutoff, meaning it may not reflect the most
recent veterinary research or updated medication guidelines. Users should always verify
medical advice with a licensed veterinarian.

### Confidence score reliability

The confidence score is self-reported by the model, not independently verified. The model
tends to report high confidence (0.8 to 0.9) even when the retrieved context is a partial
match. This means users may over-trust advice for edge-case scenarios.

### Language and accessibility

The system only supports English. Pet owners who do not read English fluently cannot use
the AI Advisor tab effectively.

### Scheduling algorithm bias

The greedy priority-sorting algorithm always favors high-priority tasks when time is limited.
This means low-priority tasks (such as grooming or enrichment) may be dropped from the schedule
if the owner has limited availability, even when those tasks have health implications over time.

---

## Potential for Misuse

### Medical misguidance

The most significant misuse risk is a user following AI-generated advice for a serious
medical condition without consulting a veterinarian. For example, a user might adjust a
diabetic pet's insulin schedule based on the AI's recommendation without understanding
that insulin dosing must be supervised by a licensed professional.

**Prevention measures implemented:**
- A disclaimer is shown at the bottom of the AI Advisor tab reminding users to verify medical advice with a veterinarian.
- The system prompt instructs the model to flag health concerns that require professional attention.
- Confidence scores below 0.7 are displayed in orange to signal lower certainty.

### Data privacy

The system sends pet profiles and task data to the Google Gemini API. In a production
deployment, this should be disclosed to users, and personally identifiable information
(such as owner names) should be anonymized before transmission. The current implementation
does not anonymize data.

---

## What Surprised Me During Reliability Testing

The most surprising finding was how much the RAG retrieval quality affected the specificity
of the AI's recommendations. When a pet had no special needs and no tasks scheduled, the
retrieved context was generic (usually just the basic species care section), and the model's
response was similarly vague. As soon as a task like "medication" or a special need like
"diabetic" was added, the retrieval engine surfaced the medication timing guidelines, and
the model produced noticeably more targeted and actionable advice. This confirmed that the
RAG pipeline was genuinely influencing the output, not just running in parallel with a
standard response.

Another surprise was that the model consistently rated its own confidence at 0.85 to 0.92
across all valid scenarios, regardless of how specific the retrieved context was. This
suggests the self-reported confidence metric is not a reliable signal for output quality
and should not be used as the sole indicator of response trustworthiness in a real deployment.

---

## Future Improvements

- Replace keyword frequency scoring with embedding-based cosine similarity for more
  semantically accurate retrieval.
- Add species coverage for reptiles, fish, and small mammals to the knowledge base.
- Anonymize owner and pet names before sending data to the API.
- Implement independent confidence verification by comparing outputs across two model calls
  (a self-consistency check).
- Add persistent storage so pet profiles and schedules survive page refreshes.
- Support multiple languages for broader accessibility.