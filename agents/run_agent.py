from agents.langgraph_agent import get_agent
from services.logger_service import log_full_state
# import logging

# Initialize agent
agent = get_agent()

def run_agent(user_input):
    try:
        # Configuration for stateful graph execution
        thread_id = "farm_user_v2"
        if user_input.lower().strip() in ["reset", "reset chat", "clear history"]:
            # Logic to switch to a new thread effectively resetting history
            from datetime import datetime
            thread_id = f"farm_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return "Sir, I have recalibrated my memory cores. Our conversation history has been reset. How may I assist you?"

        config = {"configurable": {"thread_id": thread_id}}
        
        from datetime import datetime
        from alerts.alert_manager import get_active_alerts
        now = datetime.now()
        alerts_list = get_active_alerts()
        
        alerts_context = ""
        if alerts_list:
            alerts_context = "\n[Active Alerts Check]:\n"
            for i, a in enumerate(alerts_list[:5], start=1):
                alerts_context += f"{i}. {a['title']}: {a['message']} (Category: {a['category']})\n"
        
        context = f"[Context: Current time is {now.strftime('%A, %Y-%m-%d %H:%M:%S')}]\n{alerts_context}\n"
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
        from services.logger_service import get_logger
        logger = get_logger()

        # Log to standard daily file
        log_full_state(
            human_input=user_input,
            agent_output=f"LIMITATION: {error_str}",
            tool_calls=[], tool_outputs={},
            tokens={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "total_time": 0}
        )
        logger.error(f"AGENT ERROR: {error_str}")

        # Friendly message for rate limit / API quota errors
        if "rate_limit_exceeded" in error_str or "429" in error_str:
            return "Sir, I'm currently experiencing an overload in my communication processors. Please give me a moment to recalibrate and try again shortly."

        # Generic fallback for any other error
        return "I apologize, but I've encountered a system limitation. I'm attempting to resolve it now. Shall we try again in a moment?"