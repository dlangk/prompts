"""Phase 4: Restyle content to match writing style profile."""

import anthropic
from anthropic.types import TextBlock

from ..config import MAX_TOKENS_RESTYLE, SONNET_MODEL
from ..style import StyleProfile, get_default_style_profile

RESTYLE_PROMPT = """<content>
{content}
</content>

{style_profile}

<task>
Rewrite the content to match the writing style described in <style_profile>.

Preserve all factual information, arguments, evidence, and logical structure.
Change only voice, tone, sentence construction, and word choice.

Key requirements:
- Use first person ("I think", "I believe") to own claims
- Lead paragraphs with bold assertions, then unpack with reasoning
- Vary sentence length: follow 20-30 word analytical sentences with short 5-10 word punches
- Show intellectual honesty - acknowledge limits and uncertainties
- Use analogies from betting, physics, biology, or pop culture
- End with pragmatism or honest incompleteness, never inspirational crescendos
- Avoid ALL anti-patterns listed in the style profile

Structure: prose paragraphs with occasional bold thesis statements. No bullet points in analytical sections unless presenting parallel items of comparable weight.
</task>"""


def restyle_content(
    content: str,
    style_profile: StyleProfile | None = None,
    client: anthropic.Anthropic | None = None,
) -> str:
    """Restyle content to match the given writing style profile.

    Args:
        content: The raw content to restyle (from Claude web UI).
        style_profile: Optional style profile. Uses default if not provided.
        client: Optional Anthropic client. Creates one if not provided.

    Returns:
        Restyled content matching the style profile.
    """
    if client is None:
        client = anthropic.Anthropic()

    if style_profile is None:
        style_profile = get_default_style_profile()

    prompt = RESTYLE_PROMPT.format(
        content=content,
        style_profile=style_profile.to_xml(),
    )

    response = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=MAX_TOKENS_RESTYLE,
        messages=[{"role": "user", "content": prompt}],
    )

    first_block = response.content[0]
    if isinstance(first_block, TextBlock):
        return first_block.text
    return ""
