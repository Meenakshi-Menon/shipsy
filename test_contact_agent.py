#!/usr/bin/env python3
"""
Test script for contact enrichment agent
"""

import sys
import logging
from src.processors.contact_csv_processor import ContactCSVProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_csv_processing():
    """Test CSV processing functionality."""
    print("Testing CSV processing...")
    
    processor = ContactCSVProcessor()
    
    # Test reading the sample CSV
    try:
        contacts = processor.read_contacts_csv("sample_contacts.csv")
        print(f"Successfully read {len(contacts)} contacts:")
        for i, contact in enumerate(contacts, 1):
            print(f"  {i}. {contact['contact_name']} at {contact['company_name']}")
        
        return True
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return False


def test_contact_info_structure():
    """Test ContactInfo data structure."""
    print("\nTesting ContactInfo structure...")
    
    from src.agents.contact_agent import ContactInfo
    
    # Create a test contact
    test_contact = ContactInfo(
        contact_name="John Smith",
        company_name="Microsoft",
        linkedin_url="https://linkedin.com/in/johnsmith",
        current_job_title="Software Engineer",
        work_email="john.smith@microsoft.com",
        citation_source="LinkedIn Profile"
    )
    
    print(f"Test contact created:")
    print(f"  Name: {test_contact.contact_name}")
    print(f"  Company: {test_contact.company_name}")
    print(f"  LinkedIn: {test_contact.linkedin_url}")
    print(f"  Title: {test_contact.current_job_title}")
    print(f"  Email: {test_contact.work_email}")
    print(f"  Source: {test_contact.citation_source}")
    
    return True


def test_email_generation():
    """Test email generation logic."""
    print("\nTesting email generation...")
    
    from src.agents.contact_agent import ContactEnrichmentAgent
    
    agent = ContactEnrichmentAgent()
    
    # Test cases
    test_cases = [
        ("John Smith", "microsoft.com"),
        ("Sarah Johnson", "google.com"),
        ("Michael Brown", "apple.com"),
        ("Emily Davis", "amazon.com"),
        ("David Wilson", "meta.com")
    ]
    
    for name, domain in test_cases:
        email = agent.generate_work_email(name, domain)
        print(f"  {name} @ {domain} -> {email}")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("CONTACT ENRICHMENT AGENT - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("CSV Processing", test_csv_processing),
        ("ContactInfo Structure", test_contact_info_structure),
        ("Email Generation", test_email_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print(f"{'=' * 60}")
    
    if passed == total:
        print("🎉 All tests passed! The contact enrichment agent is ready to use.")
        print("\nTo run the full enrichment process, you'll need to:")
        print("1. Set up your API keys in a .env file")
        print("2. Run: uv run python contact_enrichment.py sample_contacts.csv enriched_contacts.csv")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)
