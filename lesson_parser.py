import os
import json
import re
from typing import List, Dict, Any

from groq import Groq


SYSTEM_PROMPT = """You are a structured curriculum parser.
Given a lesson, break it into ordered concept chunks.
Return ONLY a valid JSON array - no markdown, no explanation, no code fences.

Each element must follow this exact schema:
{
  "order": <int starting at 1>,
  "text": "<verbatim excerpt or paraphrase from the lesson>",
  "concepts": ["<concept name introduced in this chunk>"],
  "prerequisites": ["<concept name required to understand this chunk>"]
}

Rules:
- Every concept name used in "prerequisites" must appear in a previous chunk's "concepts".
- The first chunk must have an empty "prerequisites" list.
- Use concise concept names (1-5 words).
- Cover the full lesson without gaps."""


def parse_lesson(text: str) -> List[Dict[str, Any]]:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        max_completion_tokens=8192,
        reasoning_effort="low",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this lesson into concept chunks:\n\n{text}"},
        ],
    )

    raw = (response.choices[0].message.content or "").strip()

    # Strip markdown code fences if the model wraps them anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    chunks = json.loads(raw)
    if not isinstance(chunks, list):
        raise ValueError("Expected a list of lesson chunks")

    # Validate basic structure
    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"Chunk {i} must be an object")
        if "order" not in chunk:
            chunk["order"] = i + 1
        if not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
            raise ValueError(f"Chunk {i} needs non-empty text")
        if "concepts" not in chunk:
            chunk["concepts"] = []
        if "prerequisites" not in chunk:
            chunk["prerequisites"] = []
        for field in ("concepts", "prerequisites"):
            if not isinstance(chunk[field], list) or not all(isinstance(item, str) for item in chunk[field]):
                raise ValueError(f"Chunk {i} {field} must be a list of strings")
        chunk["order"] = i + 1

    return chunks
