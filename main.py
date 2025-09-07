'''
#!/usr/bin/env python3
"""
Main entry point for the LangGraph Agent Development Project.
"""

from src.agents.basic_agent import run_agent


def main():
    """Main function demonstrating the LangGraph agent."""
    print("🤖 LangGraph Agent Development Project")
    print("=" * 50)
    print("This is a basic example of a LangGraph agent with tools.")
    print("Make sure to set your OPENAI_API_KEY in a .env file first!")
    print()
    
    # Example queries
    test_queries = [
        "What is 15 * 8 + 23?",
        "What's the weather like in New York?",
        "Hello, how are you?"
    ]
    
    for query in test_queries:
        print(f"User: {query}")
        response = run_agent(query)
        print(f"Agent: {response}")
        print("-" * 30)


if __name__ == "__main__":
    main()
'''

#!/usr/bin/env python3
"""
Main entry point for the project.
Supports both:
1. LangGraph Agent Demo
2. Shipsy Assignment Excel Automation
"""

from src.agents.basic_agent import run_agent
from src.processors.excel_company_processor import ExcelCompanyProcessor

def run_demo():
    """Run the LangGraph agent demo."""
    print("🤖 LangGraph Agent Development Project")
    print("=" * 50)
    print("This is a basic example of a LangGraph agent with tools.")
    print("Make sure to set your OPENAI_API_KEY in a .env file first!\n")
    
    test_queries = [
        "What is 15 * 8 + 23?",
        "What's the weather like in New York?",
        "Hello, how are you?"
    ]
    
    for query in test_queries:
        print(f"User: {query}")
        response = run_agent(query)
        print(f"Agent: {response}")
        print("-" * 30)

def run_excel_automation():
    """Run the Shipsy Excel automation."""
    print("\n🚀 Starting Shipsy Assignment automation")
    print("=" * 50)

    processor = ExcelCompanyProcessor("Shipsy Assignment.xlsx")

    # Part A: Companies
    print("\n📊 Processing Companies...")
    processor.process_companies(
        input_sheet="Company",
        output_sheet="Company Results"
    )
    print("✅ Companies processed and written to 'Company Results' sheet.")


    # Part B: Contacts
    print("\n📇 Processing Contacts...")
    processor.process_contacts(
        input_sheet="Contacts",
        output_sheet="Contact Results"
    )
    print("✅ Contacts processed and written to 'Contact Results' sheet.")

    print("\n🎉 Automation finished successfully!")

if __name__ == "__main__":
    # 👉 Change this to choose which part to run
    # run_demo()
    run_excel_automation()
