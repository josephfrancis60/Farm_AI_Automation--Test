from agents.farm_agent import FarmAgent

def main():
    agent = FarmAgent()
    
    print("Farm AI Assistant 🌱")
    print("Type your question (or type 'exit' to quit)")
    print("-" * 30)

    while True:
        user_input = input("\nUser: ")

        if user_input.lower() == "exit":
            print("Goodbye! 👋")
            break

        response = agent.ask(user_input)
        print(f"Agent: {response}")

if __name__ == "__main__":
    main()