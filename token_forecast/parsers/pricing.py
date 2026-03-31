# Per-token pricing in USD (per 1M tokens)
# Updated March 2025 from official provider pricing pages
MODEL_PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    # Anthropic
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-3-5-20241022": {"input": 0.80, "output": 4.00},
    # Aliases
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
}

# Provider detection from model name
PROVIDER_MAP: dict[str, str] = {
    "gpt": "openai",
    "o1": "openai",
    "claude": "anthropic",
}


def detect_provider(model: str) -> str:
    model_lower = model.lower()
    for prefix, provider in PROVIDER_MAP.items():
        if prefix in model_lower:
            return provider
    return "unknown"


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model) or MODEL_PRICING.get(model.lower())
    if not pricing:
        # Try partial match
        model_lower = model.lower()
        for key, val in MODEL_PRICING.items():
            if key in model_lower or model_lower in key:
                pricing = val
                break
    if not pricing:
        # Fallback: average pricing
        pricing = {"input": 2.50, "output": 10.00}
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
