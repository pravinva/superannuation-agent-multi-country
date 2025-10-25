# cost_utils.py
"""
Token tracking and cost calculation utilities
Based on Databricks Foundation Model API pricing
"""

# Databricks Pricing (per 1M tokens)
PRICING = {
    'claude-opus-4-1': {
        'input': 15.0,   # $15 per 1M input tokens
        'output': 75.0   # $75 per 1M output tokens
    },
    'claude-sonnet-4': {
        'input': 3.0,    # $3 per 1M input tokens
        'output': 15.0   # $15 per 1M output tokens
    }
}


def calculate_token_cost(input_tokens, output_tokens, model_name):
    """
    Calculate cost for a single LLM call
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_name: Model identifier (opus-4-1 or sonnet-4)
    
    Returns:
        Cost in USD
    """
    # Normalize model name
    if 'opus' in model_name.lower():
        model_key = 'claude-opus-4-1'
    elif 'sonnet' in model_name.lower():
        model_key = 'claude-sonnet-4'
    else:
        # Default to Opus pricing
        model_key = 'claude-opus-4-1'
    
    pricing = PRICING[model_key]
    
    input_cost = (input_tokens / 1_000_000) * pricing['input']
    output_cost = (output_tokens / 1_000_000) * pricing['output']
    
    return input_cost + output_cost


def calculate_query_costs(token_breakdown, main_model='opus-4-1', judge_model='sonnet-4'):
    """
    Calculate total costs for a query with breakdown
    
    Args:
        token_breakdown: Dict with structure:
            {
                'planning': {'input': int, 'output': int},
                'synthesis': {'input': int, 'output': int},
                'validation': {'input': int, 'output': int}
            }
        main_model: Model used for planning and synthesis
        judge_model: Model used for validation
    
    Returns:
        Dict with cost breakdown
    """
    costs = {
        'planning': 0.0,
        'synthesis': 0.0,
        'validation': 0.0,
        'total': 0.0
    }
    
    # Planning cost (main model)
    costs['planning'] = calculate_token_cost(
        token_breakdown['planning']['input'],
        token_breakdown['planning']['output'],
        main_model
    )
    
    # Synthesis cost (main model)
    costs['synthesis'] = calculate_token_cost(
        token_breakdown['synthesis']['input'],
        token_breakdown['synthesis']['output'],
        main_model
    )
    
    # Validation cost (judge model)
    costs['validation'] = calculate_token_cost(
        token_breakdown['validation']['input'],
        token_breakdown['validation']['output'],
        judge_model
    )
    
    costs['total'] = costs['planning'] + costs['synthesis'] + costs['validation']
    
    return costs


def calculate_projected_costs(queries_per_minute, avg_cost_per_query):
    """
    Calculate projected costs at various time scales
    
    Args:
        queries_per_minute: Expected query rate
        avg_cost_per_query: Average cost per query (from historical data)
    
    Returns:
        Dict with projections
    """
    queries_per_hour = queries_per_minute * 60
    queries_per_day = queries_per_hour * 24
    queries_per_month = queries_per_day * 30
    queries_per_year = queries_per_month * 12
    
    return {
        'hourly': {
            'queries': queries_per_hour,
            'cost': queries_per_hour * avg_cost_per_query
        },
        'daily': {
            'queries': queries_per_day,
            'cost': queries_per_day * avg_cost_per_query
        },
        'monthly': {
            'queries': queries_per_month,
            'cost': queries_per_month * avg_cost_per_query
        },
        'yearly': {
            'queries': queries_per_year,
            'cost': queries_per_year * avg_cost_per_query
        }
    }


def format_token_count(tokens):
    """Format token count with commas"""
    return f"{int(tokens):,}"


def format_cost(cost):
    """Format cost in USD"""
    return f"${cost:.4f}"


def get_pricing_info():
    """Get pricing information as formatted string"""
    return """
**Databricks Foundation Model API Pricing:**

**Claude Opus 4.1** (Planning + Synthesis):
- Input: $15 per 1M tokens
- Output: $75 per 1M tokens

**Claude Sonnet 4** (Validation):
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

[Databricks GenAI Pricing Calculator](https://www.databricks.com/product/pricing/genai-pricing-calculator)
"""


# Example usage
if __name__ == "__main__":
    # Example token breakdown
    tokens = {
        'planning': {'input': 450, 'output': 400},
        'synthesis': {'input': 2500, 'output': 700},
        'validation': {'input': 500, 'output': 100}
    }
    
    costs = calculate_query_costs(tokens)
    
    print("Token Breakdown:")
    print(f"  Planning: {tokens['planning']['input']} in + {tokens['planning']['output']} out")
    print(f"  Synthesis: {tokens['synthesis']['input']} in + {tokens['synthesis']['output']} out")
    print(f"  Validation: {tokens['validation']['input']} in + {tokens['validation']['output']} out")
    print()
    print("Cost Breakdown:")
    print(f"  Planning: ${costs['planning']:.6f}")
    print(f"  Synthesis: ${costs['synthesis']:.6f}")
    print(f"  Validation: ${costs['validation']:.6f}")
    print(f"  TOTAL: ${costs['total']:.6f}")
    print()
    
    # Projected costs at 0.1 queries/min
    projected = calculate_projected_costs(0.1, costs['total'])
    print("Projected Costs (0.1 queries/min):")
    print(f"  Hourly: ${projected['hourly']['cost']:.2f} ({projected['hourly']['queries']:.0f} queries)")
    print(f"  Daily: ${projected['daily']['cost']:.2f} ({projected['daily']['queries']:.0f} queries)")
    print(f"  Monthly: ${projected['monthly']['cost']:.2f} ({projected['monthly']['queries']:.0f} queries)")
    print(f"  Yearly: ${projected['yearly']['cost']:.2f} ({projected['yearly']['queries']:.0f} queries)")
