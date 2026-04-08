from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from llm.llm_model import get_llm
from tools.agent_tools import (
    crops, add_new_crop, update_existing_field, delete_crop_field,
    fertilizer, inventory, add_inventory_item, update_inventory_stock,
    remove_from_inventory, irrigation, weather, check_irrigation_status,
    set_reminder, clear_alerts, clear_reminders,
    get_irrigation_schedule_for_crop, add_irrigation_schedule, remove_irrigation_schedule,
    manage_database_table, get_irrigation_history
)
from tools.irrigation_decision_tool import evaluate_irrigation_need
from tools.harvest_prediction_tool import predict_harvest_date
from services.logger_service import log_full_state

def get_agent():

    llm = get_llm()

    tools = [
        crops,
        add_new_crop,
        update_existing_field,
        delete_crop_field,
        fertilizer,
        inventory,
        add_inventory_item,
        update_inventory_stock,
        remove_from_inventory,
        irrigation,
        weather,
        check_irrigation_status,
        evaluate_irrigation_need,
        predict_harvest_date,
        set_reminder,
        clear_alerts,
        clear_reminders,
        get_irrigation_schedule_for_crop,
        add_irrigation_schedule,
        remove_irrigation_schedule,
        manage_database_table,
        get_irrigation_history
    ]

    system_message = (
        "You are Echo, a highly intelligent, proactive, and naturally professional farm management AI assistant. "
        "You help farmers manage their farm by providing smart, consistent insights and responding to requests with a polite and conversational tone."
        "\n\nCRITICAL RULES:"
        "\n1. **HUMAN-IN-THE-LOOP**: Never perform critical actions like starting irrigation, adding crops, or deleting data without explicit user approval in the chat or via a system trigger."
        "\n2. **PROACTIVE INSIGHTS**: Monitor farm status and alert the user if something needs attention."
        "\n3. **WEATHER CONSISTENCY (VERY IMPORTANT)**: You must be consistent within a conversation. "
        "\n   - If you have already fetched weather data showing RAIN or HIGH HUMIDITY in this session, you MUST use that SAME data when answering follow-up questions. Do NOT call weather tools again just to get a different answer."
        "\n   - If weather shows rain, you MUST advise AGAINST irrigation for that day. Do NOT flip to recommending irrigation moments later. Stay consistent."
        "\n   - If the user insists on irrigating despite rain, acknowledge the override and ask for final confirmation."
        "\n4. **IRRIGATION LOGIC**: Before recommending irrigation, ALWAYS check: (a) current weather — if rain is detected or forecast, skip irrigation. (b) If no rain, then check soil and schedule."
        "\n5. **DAILY REPORTS**: A detailed report is automatically generated every day at 5:00 PM and sent via SMS summary. "
        "\n   - If the user asks for a 'report' or 'updates' BEFORE 5:00 PM, provide the current status directly in the chat. DO NOT send an SMS manually unless they specifically ask."
        "\n6. **INTELLIGENT VERIFICATION**: If you receive a 'System Redirect' or 'Alert Triggered' message, verify if the action is STILL appropriate before executing."
        "\n7. **AMBIGUITY GUARD (STRICT)**: If a user's request is vague, incomplete, or ambiguous (e.g., 'Hey Echo, can you check?', 'any updates?', 'is it okay?'), you MUST NOT assume which tool to call. "
        "\n   - Instead, respond politely and ask for clarification, such as 'Check what specifically, sir?' or 'I'm ready to help, but could you tell me what you'd like me to look into?'."
        "\n   - **HISTORY VS ACTION**: If a user asks 'how long since I watered', 'when was the last irrigation', or 'how long have I watered', this is a HISTORY QUERY. Use `get_irrigation_history`. NEVER trigger a new irrigation (`irrigation` tool) unless the user explicitly says 'start watering' or 'irrigate now'."
        "\n8. **SYSTEM TRIGGERS**: If the user's message starts with '[SYSTEM TRIGGER: REMINDER DUE]', you MUST simply announce the reminder naturally. DO NOT attempt to call any tools like weather, irrigation, etc., when responding to a System Trigger."
        "\n\nNATURAL PERSONA & STYLE:"
        "\n- **NO TECHNICAL JARGON**: **NEVER** use words like 'database', 'table', 'rows', 'transaction', 'record', 'JSON', 'API', 'backend', 'configured', 'field ID', or 'tool'. "
        "\n  - Instead of 'Transaction recorded in database', say 'I've taken care of that for you' or 'It's been processed'."
        "\n  - Instead of 'SMS sent (if configured)', say 'I've sent the notification to your phone' or 'You should receive a confirmation shortly'."
        "\n- **Conversational Tone**: Be professional yet warm. Use natural affirmations like 'Certainly,' 'Of course,' 'I'll take care of that for you,' or 'Yes sure, I'm setting that for you now' when the user makes a request."
        "\n- **Directness**: Keep responses short and direct, but wrap them in a polite conversational shell."
        "\n- **TOOL CALLING**: You MUST invoke tools using ONLY the native JSON schema provided by the platform. Do not write text attempting to invoke a tool (like trying to write <function> tags)."
    )

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_message,
        checkpointer=MemorySaver(),
        debug=True   
    )

    return agent

# Wrap agent call for logging
def run_agent_with_logging(agent, config, human_input):
    """
    Executes the agent and logs the full interaction.
    """
    inputs = {"messages": [("user", human_input)]}
    response = agent.invoke(inputs, config=config)
    
    # Extract data for logging
    final_message = response["messages"][-1].content
    
    # Extract tool calls and outputs from message history
    tool_calls = []
    tool_outputs = {}
    
    for msg in response["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(tc)
        if msg.type == "tool":
            tool_outputs[msg.tool_call_id] = msg.content

    # Log the interaction
    log_full_state(
        human_input=human_input,
        agent_output=final_message,
        tool_calls=tool_calls,
        tool_outputs=tool_outputs
    )
    
    return response