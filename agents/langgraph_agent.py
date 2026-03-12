from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from llm.llm_model import get_llm
from tools.agent_tools import (
    crops, add_new_crop, update_existing_field, delete_crop_field,
    fertilizer, inventory, add_inventory_item, update_inventory_stock,
    remove_from_inventory, irrigation, weather, check_irrigation_status
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
        predict_harvest_date
    ]

    system_message = (
        "You are Sam, a friendly and proactive farm assistant. "
        "You help farmers manage their farm by providing proactive insights and responding to requests."
        "\n\nCRITICAL RULES:"
        "\n1. **HUMAN-IN-THE-LOOP**: Never perform critical actions like starting irrigation, adding crops, or deleting data without explicit user approval in the chat or via a system trigger (like the 'Trigger Action' button in the UI)."
        "\n2. **PROACTIVE INSIGHTS**: You should monitor farm status and alert the user if something needs attention (e.g., 'Field 2 needs water'). Ask for permission before taking action (e.g., 'Should I start the irrigation for you?')."
        "\n3. **INTELLIGENT VERIFICATION**: If you receive a 'System Redirect' or 'Alert Triggered' message, this signals a user's intent to follow a previous recommendation. However, you MUST still use your tools (like 'check_irrigation_status' or 'evaluate_irrigation_need') to verify if the action is STILL appropriate at this exact moment. If conditions have changed (e.g., it was recently watered), explain this to the user instead of blindly executing."
        "\n\nGENERAL STYLE:"
        "\n- Greet users warmly. Speak casually, like a friend."
        "\n- Only use tools when relevant. Do not over-explain."
        "\n- Use 'evaluate_irrigation_need' to identify needs, but ASK for permission before calling the 'irrigation' (Sprinkler) tool."
        "\n- For FERTILIZER, the tool now returns raw data. Use your knowledge to recommend specific fertilizers based on the soil and area provided."
        "\n- Keep responses short and friendly."
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
    
    # Log the interaction
    log_full_state(
        human_input=human_input,
        agent_output=final_message,
        # In a real scenario, we'd extract tool calls/outputs from the message history
        # For simplicity in this implementation, we focus on the final output
    )
    
    return response