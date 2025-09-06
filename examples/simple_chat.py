#!/usr/bin/env python3
"""
Simple example script to demonstrate the LangGraph agent.
"""

from src.agents.basic_agent import run_agent


def main():
    """Main function to run the agent example."""
    print("🤖 LangGraph Agent Development Project")
    print("=" * 50)
    print("This is a basic example of a LangGraph agent with tools.")
    print("Make sure to set your OPENAI_API_KEY in a .env file first!")
    print()
    
    # Interactive mode
    print("Enter your questions (type 'quit' to exit):")
    print("-" * 30)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if not user_input:
                continue
            
            print("Agent: ", end="")
            response = run_agent(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
