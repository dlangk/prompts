"""Style profile parser for daniel_writing_style.md."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class StyleProfile:
    """Extracted style profile from writing style document."""

    synthesis_instruction: str
    golden_rules: list[str]
    anti_patterns: list[str]

    def to_xml(self) -> str:
        """Convert style profile to XML format for prompts."""
        rules_text = "\n".join(f"- {rule}" for rule in self.golden_rules)
        anti_patterns_text = "\n".join(f"- {pattern}" for pattern in self.anti_patterns)

        return f"""<style_profile>
  <style_description>
{self.synthesis_instruction}
  </style_description>

  <style_rules>
Golden rules:
{rules_text}

Anti-patterns to avoid:
{anti_patterns_text}
  </style_rules>
</style_profile>"""


def parse_style_file(file_path: Path | str) -> StyleProfile:
    """Parse the writing style markdown file and extract key components."""
    file_path = Path(file_path)
    content = file_path.read_text()

    # Extract synthesis instruction (after "## SYNTHESIS: THE STYLE TRANSFER INSTRUCTION")
    synthesis_start = content.find("## SYNTHESIS: THE STYLE TRANSFER INSTRUCTION")
    golden_rules_start = content.find("## GOLDEN RULES")

    synthesis_instruction = ""
    if synthesis_start != -1 and golden_rules_start != -1:
        synthesis_section = content[synthesis_start:golden_rules_start]
        # Get the paragraph after the header
        lines = synthesis_section.split("\n")
        # Skip header and empty lines, get the instruction paragraph
        instruction_lines = []
        started = False
        for line in lines[1:]:
            if line.strip() and not line.startswith("#"):
                started = True
                instruction_lines.append(line)
            elif started and not line.strip():
                break
        synthesis_instruction = " ".join(instruction_lines).strip()

    # Extract golden rules (numbered 1-8)
    golden_rules = []
    if golden_rules_start != -1:
        # Find the end of golden rules section (next ## or end of file)
        remaining = content[golden_rules_start:]
        next_section = remaining.find("\n---")
        if next_section == -1:
            golden_section = remaining
        else:
            golden_section = remaining[:next_section]

        # Parse numbered rules
        import re

        rule_pattern = r"\d+\.\s+\*\*([^*]+)\*\*\s*(.+?)(?=\n\d+\.\s+\*\*|\Z)"
        matches = re.findall(rule_pattern, golden_section, re.DOTALL)
        for title, description in matches:
            # Clean up the description
            desc = description.strip().replace("\n", " ")
            golden_rules.append(f"{title.strip()}: {desc}")

    # Extract anti-patterns (LLM slop patterns)
    anti_patterns = []
    anti_start = content.find("### LLM slop patterns")
    if anti_start != -1:
        # Find the end of this subsection
        remaining = content[anti_start:]
        next_section = remaining.find("\n---")
        if next_section == -1:
            next_section = remaining.find("\n## ")
        if next_section == -1:
            anti_section = remaining
        else:
            anti_section = remaining[:next_section]

        # Parse bullet points
        for line in anti_section.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                pattern = line[2:].strip()
                # Remove quotes if present
                pattern = pattern.strip('"').strip("'")
                anti_patterns.append(pattern)

    return StyleProfile(
        synthesis_instruction=synthesis_instruction,
        golden_rules=golden_rules,
        anti_patterns=anti_patterns,
    )


def get_default_style_profile() -> StyleProfile:
    """Get the default style profile from daniel_writing_style.md."""
    # Look for the file in common locations
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "daniel_writing_style.md",
        Path.cwd() / "daniel_writing_style.md",
    ]

    for path in possible_paths:
        if path.exists():
            return parse_style_file(path)

    # Return a minimal default if file not found
    return StyleProfile(
        synthesis_instruction="Write in first person with confident hedging. Lead paragraphs with bold claims, then unpack them.",
        golden_rules=[
            "Own every claim with 'I think' or 'I believe'",
            "Bold the thesis, then earn it with reasoning",
            "Punch short after thinking long",
            "Show the seams - admit mistakes and doubts",
            "Never perform - no hype, no false modesty",
            "Frameworks over arguments",
            "Trust the reader",
            "Keep it grounded with concrete examples",
        ],
        anti_patterns=[
            "Let's dive in / Let's unpack this",
            "Here's the thing / Here's why that matters",
            "Numbered takeaway lists at the end",
            "Starting multiple paragraphs with 'The'",
            "Ending with 'And that's the power of [concept]'",
        ],
    )
