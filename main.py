from core.selector import seleccionar_monedas
from core.monitor import start_monitoring

def main():
    state, test_mode = seleccionar_monedas()
    if not state:
        print("No symbols configured. Exiting.")
        return
    start_monitoring(test_mode=test_mode)

if __name__ == "__main__":
    main()
