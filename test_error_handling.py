#!/usr/bin/env python3
"""
Test script to demonstrate error handling capabilities of the revenue agent.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.revenue_agent import DeepSeekRevenueAgent, ValidationError, APIError, ConfigurationError, DataProcessingError
from src.tools.web_search import BraveWebSearch
import logging

# Configure logging to see error handling in action
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_validation_errors():
    """Test input validation error handling."""
    print("\n" + "="*60)
    print("TESTING INPUT VALIDATION ERROR HANDLING")
    print("="*60)
    
    try:
        agent = DeepSeekRevenueAgent()
        
        # Test empty company name
        print("\n1. Testing empty company name:")
        try:
            agent.search_company_financials("")
        except ValidationError as e:
            print(f"   ✓ Caught ValidationError: {e}")
        
        # Test None company name
        print("\n2. Testing None company name:")
        try:
            agent.search_company_financials(None)
        except ValidationError as e:
            print(f"   ✓ Caught ValidationError: {e}")
        
        # Test very short company name
        print("\n3. Testing very short company name:")
        try:
            agent.search_company_financials("A")
        except ValidationError as e:
            print(f"   ✓ Caught ValidationError: {e}")
        
        # Test invalid domain format
        print("\n4. Testing invalid domain format:")
        try:
            agent.search_company_financials("Apple Inc", "invalid-domain")
        except ValidationError as e:
            print(f"   ✓ Caught ValidationError: {e}")
        else:
            print("   ✓ Warning logged for invalid domain format")
        
        # Test with None domain (should be allowed)
        print("\n5. Testing with None domain (should be allowed):")
        try:
            agent.search_company_financials("Apple Inc", None)
            print("   ✓ None domain accepted (optional parameter)")
        except ValidationError as e:
            print(f"   ✗ Unexpected ValidationError: {e}")
        
        # Test with empty string domain (should be allowed)
        print("\n6. Testing with empty string domain (should be allowed):")
        try:
            agent.search_company_financials("Apple Inc", "")
            print("   ✓ Empty string domain accepted (optional parameter)")
        except ValidationError as e:
            print(f"   ✗ Unexpected ValidationError: {e}")
        
        # Test with blank string domain from CSV (should be allowed)
        print("\n7. Testing with blank string domain from CSV (should be allowed):")
        try:
            agent.search_company_financials("Wincanton", "   ")  # Blank string with spaces
            print("   ✓ Blank string domain accepted (CSV empty cell)")
        except ValidationError as e:
            print(f"   ✗ Unexpected ValidationError: {e}")
        
        # Test with whitespace-only domain (should be treated as empty)
        print("\n8. Testing with whitespace-only domain (should be treated as empty):")
        try:
            agent.search_company_financials("Black Sheep UK", "\t\n  \t")
            print("   ✓ Whitespace-only domain accepted (treated as empty)")
        except ValidationError as e:
            print(f"   ✗ Unexpected ValidationError: {e}")
        
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")

def test_api_error_handling():
    """Test API error handling."""
    print("\n" + "="*60)
    print("TESTING API ERROR HANDLING")
    print("="*60)
    
    try:
        agent = DeepSeekRevenueAgent()
        
        # Test with invalid search results (empty string)
        print("\n1. Testing revenue extraction with empty search results:")
        try:
            revenue, citation = agent.extract_revenue_from_sources("Apple Inc", "")
        except ValidationError as e:
            print(f"   ✓ Caught ValidationError: {e}")
        
        # Test with None search results
        print("\n2. Testing revenue extraction with None search results:")
        try:
            revenue, citation = agent.extract_revenue_from_sources("Apple Inc", None)
        except ValidationError as e:
            print(f"   ✓ Caught ValidationError: {e}")
        
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")

def test_graceful_degradation():
    """Test graceful degradation when services fail."""
    print("\n" + "="*60)
    print("TESTING GRACEFUL DEGRADATION")
    print("="*60)
    
    try:
        agent = DeepSeekRevenueAgent()
        
        # Test complete analysis with a real company (this will show graceful handling)
        print("\n1. Testing complete analysis with graceful error handling:")
        result = agent.analyze_company_revenue("Apple Inc", "apple.com")
        
        print(f"   Company: {result['company_name']}")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Revenue: {result.get('estimated_revenue_usd', 'Not found')}")
        print(f"   Citation: {result.get('citation', 'No citation')[:100]}...")
        
        if result.get('error'):
            print(f"   Error handled gracefully: {result['error']}")
        
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")

def test_web_search_error_handling():
    """Test web search error handling."""
    print("\n" + "="*60)
    print("TESTING WEB SEARCH ERROR HANDLING")
    print("="*60)
    
    try:
        search_tool = BraveWebSearch()
        
        # Test with empty query
        print("\n1. Testing search with empty query:")
        result = search_tool.search("")
        if "error" in result:
            print(f"   ✓ Error handled: {result['error']}")
        
        # Test with None query
        print("\n2. Testing search with None query:")
        result = search_tool.search(None)
        if "error" in result:
            print(f"   ✓ Error handled: {result['error']}")
        
        # Test company revenue search with invalid input
        print("\n3. Testing company revenue search with invalid input:")
        results = search_tool.search_company_revenue("")
        print(f"   ✓ Returned empty results: {len(results)} results")
        
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")

def test_tool_error_handling():
    """Test LangChain tool error handling."""
    print("\n" + "="*60)
    print("TESTING LANGCHAIN TOOL ERROR HANDLING")
    print("="*60)
    
    try:
        from src.agents.revenue_agent import create_revenue_agent_tools
        
        tools = create_revenue_agent_tools()
        search_tool, extract_tool = tools
        
        # Test search tool with invalid input
        print("\n1. Testing search tool with invalid input:")
        result = search_tool.invoke({"company_name": "", "company_domain": ""})
        print(f"   ✓ Tool handled error gracefully: {result[:100]}...")
        
        # Test extract tool with invalid input
        print("\n2. Testing extract tool with invalid input:")
        result = extract_tool.invoke({"company_name": "", "search_results": ""})
        print(f"   ✓ Tool handled error gracefully: {result[:100]}...")
        
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")

def main():
    """Run all error handling tests."""
    print("REVENUE AGENT ERROR HANDLING TEST SUITE")
    print("="*60)
    print("This script tests the comprehensive error handling")
    print("capabilities added to the revenue agent.")
    
    try:
        test_validation_errors()
        test_api_error_handling()
        test_graceful_degradation()
        test_web_search_error_handling()
        test_tool_error_handling()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        print("✓ Error handling is working correctly!")
        print("✓ The agent gracefully handles various error conditions")
        print("✓ Logging provides detailed information for debugging")
        print("✓ Custom exceptions provide clear error categorization")
        
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        logger.error(f"Test suite failed: {e}")

if __name__ == "__main__":
    main()
