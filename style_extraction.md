Writing Style Extraction Prompt
Purpose
This prompt is designed to extract a detailed, actionable writing style profile from a corpus of writing samples. The output is intended for style transfer — i.e., to be used as a system prompt or style guide that enables an LLM to produce new text that reads as if written by the same author.
How to Use

Run the extraction prompt (Section A below) against your full corpus, or against representative samples (~15-20k tokens covering different topics and moods).
Review and edit the resulting style profile. The author should verify it and correct anything that feels off — you know your voice better than any model.
Use the style profile as a system prompt prefix when generating new text, ideally combined with 2-3 representative writing samples as few-shot examples in the conversation history.


Section A: The Extraction Prompt
Paste the following as a prompt, with your writing samples appended after the <writing_samples> tag.
You are a computational stylometrist and writing coach. Your task is to analyze a corpus of writing samples by a single author and produce a detailed, structured **Writing Style Profile** that could be used to instruct another writer (or an LLM) to produce text in the same style.

This is NOT a summary of what the author writes about. This is an analysis of HOW they write — their voice, rhythm, structure, and rhetorical habits. The profile must be specific enough that someone unfamiliar with the author could reproduce the style on a completely different topic.

Analyze the writing samples below across the following dimensions. For each dimension, provide:
- A clear description of the pattern
- 2-3 SHORT illustrative quotes (under 15 words each) showing the pattern in action
- Where relevant, contrast with what the author does NOT do

---

### DIMENSION 1: SENTENCE-LEVEL PATTERNS

**1a. Sentence length and rhythm**
- What is the typical sentence length range?
- How does the author vary sentence length for effect? (e.g., short punchy sentences after longer analytical ones)
- What is the characteristic rhythm or cadence?

**1b. Sentence openings**
- How do sentences typically begin? (e.g., "I", subject-first, conjunctions, temporal markers)
- Does the author use sentence fragments? How often?
- Are there signature opening patterns?

**1c. Voice and person**
- What grammatical person dominates? (first, second, third)
- How does the author shift between persons, and when?
- Active vs. passive voice ratio and usage patterns

**1d. Hedging and certainty**
- How does the author express uncertainty? (specific phrases, qualifiers)
- How does the author express conviction? (specific phrases, patterns)
- What is the balance between the two?

---

### DIMENSION 2: PARAGRAPH AND SECTION ARCHITECTURE

**2a. Paragraph structure**
- Typical paragraph length (sentences)
- How do paragraphs open and close?
- How does the author transition between paragraphs?

**2b. Essay/post structure**
- How does the author typically open a piece?
- How are arguments structured? (linear, dialectical, exploratory, etc.)
- How do pieces typically end?
- What role do section headers play?

**2c. Use of lists, bullets, and structured elements**
- When does the author switch from prose to lists?
- How are lists formatted and how long are list items?
- How does the author integrate structured elements back into prose flow?

---

### DIMENSION 3: WORD CHOICE AND VOCABULARY

**3a. Register and formality**
- Where does the writing fall on formal ↔ conversational spectrum?
- Does the register shift within a piece? When and why?
- Technical vocabulary usage patterns

**3b. Distinctive vocabulary**
- Are there signature words or phrases the author gravitates toward?
- What words does the author notably AVOID?
- Any recurring metaphor domains or analogies?

**3c. Emphasis and intensifiers**
- How does the author create emphasis? (bold, italics, punctuation, word choice)
- What intensifiers are used? Which are avoided?
- Use of typographic emphasis (bold, italics, caps, emoji)

---

### DIMENSION 4: RHETORICAL AND ARGUMENTATIVE STYLE

**4a. How claims are introduced**
- Does the author assert, propose, or explore?
- How are opinions distinguished from facts?
- How does the author handle nuance and caveats?

**4b. Use of evidence and authority**
- How does the author reference sources? (links, names, books, data)
- How are examples and anecdotes deployed?
- How does the author handle disagreement with others' views?

**4c. Rhetorical devices**
- What questions does the author ask? (rhetorical, genuine, section-opening)
- Use of analogies, thought experiments, or hypotheticals
- Any recurring structural devices (e.g., "Let's imagine...", numbered arguments)

**4d. Engagement with the reader**
- How directly does the author address the reader?
- What relationship does the author assume with the reader? (peer, teacher, fellow explorer)
- How does the author create a sense of dialogue or shared inquiry?

---

### DIMENSION 5: EMOTIONAL REGISTER AND PERSONA

**5a. Emotional tone**
- What is the baseline emotional temperature? (warm, clinical, passionate, detached)
- How does the author express enthusiasm, frustration, uncertainty, humor?
- How much personal vulnerability is revealed?

**5b. Intellectual stance**
- How does the author position themselves? (expert, learner, questioner)
- What is the relationship between confidence and humility?
- How does the author handle complexity — does it energize or frustrate them?

**5c. Humor and personality**
- What kind of humor appears, if any? (dry, self-deprecating, playful, sardonic)
- How does personality manifest in word choice and rhythm?
- What makes this author's voice distinctive from "generic smart person writing on the internet"?

---

### DIMENSION 6: ANTI-PATTERNS (What the author does NOT do)

This section is critical for style transfer. LLMs have strong default tendencies. Explicitly list patterns this author avoids:

- Clichés or stock phrases the author never uses
- Structural habits the author avoids (e.g., "In conclusion," grand summaries)
- Tonal qualities absent from the writing (e.g., breathless enthusiasm, false modesty)
- Any "LLM slop" patterns (e.g., "It's not X — it's Y", "Let's dive in", "Here's the thing") that would be foreign to this author's voice

---

### SYNTHESIS: THE STYLE TRANSFER INSTRUCTION

Finally, compress the entire analysis into a **single, dense paragraph of 150-250 words** that could serve as a system prompt for an LLM. This paragraph should be written as direct instructions (e.g., "Write in first person. Use short, assertive sentences..."). It should capture the essence of the style without referencing specific content topics.

Follow this with a **short list of 5-8 "golden rules"** — the most important style constraints that, if violated, would immediately make the text feel inauthentic.

---

<writing_samples>
[PASTE YOUR WRITING SAMPLES HERE]
</writing_samples>

Section B: Building a Few-Shot Style Prompt
After extracting the style profile, use this structure for generating new text:
System Prompt Structure
[Paste the SYNTHESIS paragraph and golden rules from the extraction output]

It is crucial that you follow the style described above. Avoid stereotypical,
generic, or cliché language. Specifically avoid:
- Phrases like "it's not X — it's Y", "Here's the thing", "Let's dive in"
- Repeating the same idea in different words within a paragraph
- Generic filler sentences that add no information
- Prioritizing style over substance
- Inspirational or motivational register unless the content genuinely calls for it
Conversation History Structure
For best results, construct a few-shot conversation using 2-4 of your actual
writing samples. For each sample:

Generate a short prompt (1-2 sentences) that could have been used to request
that piece. Example: "Write a blog post exploring whether VC fund economics
explain why startups need to aim for 100x returns."
Place the prompt as a user message and the actual writing sample as an
assistant message.
After these few-shot examples, add your actual request as the final user
message.

This teaches the model in-context that "the assistant" writes in your style.
Example conversation structure:
System: [Style profile + anti-slop instructions]

User: "Write a short essay exploring what motivates high-performing people
       and whether ambition is always positive."
Assistant: [Actual writing sample: "The energy to keep going"]

User: "Explain VC fund economics and what return multiples mean for
       startup founders."

Assistant: [Actual writing sample: "Lets start a VC fund and make money!"]

User: [YOUR ACTUAL REQUEST HERE]

Section C: Iterative Refinement
Style extraction is not a one-shot process. After generating your first piece
of styled text:

Compare side-by-side with an actual writing sample on a similar topic
Identify drift — where does the generated text feel "off"?
Update the style profile with more specific constraints
Add negative examples — if the model produces a pattern you dislike,
add it explicitly to the anti-patterns list

Common failure modes to watch for:

The model over-applies the most salient features (e.g., too many questions
as headers, too much bold)
The model captures surface patterns but misses deeper argumentative structure
The model adds false personality (e.g., forced self-deprecation, artificial
vulnerability)
The model defaults to LLM-typical transitions and connectives despite
instructions


Section D: Research Notes
This prompt design draws on several approaches from the literature:

ZeroStylus (2025): Hierarchical template extraction at sentence and
paragraph levels for long-text style transfer
Register Analysis (UMD, 2025): Using linguistic feature measurement
(word choice, sentence length, abstraction) rather than vague style labels
CAT-LLM (Tao et al., 2024): Text Style Definition modules analyzing
word-level and sentence-level features to create style-enhanced prompts
Few-shot conversation conditioning (Panickssery, 2025): Constructing
synthetic conversation histories where the assistant role demonstrates
the target style
Key empirical finding: Preserving original text structure in examples
matters more than description alone — flattened samples lose the voice
