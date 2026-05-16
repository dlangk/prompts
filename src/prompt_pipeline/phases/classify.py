"""Phase 1: Classify the prompt into task categories."""

import json

import anthropic
from anthropic.types import TextBlock

from ..config import HAIKU_MODEL, MAX_TOKENS_CLASSIFY
from ..models import ClassificationResult, TaskCategory

CLASSIFICATION_PROMPT = """Classify the following user prompt into exactly one category.

Categories and their signals:
- research: "what is", "how does", "compare", topic keywords, questions about concepts
- analysis: "analyze", "evaluate", company/market references, data interpretation
- creative: "write", "draft", "blog", "memo", "reflect", content creation
- extraction: "summarize", "list", "extract", "find", structured output requests

<prompt>
{prompt}
</prompt>

Respond with a JSON object containing:
- "category": one of "research", "analysis", "creative", "extraction"
- "confidence": float between 0 and 1
- "reasoning": brief explanation of why this category was chosen

JSON response:"""


def classify_prompt(
    prompt: str, client: anthropic.Anthropic | None = None
) -> ClassificationResult:
    """Classify a prompt into one of four task categories.

    Args:
        prompt: The user's raw prompt to classify.
        client: Optional Anthropic client. Creates one if not provided.

    Returns:
        ClassificationResult with category, confidence, and reasoning.
    """
    if client is None:
        client = anthropic.Anthropic()

    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=MAX_TOKENS_CLASSIFY,
        messages=[
            {
                "role": "user",
                "content": CLASSIFICATION_PROMPT.format(prompt=prompt),
            },
            {
                "role": "assistant",
                "content": "{",
            },
        ],
    )

    # Parse the response (prefilled with "{")
    first_block = response.content[0]
    if not isinstance(first_block, TextBlock):
        return ClassificationResult(
            category=TaskCategory.RESEARCH,
            confidence=0.5,
            reasoning="Unexpected response type from API",
        )
    response_text = "{" + first_block.text
    try:
        data = json.loads(response_text)
        return ClassificationResult(
            category=TaskCategory(data["category"]),
            confidence=float(data["confidence"]),
            reasoning=data["reasoning"],
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Fallback to research if parsing fails
        return ClassificationResult(
            category=TaskCategory.RESEARCH,
            confidence=0.5,
            reasoning=f"Failed to parse classification response: {e}",
        )
