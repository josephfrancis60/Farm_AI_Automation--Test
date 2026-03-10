from agents.langgraph_agent import get_agent
from services.logger_service import log_full_state
import logging

# Initialize agent
agent = get_agent()

def run_agent(user_input):
    try:
        # Configuration for stateful graph execution
        config = {"configurable": {"thread_id": "farm_user_1"}}
        
        # Invoke agent
        result = agent.invoke(
            {"messages": [("user", user_input)]},
            config=config
        )

        messages = result["messages"]
        human_input = user_input
        
        # Final message from the agent
        final_message = messages[-1]
        agent_output = final_message.content

        # Information for logs
        tool_calls = []
        token_usage = None
        
        for msg in messages:
            # Check for tool usage
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "id": tc.get("id"),
                        "name": tc["name"],
                        "args": tc["args"]
                    })
            
            # Extract token usage from the most detailed metadata
            meta = getattr(msg, "response_metadata", {})
            if "token_usage" in meta:
                token_usage = meta["token_usage"]

        # Log detailed info to logs/<date>.log
        log_full_state(
            human_input=human_input,
            agent_output=agent_output,
            tool_calls=tool_calls,
            tokens=token_usage
        )

        return agent_output

    except Exception as e:
        logging.error(f"Agent Error: {str(e)}")
        return f"An error occurred: {str(e)}"