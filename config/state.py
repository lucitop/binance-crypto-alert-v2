import json

def load_state():
    try:
        with open("config/state.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_state(state):
    try:
        with open("config/state.json", "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Failed to save state: {e}")
