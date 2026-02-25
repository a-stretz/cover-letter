"""
Model Configuration and Cost Tracking
Tiered model routing for cost optimization
"""

# Model routing configuration
MODEL_CONFIG = {
    "screening": "claude-haiku-4-5-20251001",           # Fast, cheap screening
    "analysis": "claude-sonnet-4-5-20250929",           # Nuanced job analysis
    "cover_letter_standard": "claude-sonnet-4-5-20250929",  # Standard cover letters
    "cover_letter_priority": "claude-opus-4-5-20250915",    # Priority targets (8.5+ score)
    "message": "claude-sonnet-4-5-20250929",            # Follow-up messages
}

# Cost per million tokens (as of 2025)
MODEL_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-opus-4-5-20250915": {"input": 15.00, "output": 75.00},
    # Fallbacks for older model names
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
}

# Priority threshold for Opus upgrade
PRIORITY_SCORE_THRESHOLD = 8.5


def get_model(task: str) -> str:
    """Get the appropriate model for a task."""
    return MODEL_CONFIG.get(task, MODEL_CONFIG["analysis"])


def calculate_cost(model: str, input_tokens: int, output_tokens: int,
                   cache_read_tokens: int = 0, cache_creation_tokens: int = 0) -> dict:
    """
    Calculate the cost of an API call.

    Returns dict with:
        - input_cost: Cost for input tokens
        - output_cost: Cost for output tokens
        - total_cost: Total cost
        - cache_savings: Estimated savings from cache hits (90% savings on cached tokens)
    """
    costs = MODEL_COSTS.get(model, {"input": 3.00, "output": 15.00})

    # Regular input cost (excluding cached reads which are 90% cheaper)
    regular_input = input_tokens - cache_read_tokens
    input_cost = (regular_input / 1_000_000) * costs["input"]

    # Cache read cost (10% of normal input cost)
    cache_read_cost = (cache_read_tokens / 1_000_000) * costs["input"] * 0.1

    # Cache creation cost (25% premium on first write)
    cache_creation_cost = (cache_creation_tokens / 1_000_000) * costs["input"] * 1.25

    # Output cost
    output_cost = (output_tokens / 1_000_000) * costs["output"]

    # Total
    total_cost = input_cost + cache_read_cost + cache_creation_cost + output_cost

    # Savings from cache (what we would have paid without cache)
    cache_savings = (cache_read_tokens / 1_000_000) * costs["input"] * 0.9

    return {
        "input_cost": input_cost + cache_read_cost + cache_creation_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "cache_savings": cache_savings,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
    }


def log_api_cost(model: str, usage, task_name: str = "API Call") -> dict:
    """
    Log and return cost info from an API response.

    Args:
        model: Model name used
        usage: response.usage object from Anthropic API
        task_name: Human-readable task name for logging

    Returns:
        Dict with model, tokens, and cost info
    """
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    cache_read = getattr(usage, 'cache_read_input_tokens', 0) or 0
    cache_creation = getattr(usage, 'cache_creation_input_tokens', 0) or 0

    cost_info = calculate_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_creation
    )

    # Console logging
    print(f"\n{'='*50}")
    print(f"  {task_name}")
    print(f"  Model: {model}")
    print(f"  Tokens: {input_tokens} in / {output_tokens} out")
    if cache_read > 0 or cache_creation > 0:
        print(f"  Cache: {cache_read} read / {cache_creation} created")
        print(f"  Cache Savings: ${cost_info['cache_savings']:.4f}")
    print(f"  Cost: ${cost_info['total_cost']:.4f}")
    print(f"{'='*50}\n")

    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read,
        "cache_creation_tokens": cache_creation,
        "estimated_cost": round(cost_info['total_cost'], 6),
        "cache_savings": round(cost_info['cache_savings'], 6),
    }


def format_cost_for_ui(cost_info: dict) -> str:
    """Format cost info for display in UI."""
    model = cost_info.get('model', 'Unknown')
    cost = cost_info.get('estimated_cost', 0)

    # Shorten model name for display
    if 'haiku' in model.lower():
        model_display = 'Haiku'
    elif 'opus' in model.lower():
        model_display = 'Opus'
    elif 'sonnet' in model.lower():
        model_display = 'Sonnet'
    else:
        model_display = model.split('-')[0].title()

    return f"{model_display} (${cost:.4f})"
