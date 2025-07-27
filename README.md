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

## Usage

1. Clone the repository and install dependencies
2. Create a `.env` file based on `.env.example`  
   - Add your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
3. Run `main.py` and follow the prompt  
   - Use saved configs or manually select pairs
   - Alerts will be sent to Telegram if set up
