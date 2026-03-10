from agents.langgraph_agent import get_agent
from services.logger_service import log_full_state
# import logging

# Initialize agent
agent = get_agent()

def run_agent(user_input):
    try:
        # Configuration for stateful graph execution
        config = {"configurable": {"thread_id": "farm_user_1"}}
        
        from datetime import datetime
        now = datetime.now()
        context = f"[Context: Current time is {now.strftime('%A, %Y-%m-%d %H:%M:%S')}]\n"
        full_input = context + user_input

        # Invoke agent
        result = agent.invoke(
            {"messages": [("user", full_input)]},
            config=config
        )

        messages = result["messages"]
        human_input = user_input
        
        # Final message from the agent
        final_message = messages[-1]
        agent_output = final_message.content

        # Information for logs
        tool_calls = []
        tool_outputs = {}   # maps tool_call_id -> content string
        token_usage = None
        
        for msg in messages:
            # Capture tool call requests (from AIMessage)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append({
                        "id": tc.get("id"),
                        "name": tc["name"],
                        "args": tc["args"]
                    })
            
            # Capture tool responses (ToolMessage nodes in the graph)
            if hasattr(msg, "tool_call_id") and hasattr(msg, "content"):
                tool_outputs[msg.tool_call_id] = msg.content

            # Extract token usage from the most detailed metadata
            meta = getattr(msg, "response_metadata", {})
            if "token_usage" in meta:
                token_usage = meta["token_usage"]

        # Log detailed info to logs/<date>.log
        log_full_state(
            human_input=human_input,
            agent_output=agent_output,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
            tokens=token_usage
        )

        return agent_output

    except Exception as e:
        error_str = str(e)
        logger = __import__('logging').getLogger("FarmAIAgent")

        # Log the full technical error to the log file (not visible in UI)
        logger.error(f"AGENT ERROR (full details): {error_str}")

        # Friendly message for rate limit / API quota errors
        if "rate_limit_exceeded" in error_str or "429" in error_str:
            return "Sorry, I'm a bit overloaded right now. Please try again in a few minutes! ☕"

        # Generic fallback for any other error
        return "Hmm, something went wrong on my end. Please try again shortly."