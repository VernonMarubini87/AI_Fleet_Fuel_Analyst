"""
Thin wrapper around the Anthropic API. Claude is only ever given validated,
pre-computed evidence JSON and asked to interpret/narrate it — it is never
asked to calculate a number itself. If no API key is configured, callers
should fall back to the deterministic report generator (see reporting/).
"""
import os
import json

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


class ClaudeClient:
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.enabled = bool(self.api_key) and _ANTHROPIC_AVAILABLE
        if self.enabled:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def interpret(self, system_prompt: str, evidence: dict, question: str = None, max_tokens: int = 1000) -> str:
        if not self.enabled:
            return "[Claude API not configured — showing evidence only. See deterministic report for narrative.]"

        user_content = f"Evidence (validated, pre-calculated — do not recompute):\n{json.dumps(evidence, indent=2, default=str)}"
        if question:
            user_content += f"\n\nQuestion: {question}"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text"))
