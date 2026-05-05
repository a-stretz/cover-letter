"""
Scout model routing — aligned with JADE model routing standard.

  orchestration  Haiku 4.5   fast classification, filter passes
  reasoning      Sonnet 4.6  job scoring, nuanced analysis
  heavy          Opus 4.6    reserved for future deep-dive synthesis
"""

MODELS: dict[str, str] = {
    "orchestration": "claude-haiku-4-5-20251001",
    "reasoning":     "claude-sonnet-4-6",
    "heavy":         "claude-opus-4-6",
}
