# binance-crypto-alert-v2

Python bot to monitor Binance Futures pairs and trigger alerts based on price changes.

## Features

- Monitor selected Binance Futures pairs  
- Custom % thresholds and time windows  
- Alerts on upward/downward price changes  
- Save/load configurations via JSON files  
- Validates saved configuration structure  
- Flexible pair selection (e.g., `1,3,5-7`)  
- Test mode: type `t` when selecting pairs  
- Telegram alerts using bot token and chat ID
- Post-alert price tracking for 1 hour with analytics

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file based on `.env.example`
4. Add your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

## Usage

Run `python main.py` and follow the prompts to:
- Select cryptocurrency pairs to monitor
- Configure alert thresholds and time windows
- Save configurations for future use
- Start real-time monitoring

## Data Analysis

View tracking data from recent alerts:
```bash
python tools/tracking_analyzer.py summary
python tools/tracking_analyzer.py stats BTCUSDT
```

## License

MIT License
