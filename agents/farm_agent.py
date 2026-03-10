from agents.langgraph_agent import get_agent

class FarmAgent:
    def __init__(self):
        self.agent = get_agent()
        self.config = {"configurable": {"thread_id": "farm_user_1"}}

    def ask(self, user_input):
        try:
            # Use LangGraph agent for processing
            result = self.agent.invoke(
                {"messages": [("user", user_input)]},
                config=self.config
            )
            # The last message in the state is the agent's response
            return result["messages"][-1].content
        except Exception as e:
            return f"An error occurred: {str(e)}"

def run_agent(user_input):
    agent = FarmAgent()
    return agent.ask(user_input)