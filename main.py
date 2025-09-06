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
