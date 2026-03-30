import os
import uuid
from agents.langgraph_agent import get_agent, run_agent_with_logging
from dotenv import load_dotenv

def test_agent_logging():
    print("--- Testing Agent Logging with Tool Calls ---")
    load_dotenv()
    
    agent = get_agent()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # Use a query that forces a tool call
    user_input = "What crops are in my farm and what is the latest weather?"
    print(f"User: {user_input}")
    
    response = run_agent_with_logging(agent, config, user_input)
    print(f"Agent Reply: {response['messages'][-1].content}")
    
    # Check the log file for today
    today_str = os.popen("date /t").read().strip().split(' ')[-1] # Quick way to get date or just use datetime
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = f"logs/{today}.log"
    
    if os.path.exists(log_file):
        print(f"\n[LOG FILE CONTENT: {log_file}]")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Print the last 50 lines to see the interaction
            for line in lines[-50:]:
                print(line.strip())
    else:
        print(f"Log file {log_file} not found!")

if __name__ == "__main__":
    test_agent_logging()
