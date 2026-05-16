"""Pydantic models for the pipeline."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskCategory(str, Enum):
    """Classification categories for prompts."""

    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    EXTRACTION = "extraction"


class ClassificationResult(BaseModel):
    """Result of prompt classification."""

    category: TaskCategory
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ExpandedPrompt(BaseModel):
    """Expanded prompt with XML-tagged structure."""

    system_prompt: str
    context: Optional[str] = None
    task: str
    constraints: Optional[str] = None
    purpose: Optional[str] = None  # for creative tasks
    audience: Optional[str] = None  # for creative tasks
    output_format: Optional[str] = None  # for extraction tasks

    def to_user_message(self) -> str:
        """Build the user message from XML-tagged blocks."""
        parts = []

        if self.context:
            parts.append(f"<context>\n{self.context}\n</context>")

        if self.purpose:
            parts.append(f"<purpose>\n{self.purpose}\n</purpose>")

        if self.audience:
            parts.append(f"<audience>\n{self.audience}\n</audience>")

        parts.append(f"<task>\n{self.task}\n</task>")

        if self.constraints:
            parts.append(f"<constraints>\n{self.constraints}\n</constraints>")

        if self.output_format:
            parts.append(f"<output_format>\n{self.output_format}\n</output_format>")

        return "\n\n".join(parts)

    def to_full_prompt(self) -> str:
        """Return the complete prompt ready for Claude web UI."""
        return f"System: {self.system_prompt}\n\n{self.to_user_message()}"
