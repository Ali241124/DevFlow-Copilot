# DevFlow Copilot — Known Limitations, Failure Modes & Future Roadmap

## 1. Known Limitations of the Local-First Stack

### 1.1 Local Model Context Windows & Compute Constraints
- **Hardware Dependency**: Local inference latency depends heavily on available RAM/VRAM. On CPU-only environments, generating a full specification with a 4B parameter model (`qwen3:4b`) takes approximately 30–90 seconds.
- **Context Length Truncation**: Small local models (e.g. `qwen2.5:1.5b`) typically operate with a 2,048–4,096 token context window. Ingesting massive 50-page RFPs or lengthy meeting transcripts without chunking can lead to context exhaustion.
- **Vision Resolution & Detail**: Lightweight local vision models (`moondream`) excel at high-contrast UI component identification (buttons, input fields, cards), but can misread dense, low-contrast text in blurry, compressed screenshots compared to large proprietary vision models.

### 1.2 Zero Paid API Trade-Offs
- **No Auto-Translation of Niche File Types**: Proprietary OCR services support raw hand-drawn sketches on whiteboards more reliably than lightweight local OCR engines, which require reasonable image contrast.
- **Local Model Quantization**: 4-bit quantized local models occasionally produce repetitive phrased sentences when temperature is set higher than 0.3; our system intentionally keeps temperature at `0.1 – 0.15` for deterministic structured generation.

---

## 2. Failure Modes & Automated Defenses

| Failure Mode | Root Cause | System Defense in DevFlow Copilot |
|---|---|---|
| **Hallucinated Third-Party APIs** | Model assumes common cloud services (e.g. AWS S3, Stripe, OAuth) when brief doesn't specify. | **Prompt Constraints + Anti-Hallucination Scoring**: Prompt v2 strictly forbids third-party inventions. `verify_evidence()` downgrades unverified claims to `needs_clarification`. |
| **Silent Assumption of Missing Rules** | Client brief does not specify auth or data retention. Model invents arbitrary rules. | **Strict Uncertainty Surfacing (`GEN-005`)**: Evaluator checks `should_identify_unknowns`. Missing information MUST be placed into `open_questions`. |
| **Invalid Schema / Extra JSON Keys** | Local LLM inserts conversational markdown or extra keys outside the schema. | **Pydantic v2 Strict Enforcement (`extra='forbid'`)**: Any invalid structure immediately fails validation and is returned with explicit line/column diagnostics rather than crashing silently. |
| **Prompt Injection via Client Brief** | Malicious user puts `Ignore previous instructions` inside uploaded text. | **Context Boundary Delimiters + Untrusted Data Protocol (`GEN-009`)**: Input is treated strictly as passive data inside isolated tags; instructions are not interpreted as commands. |
| **Premature Production Deployment** | Stakeholders assume AI output is production-ready. | **Mandatory Human-in-the-Loop Review Gate (`GEN-008`)**: All artifacts default to `draft` with visual warnings. Approval requires explicit reviewer action. |

---

## 3. Future Roadmap

1. **Local Semantic Retrieval (RAG)**: Integrate Sentence Transformers (`all-MiniLM-L6-v2`) with local FAISS vector search to allow referencing past company project specifications.
2. **Interactive Bounding-Box Annotation**: Allow human reviewers to draw click-and-drag bounding boxes on uploaded wireframes directly in the Streamlit UI to highlight specific regions for visual analysis.
3. **Multi-Model Ensembling**: Combine outputs from multiple open-source checkpoints (e.g. Qwen2.5-Coder for developer prompts and Llama-3.2 for user stories).
4. **Export Integration with Jira / GitHub Issues**: Add export format adapters that format approved user stories and acceptance criteria directly into CSV or JSON ready for one-click import into issue trackers.
