import os
import json
from core.binance_utils import get_futures_symbols
from config.state import save_state

CONFIG_DIR = "config/saves"
os.makedirs(CONFIG_DIR, exist_ok=True)

def validate_config_structure(config):
    if not isinstance(config, dict):
        return False

    required_keys = {
        "enabled": bool,
        "initial_price": (float, type(None), int),  # Aceptamos float o None o int
        "threshold": (float, int),
        "window_minutes": int,
        "alert_on_up": bool,
        "alert_on_down": bool
    }

    for symbol, settings in config.items():
        if not isinstance(symbol, str):
            return False
        if not isinstance(settings, dict):
            return False
        for key, expected_type in required_keys.items():
            if key not in settings or not isinstance(settings[key], expected_type):
                return False
    return True

def parse_indices(input_str):
    indices = set()
    parts = input_str.split(',')
    for part in parts:
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                indices.update(range(start, end + 1))
            except:
                continue
        else:
            try:
                indices.add(int(part.strip()))
            except:
                continue
    return sorted(list(indices))

def seleccionar_monedas():
    symbols = get_futures_symbols()
    print("\nAvailable Binance Futures pairs:\n")
    for i, sym in enumerate(symbols):
        print(f"{i+1:>3}. {sym}")

    print("\nEnter pair numbers (comma or range, e.g., 1,3,7-9).")
    print("Or enter a saved config name (e.g., my_config) to reuse it.")
    entry = input("> ").strip()

    test_mode = "T" in entry.upper()
    entry = entry.replace("T", "").replace("t", "").strip()

    filename = entry if entry.endswith(".json") else f"{entry}.json"
    path = os.path.join(CONFIG_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                state = json.load(f)

            if not validate_config_structure(state):
                raise ValueError("Invalid configuration structure or types.")

            save_state(state)
            print(f"\nLoaded configuration from '{filename}'\n")
            return state, test_mode

        except Exception as e:
            print(f"\nError reading '{filename}': {e}")
            print("Continuing with manual configuration...")

    indices = parse_indices(entry)
    selected = []
    for idx in indices:
        real_idx = idx - 1
        if 0 <= real_idx < len(symbols):
            selected.append(symbols[real_idx])

    print("\nGeneral configuration for all selected pairs:")

    while True:
        try:
            threshold = float(input("  - Threshold percentage: "))
            break
        except ValueError:
            print("  Invalid input. Enter a valid number.")

    while True:
        try:
            window = int(input("  - Evaluation window in minutes (multiple of 5): "))
            if window % 5 != 0 or window <= 0:
                raise ValueError
            break
        except ValueError:
            print("  Invalid input. Must be a positive multiple of 5.")

    while True:
        alert_up = input("  - Alert on upward movement? (y/n): ").lower()
        if alert_up in ("y", "n"):
            alert_up = alert_up == "y"
            break
        print("  Invalid input. Please enter 'y' or 'n'.")

    while True:
        alert_down = input("  - Alert on downward movement? (y/n): ").lower()
        if alert_down in ("y", "n"):
            alert_down = alert_down == "y"
            break
        print("  Invalid input. Please enter 'y' or 'n'.")

    state = {}
    for symbol in selected:
        state[symbol] = {
            "enabled": True,
            "initial_price": None,
            "threshold": threshold,
            "window_minutes": window,
            "alert_on_up": alert_up,
            "alert_on_down": alert_down
        }

    while True:
        save_ans = input("Do you want to save this configuration for future use? (y/n): ").lower()
        if save_ans in ("y", "n"):
            break
        print("  Invalid input. Please enter 'y' or 'n'.")

    if save_ans == "y":
        name = input("Enter a name for this configuration file: ").strip()
        save_path = os.path.join(CONFIG_DIR, f"{name}.json")
        with open(save_path, "w") as f:
            json.dump(state, f, indent=2)
        print(f"\nConfiguration saved as '{name}.json'\n")

    save_state(state)
    print("\nConfiguration saved to state.json.\n")
    return state, test_mode
