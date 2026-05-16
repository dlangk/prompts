# Prompt Expansion Pipeline — Anthropic Claude API

Requirements spec for a pipeline that takes a primitive user question and produces a high-quality, style-matched report via the Anthropic Messages API.

Architecture: **classify → expand → generate → restyle**

Target models: `claude-opus-4-5-20251101`, `claude-sonnet-4-5-20250929`, `claude-haiku-4-5-20251001`

---

## Phase 1: Classify

Determine task type from the primitive prompt. This controls all downstream decisions: model selection, extended thinking, prompt structure, and whether format constraints are allowed.

| Category | Signals | Extended thinking | Format constraints | Model |
|---|---|---|---|---|
| `research` | "what is", "how does", "compare", topic keywords | Yes, `budget_tokens: 10000`+ | No — free text only | `opus-4-5` or `sonnet-4-5` |
| `analysis` | "analyze", "evaluate", company/market references | Yes, `budget_tokens: 10000`+ | No — free text only | `opus-4-5` or `sonnet-4-5` |
| `creative` | "write", "draft", "blog", "memo", "reflect" | No | No — style applied in Phase 4 | `opus-4-5` or `sonnet-4-5` |
| `extraction` | "summarize", "list", "extract", "find" | No | Yes — JSON/XML constraints help here | `haiku-4-5` or `sonnet-4-5` |

---

## Phase 2: Expand

Transform the primitive prompt into a structured Claude API request using XML tags. Claude was trained on XML-tagged prompts — this is the single highest-impact structural decision.

### System prompt

Use the `system` parameter for role assignment only. Keep it short. Put all detailed instructions in the user message.

```python
system = "You are a senior research analyst specializing in {domain}."
```

### User message structure

Build the user message from XML-tagged blocks. Use consistent tag names and refer to them explicitly in instructions (e.g., "Using the data in <context> tags...").

```xml
<context>
{background information, uploaded documents, prior conversation context}
</context>

<task>
{decomposed subtasks derived from the primitive prompt}
</task>

<constraints>
{content boundaries: scope, depth, citation requirements, what to exclude}
</constraints>
```

### Expansion rules by task type

**For `research` and `analysis`:**
- Decompose the primitive prompt into 3-5 explicit subtasks inside `<task>`
- Add `<constraints>` requiring evidence and source attribution
- Do NOT add `<output_format>` — let the model choose its own structure
- Do NOT add tone, voice, length, or structural instructions
- When extended thinking is OFF and targeting Opus 4.5: replace the word "think" with "consider", "evaluate", or "assess" in all instructions. Opus 4.5 is sensitive to "think" when extended thinking is disabled

**For `creative`:**
- Add `<purpose>` and `<audience>` tags
- Do NOT add style, tone, or voice instructions — these go in Phase 4
- Do NOT add length constraints — trim in Phase 4

**For `extraction`:**
- This is the ONE category where format constraints improve accuracy
- Add `<output_format>` with explicit JSON schema or structured template
- Use assistant prefill to enforce format (see below)

### What to NEVER include in expanded prompts

- Tone instructions ("write in a professional tone")
- Voice constraints ("use active voice", "be concise")
- Length targets ("write 800 words")
- Structural mandates ("use headers and bullet points")
- JSON/XML schema constraints on `research` or `analysis` tasks — these cause 25-63% accuracy degradation by forcing answer-before-reasoning ordering

Exception: all of the above are permitted for `extraction` tasks.

---

## Phase 3: Generate

Execute the expanded prompt against the Claude API.

### API request construction

```python
import anthropic

client = anthropic.Anthropic()

# Base request
request = {
    "model": model_id,           # from classification
    "max_tokens": 16000,         # generous ceiling, do not constrain
    "system": system_prompt,     # role only
    "messages": [
        {"role": "user", "content": user_message}  # XML-tagged prompt from Phase 2
    ]
}
```

### Extended thinking (research and analysis only)

Enable for `research` and `analysis` tasks. Do not enable for `creative` or `extraction`.

```python
request["thinking"] = {
    "type": "enabled",
    "budget_tokens": 10000  # start here, increase for complex tasks
}
```

- Start at `budget_tokens: 10000`. Increase to 20000-50000 for multi-step reasoning
- The budget is a target, not a strict limit — actual usage varies by task
- Do NOT prefill assistant responses when extended thinking is enabled. Prefilling is explicitly incompatible with extended thinking
- Add instruction: "Do not repeat your extended thinking in your response. Output only the final answer."

### Effort parameter (optional optimization)

Use the `effort` parameter to control token spend across the entire response. Requires beta header `effort-2025-11-24`.

```python
request["betas"] = ["effort-2025-11-24"]
request["effort"] = "high"  # default. Use "low" for simple extraction tasks
```

- `"high"`: maximum quality, use for `research` and `analysis`
- `"medium"`: good for `creative` tasks
- `"low"`: use for `extraction` and simple classification

### Assistant prefill (extraction only)

For `extraction` tasks without extended thinking, prefill the assistant response to skip preamble and enforce format:

```python
request["messages"].append(
    {"role": "assistant", "content": "{"}  # forces JSON output
)
```

- Prefill `{` for JSON, `<result>` for XML output
- Do NOT use prefill with extended thinking enabled
- Do NOT use prefill for `research`, `analysis`, or `creative` tasks

### Multi-agent research (complex research only)

For complex research tasks requiring multiple sources or perspectives, use parallel sub-agents:

```python
# Spawn 3-5 sub-agents with distinct retrieval scopes
sub_queries = decompose(primitive_prompt)  # from Phase 2

results = await asyncio.gather(*[
    client.messages.create(
        model="claude-sonnet-4-5-20250929",  # use Sonnet for sub-agents (cost)
        thinking={"type": "enabled", "budget_tokens": 5000},
        messages=[{"role": "user", "content": sub_query}]
    )
    for sub_query in sub_queries
])

# Synthesize with Opus
synthesis_prompt = f"""
<sub_results>
{format_results(results)}
</sub_results>

<task>
Synthesize these research results into a coherent analysis.
Resolve any contradictions. Identify consensus and open questions.
</task>
"""
```

- Use `sonnet-4-5` for sub-agents, `opus-4-5` for synthesis (cost optimization)
- Enable interleaved thinking for tool-using sub-agents: add beta header `interleaved-thinking-2025-05-14`
- Budget: multi-agent uses ~15x more tokens than single-pass. Reserve for tasks where depth justifies cost

### Quality gate

Before proceeding to Phase 4, validate the generation output. Run a single Self-Refine pass if needed:

```xml
<generated_output>
{output from Phase 3}
</generated_output>

<task>
Review this output for:
1. Are all subtasks from the original request addressed?
2. Are claims supported by evidence or reasoning?
3. Are there internal contradictions?
4. Are there obvious gaps or missing perspectives?

If issues are found, produce a corrected version. If no issues, respond with "PASS" only.
</task>
```

- Maximum 2 refinement iterations. Quality plateaus after that
- Use the same model that generated the output
- If validation passes, proceed directly to Phase 4

---

## Phase 4: Restyle

Apply the user's writing style to the generated content. This is a separate API call — never combine style application with content generation.

### Style profile structure

Store as a reusable XML block:

```xml
<style_profile>
  <style_description>
  {LLM-generated description of the user's writing style: sentence structure,
   vocabulary patterns, rhetorical habits, tone, distinctive choices}
  </style_description>

  <style_examples>
    <example>
    {writing sample 1 — 200-500 words}
    </example>
    <example>
    {writing sample 2 — 200-500 words}
    </example>
  </style_examples>

  <style_rules>
  {explicit rules: e.g., "never use bullet points in prose",
   "prefer analogies from complex systems theory",
   "use first person sparingly"}
  </style_rules>
</style_profile>
```

### Restyle prompt

```xml
<content>
{output from Phase 3}
</content>

<style_profile>
{style profile from above}
</style_profile>

<task>
Rewrite the content to match the writing style described in <style_profile>.

Preserve all factual information, arguments, evidence, and logical structure.
Change only voice, tone, sentence construction, and word choice.

Target length: {length_target} words.
Structure: {structural_preferences — e.g., "prose paragraphs, no bullet points"}
</task>
```

### Restyle rules

- Use `sonnet-4-5` for restyling (Opus is overkill for style transfer)
- Do NOT enable extended thinking for restyle — it's a surface transformation, not reasoning
- For content >1000 tokens: segment into 500-1000 token chunks, include `<style_profile>` with each chunk, then validate consistency across chunks
- Apply length targets HERE, not in Phase 3
- Apply structural preferences (headers, bullets, prose) HERE, not in Phase 3
- Maximum 2 restyle iterations. If the output still doesn't match after 2 passes, update the style profile, don't add more iterations

### Building the style profile

When creating a new profile from writing samples:

```python
profile_prompt = """
<writing_samples>
{2-6 samples, 200-500 words each}
</writing_samples>

<task>
Analyze these writing samples and produce a detailed style guide covering:
- Sentence length and variation patterns
- Vocabulary level and domain-specific terminology
- Use of metaphor, analogy, and rhetorical devices
- Paragraph structure and transitions
- Tone (formal/informal spectrum, warmth, directness)
- Distinctive habits or recurring patterns
- What the author avoids (e.g., jargon, passive voice, lists)
</task>
"""
```

- 2-6 samples is the sweet spot. Quality matters more than quantity. Diminishing returns after 6
- Regenerate the style description if writing style evolves — don't just add more samples

---

## Prompt caching

For pipelines that reuse the same system prompt, style profile, or context across multiple calls, use Anthropic's prompt caching to reduce latency and cost.

- Place stable content (system prompt, style profile, role definition) at the beginning of the message sequence
- Variable content (the specific task, generated output for restyling) goes at the end
- Cached prefixes are only charged 10% of normal input token cost on cache hits

---

## Model selection summary

| Phase | Model | Why |
|---|---|---|
| Classification | `haiku-4-5` | Fast, cheap, classification is simple |
| Expansion | `haiku-4-5` | Template assembly, not reasoning |
| Generation (simple) | `sonnet-4-5` | Best balance of quality and cost |
| Generation (complex) | `opus-4-5` | Maximum reasoning capability |
| Sub-agents | `sonnet-4-5` | Cost-efficient for parallel work |
| Synthesis | `opus-4-5` | Needs highest reasoning for integration |
| Quality gate | Same as generation | Consistency with original output |
| Restyle | `sonnet-4-5` | Style transfer doesn't need Opus |
| Style profile generation | `sonnet-4-5` | One-time cost, moderate reasoning |

---

## Anti-patterns

- **Style + reasoning in one pass**: never combine format/style constraints with reasoning-heavy generation. Separate them into Phase 3 and Phase 4
- **Prefill with extended thinking**: explicitly not supported. Will degrade results
- **"Think" with Opus 4.5**: when extended thinking is OFF, avoid the word "think" — use "consider", "evaluate", "assess" instead
- **JSON schema on reasoning tasks**: forces answer-before-reasoning token ordering, kills chain-of-thought. Use only for `extraction`
- **Unbounded refinement loops**: cap at 2 iterations per phase. Diminishing returns are steep
- **Over-engineering prompts**: first 5-10 hours of prompt development provides most value. If you're iterating 20+ hours on the same prompt, it's an architecture problem
- **Skipping classification**: applying the same prompt structure to all task types wastes quality on extraction and wastes tokens on creative tasks
