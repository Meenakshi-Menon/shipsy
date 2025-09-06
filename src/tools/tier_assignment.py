from typing import Optional, Dict, Any


def assign_company_tier(revenue_usd: Optional[float]) -> str:
    """
    Assign a company tier based on annual revenue from operations.
    
    Args:
        revenue_usd: Annual revenue from operations in USD
        
    Returns:
        Tier assignment string
    """
    if revenue_usd is None:
        return "Unknown"
    
    # Tier definitions based on annual revenue from operations
    if revenue_usd >= 1_000_000_000:  # $1 billion or more
        return "Super Platinum"
    elif revenue_usd >= 500_000_000:  # $500 million to $1 billion
        return "Platinum"
    elif revenue_usd >= 100_000_000:   # $100 million to $500 million
        return "Diamond"
    else:  # Below $100 million
        return "Gold"


def format_revenue_display(revenue_usd: Optional[float]) -> str:
    """
    Format revenue for display purposes.
    
    Args:
        revenue_usd: Revenue in USD
        
    Returns:
        Formatted revenue string
    """
    if revenue_usd is None:
        return "Not Available"
    
    if revenue_usd >= 1_000_000_000:
        return f"${revenue_usd / 1_000_000_000:.2f}B"
    elif revenue_usd >= 1_000_000:
        return f"${revenue_usd / 1_000_000:.2f}M"
    elif revenue_usd >= 1_000:
        return f"${revenue_usd / 1_000:.2f}K"
    else:
        return f"${revenue_usd:,.2f}"


def get_tier_description(tier: str) -> str:
    """
    Get a description of what each tier represents.
    
    Args:
        tier: Tier name
        
    Returns:
        Description of the tier
    """
    descriptions = {
        "Super Platinum": "Annual revenue from operations > $1Bn",
        "Platinum": "Annual revenue from operations $500Mn to $1Bn",
        "Diamond": "Annual revenue from operations $100Mn to $500Mn",
        "Gold": "Annual revenue from operations below $100Mn",
        "Unknown": "Revenue information not available"
    }
    
    return descriptions.get(tier, "Unknown tier")


def analyze_company_tier(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete tier analysis for a company.
    
    Args:
        company_data: Dictionary containing company information including revenue
        
    Returns:
        Dictionary with tier analysis results
    """
    revenue_usd = company_data.get("estimated_revenue_usd")
    tier = assign_company_tier(revenue_usd)
    
    return {
        "company_name": company_data.get("company_name", "Unknown"),
        "company_domain": company_data.get("company_domain", ""),
        "estimated_revenue_usd": revenue_usd,
        "revenue_display": format_revenue_display(revenue_usd),
        "tier": tier,
        "tier_description": get_tier_description(tier),
        "citation": company_data.get("citation", "")
    }


if __name__ == "__main__":
    # Test the tier assignment function
    test_revenues = [
        None,  # No data
        50_000_000,   # Gold
        150_000_000,  # Diamond
        750_000_000,  # Platinum
        2_500_000_000  # Super Platinum
    ]
    
    print("Testing Tier Assignment Function")
    print("=" * 50)
    
    for revenue in test_revenues:
        tier = assign_company_tier(revenue)
        display = format_revenue_display(revenue)
        description = get_tier_description(tier)
        
        print(f"Revenue: {display}")
        print(f"Tier: {tier}")
        print(f"Description: {description}")
        print("-" * 30)
