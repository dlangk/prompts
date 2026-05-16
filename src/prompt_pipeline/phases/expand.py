"""Phase 2: Expand the prompt into structured XML format."""

import json

import anthropic
from anthropic.types import TextBlock

from ..config import HAIKU_MODEL, MAX_TOKENS_EXPAND
from ..models import ClassificationResult, ExpandedPrompt, TaskCategory

EXPANSION_PROMPT_RESEARCH_ANALYSIS = """Transform this primitive prompt into a structured Claude API request.

<primitive_prompt>
{prompt}
</primitive_prompt>

<task_category>{category}</task_category>

Rules for {category} tasks:
- Create a short system prompt for role assignment only (one sentence)
- Decompose the primitive prompt into 3-5 explicit subtasks
- Add constraints requiring evidence and source attribution
- Do NOT add output_format - let the model choose its own structure
- Do NOT add tone, voice, length, or structural instructions
- Replace the word "think" with "consider", "evaluate", or "assess"

Respond with a JSON object:
{{
  "system_prompt": "You are a senior [domain] analyst.",
  "context": "Background information if needed, or null",
  "task": "Decomposed subtasks as numbered list",
  "constraints": "Evidence and citation requirements"
}}

JSON response:"""

EXPANSION_PROMPT_CREATIVE = """Transform this primitive prompt into a structured Claude API request.

<primitive_prompt>
{prompt}
</primitive_prompt>

<task_category>creative</task_category>

Rules for creative tasks:
- Create a short system prompt for role assignment only (one sentence)
- Add purpose and audience tags
- Do NOT add style, tone, or voice instructions - these go in a later phase
- Do NOT add length constraints

Respond with a JSON object:
{{
  "system_prompt": "You are a [role].",
  "context": "Background information if needed, or null",
  "task": "The creative task",
  "purpose": "The purpose of this content",
  "audience": "The intended audience"
}}

JSON response:"""

EXPANSION_PROMPT_EXTRACTION = """Transform this primitive prompt into a structured Claude API request.

<primitive_prompt>
{prompt}
</primitive_prompt>

<task_category>extraction</task_category>

Rules for extraction tasks:
- Create a short system prompt for role assignment only (one sentence)
- Add explicit output_format with JSON schema or structured template
- This is the ONE category where format constraints improve accuracy

Respond with a JSON object:
{{
  "system_prompt": "You are a data extraction specialist.",
  "context": "Background information if needed, or null",
  "task": "The extraction task",
  "constraints": "Any constraints on the extraction",
  "output_format": "The expected output schema"
}}

JSON response:"""


def expand_prompt(
    prompt: str,
    classification: ClassificationResult,
    client: anthropic.Anthropic | None = None,
) -> ExpandedPrompt:
    """Expand a prompt into XML-tagged structure based on its classification.

    Args:
        prompt: The user's raw prompt to expand.
        classification: The classification result from phase 1.
        client: Optional Anthropic client. Creates one if not provided.

    Returns:
        ExpandedPrompt with structured components.
    """
    if client is None:
        client = anthropic.Anthropic()

    # Select the appropriate expansion template
    if classification.category in (TaskCategory.RESEARCH, TaskCategory.ANALYSIS):
        expansion_prompt = EXPANSION_PROMPT_RESEARCH_ANALYSIS.format(
            prompt=prompt, category=classification.category.value
        )
    elif classification.category == TaskCategory.CREATIVE:
        expansion_prompt = EXPANSION_PROMPT_CREATIVE.format(prompt=prompt)
    else:  # EXTRACTION
        expansion_prompt = EXPANSION_PROMPT_EXTRACTION.format(prompt=prompt)

    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=MAX_TOKENS_EXPAND,
        messages=[
            {"role": "user", "content": expansion_prompt},
            {"role": "assistant", "content": "{"},
        ],
    )

    # Parse the response (prefilled with "{")
    first_block = response.content[0]
    if not isinstance(first_block, TextBlock):
        return ExpandedPrompt(
            system_prompt="You are a helpful assistant.",
            task=prompt,
            constraints="Unexpected response type from API",
        )
    response_text = "{" + first_block.text
    try:
        data = json.loads(response_text)
        return ExpandedPrompt(
            system_prompt=data.get("system_prompt", "You are a helpful assistant."),
            context=data.get("context"),
            task=data.get("task", prompt),
            constraints=data.get("constraints"),
            purpose=data.get("purpose"),
            audience=data.get("audience"),
            output_format=data.get("output_format"),
        )
    except (json.JSONDecodeError, KeyError) as e:
        # Fallback to a basic expansion
        return ExpandedPrompt(
            system_prompt="You are a helpful assistant.",
            task=prompt,
            constraints=f"Expansion failed: {e}",
        )
