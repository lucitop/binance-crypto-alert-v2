import time
from datetime import datetime, timedelta
from config.state import load_state
from core.binance_utils import get_all_futures_prices
from messaging.telegram_bot import send_telegram_message

def start_monitoring(test_mode=False):
    print("Monitoring started...\n")

    state = load_state()
    history = {symbol: [] for symbol in state}

    test_counter = 0

    while True:
        now = datetime.utcnow()
        prices = get_all_futures_prices()

        if not prices:
            print("No price data received.")
            time.sleep(10)
            continue

        print(f"Tick at {now.strftime('%H:%M:%S')}")
        print(f"Received prices for: {list(prices.keys())[:15]} ...")

        configured_prices = {s: prices[s] for s in state if s in prices}
        print(f"Configured symbol prices: {configured_prices}\n")

        for symbol, config in state.items():
            if not config.get("enabled", True):
                continue

            price = prices.get(symbol)
            if price is None:
                print(f"Skipping {symbol}: no price available.")
                continue

            threshold = config.get("threshold", 5.0)
            window = config.get("window_minutes", 15)
            alert_up = config.get("alert_on_up", True)
            alert_down = config.get("alert_on_down", True)

            if test_mode:
                test_counter += 1
                if test_counter % 2 == 0:
                    price *= 1.2
                else:
                    price *= 0.85

            history[symbol].append((now, price))
            cutoff = now - timedelta(minutes=window)
            history[symbol] = [(t, p) for t, p in history[symbol] if t >= cutoff]

            if not history[symbol]:
                continue

            oldest_time, oldest_price = history[symbol][0]
            percentage_change = ((price - oldest_price) / oldest_price) * 100

            if alert_up and percentage_change >= threshold:
                message = f"{symbol} increased by {percentage_change:.2f}% in {window} minutes."
                send_telegram_message(message)
                print(f"↑ Alert: {message}")
                history[symbol] = [(now, price)]

            if alert_down and percentage_change <= -threshold:
                message = f"{symbol} decreased by {abs(percentage_change):.2f}% in {window} minutes."
                send_telegram_message(message)
                print(f"↓ Alert: {message}")
                history[symbol] = [(now, price)]

        time.sleep(10)
