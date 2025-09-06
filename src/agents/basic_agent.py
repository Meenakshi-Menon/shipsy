from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from src.config.settings import Config


class AgentState:
    """State for the agent graph."""
    messages: List[Any]


def create_agent_graph():
    """Create a LangGraph agent with basic tools."""
    
    # Initialize the LLM
    llm = ChatOpenAI(
        model=Config.AGENT_MODEL,
        temperature=Config.AGENT_TEMPERATURE,
        max_tokens=Config.AGENT_MAX_TOKENS,
        api_key=Config.OPENAI_API_KEY
    )
    
    # Define tools
    @tool
    def calculate(expression: str) -> str:
        """Calculate a mathematical expression safely."""
        try:
            # Simple evaluation for basic math operations
            allowed_chars = set('0123456789+-*/().')
            if all(c in allowed_chars or c.isspace() for c in expression):
                result = eval(expression)
                return f"The result of {expression} is {result}"
            else:
                return "Error: Invalid characters in expression"
        except Exception as e:
            return f"Error calculating {expression}: {str(e)}"
    
    @tool
    def get_weather(city: str) -> str:
        """Get weather information for a city (mock implementation)."""
        # This is a mock implementation - in a real scenario, you'd call a weather API
        weather_data = {
            "New York": "Sunny, 72°F",
            "London": "Cloudy, 55°F",
            "Tokyo": "Rainy, 68°F",
            "Paris": "Partly cloudy, 65°F"
        }
        return weather_data.get(city, f"Weather data not available for {city}")
    
    # Bind tools to LLM
    tools = [calculate, get_weather]
    llm_with_tools = llm.bind_tools(tools)
    
    # Create tool node
    tool_node = ToolNode(tools)
    
    def call_model(state: AgentState) -> Dict[str, Any]:
        """Call the model with the current state."""
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    
    def should_continue(state: AgentState) -> str:
        """Determine whether to continue with tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the LLM makes a tool call, then we route to the "tools" node
        if last_message.tool_calls:
            return "tools"
        # Otherwise, we stop
        return "end"
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    app = workflow.compile()
    
    return app


def run_agent(user_input: str) -> str:
    """Run the agent with user input and return the response."""
    try:
        Config.validate()
        
        # Create the agent graph
        agent = create_agent_graph()
        
        # Run the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=user_input)]
        })
        
        # Extract the final response
        final_message = result["messages"][-1]
        return final_message.content
        
    except Exception as e:
        return f"Error running agent: {str(e)}"


if __name__ == "__main__":
    # Example usage
    print("LangGraph Agent Example")
    print("=" * 50)
    
    # Test the agent
    test_queries = [
        "What is 15 * 8 + 23?",
        "What's the weather like in New York?",
        "Hello, how are you?"
    ]
    
    for query in test_queries:
        print(f"\nUser: {query}")
        response = run_agent(query)
        print(f"Agent: {response}")
        print("-" * 30)
