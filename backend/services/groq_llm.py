"""
VoiceTrace AI — Groq LLM Service
Provides: entity extraction, memory importance analysis,
          and final response generation.

NOTE: Safety guardrails are handled by services/guardrail.py
"""
from __future__ import annotations

import json
import re
from groq import Groq
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import (
    GROQ_API_KEY,
    GROQ_FAST_MODEL,
    GROQ_MEMORY_MODEL,
    GROQ_RESPONSE_MODEL,
)

client = Groq(api_key=GROQ_API_KEY)


# ═══════════════════════════════════════════════════════════════════════
#  Retry decorator for Groq calls
# ═══════════════════════════════════════════════════════════════════════

groq_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: logger.warning(
        f"Groq retry attempt {rs.attempt_number} after error: {rs.outcome.exception()}"
    ),
)


# ═══════════════════════════════════════════════════════════════════════
#  Entity Extraction
# ═══════════════════════════════════════════════════════════════════════

EXTRACTION_PROMPT = """You are a business data extraction assistant.
Analyze the following transcript from a small business owner and extract structured information.

Return ONLY valid JSON with these fields:
{{
  "items_sold": [{{ "item": "string", "quantity": number, "price": number }}],
  "expenses": [{{ "description": "string", "amount": number }}],
  "total_earnings": number,
  "total_expenses": number,
  "net_profit": number,
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "key_topics": ["string"],
  "summary": "One-sentence summary of the business activity"
}}

If a field cannot be determined, use null or empty array.

TRANSCRIPT:
{transcript}
"""


@groq_retry
def extract_entities(transcript: str) -> dict:
    """Extract structured business data from transcript."""
    logger.info("Extracting entities from transcript")

    response = client.chat.completions.create(
        model=GROQ_FAST_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise data extraction assistant. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": EXTRACTION_PROMPT.format(transcript=transcript),
            },
        ],
        temperature=0.1,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to find JSON in response
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            logger.error(f"Failed to parse extraction JSON: {raw[:200]}")
            data = {"error": "Failed to parse extraction response", "raw": raw[:500]}

    logger.info(f"Extraction complete: {list(data.keys())}")
    return data


# ═══════════════════════════════════════════════════════════════════════
#  Memory Importance Analysis
# ═══════════════════════════════════════════════════════════════════════

MEMORY_ANALYSIS_PROMPT = """You are a memory importance classifier for a business assistant.

Analyze the following transcript and extracted business data. Determine if this information
contains IMPORTANT long-term insights worth remembering.

Important memories include:
- Significant business events (large sales, new customers, unusual expenses)
- Trends or patterns (declining sales, growing demand)
- Strategic decisions or changes mentioned
- Financial milestones or concerns
- Key business relationships or partnerships

NOT important:
- Routine daily transactions of small amounts
- General greetings or small talk
- Repeated information already stored
- Test or trivial messages

TRANSCRIPT:
{transcript}

EXTRACTED DATA:
{extracted_data}

Return ONLY valid JSON:
{{
  "is_important": true/false,
  "reasoning": "Brief explanation of why this is or isn't important",
  "formatted_memory": "A concise, well-formatted summary of the key insight (null if not important)"
}}
"""


@groq_retry
def analyze_memory_importance(transcript: str, extracted_data: dict) -> dict:
    """Classify whether the transcript contains important long-term insights."""
    logger.info("Analyzing memory importance")

    response = client.chat.completions.create(
        model=GROQ_MEMORY_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a memory importance classifier. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": MEMORY_ANALYSIS_PROMPT.format(
                    transcript=transcript,
                    extracted_data=json.dumps(extracted_data, indent=2),
                ),
            },
        ],
        temperature=0.1,
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse memory analysis JSON: {raw[:200]}")
        data = {"is_important": False, "formatted_memory": None}

    logger.info(f"Memory importance: {data.get('is_important', False)}")
    return data


# ═══════════════════════════════════════════════════════════════════════
#  Final Response Generation
# ═══════════════════════════════════════════════════════════════════════

RESPONSE_PROMPT = """You are VoiceTrace AI — a friendly, insightful business assistant.

Based on the following information, provide a clear, actionable summary for the business owner.

TODAY'S TRANSCRIPT:
{transcript}

EXTRACTED DATA:
{extracted_data}

RELATED PAST MEMORIES (from previous conversations):
{past_memories}

Provide:
1. **Today's Summary** — What happened today in simple terms
2. **Key Insights** — Patterns, trends, or notable observations
3. **Recommendations** — Actionable advice based on today's data and past trends

Keep your response concise, warm, and professional. Use bullet points where helpful.
If there are relevant past memories, explicitly reference them to show continuity.
"""


@groq_retry
def generate_response(
    transcript: str,
    extracted_data: dict,
    past_memories: list[dict],
) -> str:
    """Generate the final AI response combining current data with past context."""
    logger.info("Generating final response")

    memories_text = "\n".join(
        f"- {m.get('formatted_memory', m.get('text', 'N/A'))}"
        for m in past_memories
    ) if past_memories else "No relevant past memories found."

    response = client.chat.completions.create(
        model=GROQ_RESPONSE_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are VoiceTrace AI, a business assistant that helps "
                    "small business owners track and understand their daily operations."
                ),
            },
            {
                "role": "user",
                "content": RESPONSE_PROMPT.format(
                    transcript=transcript,
                    extracted_data=json.dumps(extracted_data, indent=2),
                    past_memories=memories_text,
                ),
            },
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    result = response.choices[0].message.content.strip()
    logger.info(f"Final response generated ({len(result)} chars)")
    return result
