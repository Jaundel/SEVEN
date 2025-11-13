# ============================================================
#  File: main.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Command-line interface entry point and workflow scaffold.
#  Author(s): Team SEVEN
#  Date: 2025-11-07
# ============================================================
"""Entry point module for the SEVEN energy-aware CLI router."""


from router import route_prompt

def main():
    print("🌿 SEVEN CLI (Energy-Aware Hybrid Assistant)")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break
        try:
            result = route_prompt(user_input)
            print(f"\nModel: {result.model}")
            print(f"Response:\n{result.text}\n")
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    main()
