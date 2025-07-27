import requests

def get_futures_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()["symbols"]
        return sorted([s["symbol"] for s in data if s["contractType"] == "PERPETUAL"])
    except Exception as e:
        print(f"Failed to fetch futures symbols: {e}")
        return []

def get_all_futures_prices():
    url = "https://fapi.binance.com/fapi/v1/ticker/price"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {entry["symbol"]: float(entry["price"]) for entry in data}
    except Exception as e:
        print(f"Failed to fetch futures prices: {e}")
        return {}
