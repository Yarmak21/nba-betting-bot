# NBA Value Betting Telegram Bot

A production-ready automated NBA value betting Telegram bot that analyzes games and identifies profitable betting opportunities.

## Features

- Fetches today's NBA games
- Gets team statistics
- Retrieves Polymarket probabilities
- Calculates model probabilities based on team net ratings
- Computes value edges
- Sends formatted reports to Telegram
- Robust error handling to prevent crashes
- Runs daily via GitHub Actions

## Configuration

The bot uses the following configuration:

- `TELEGRAM_TOKEN`: Telegram bot API token
- `TELEGRAM_CHAT_ID`: Chat ID to send reports to
- `NBA_API_KEY`: NBA API key for team statistics
- `POLYMARKET_URL`: Polymarket CLOB endpoint

## Edge Classification

- **GOOD BET**: Edge ≥ 7% (💡 emoji)
- **SMALL EDGE**: Edge 3-7% (📈 emoji)
- **NO BET**: Edge < 3% (🧱 emoji)

## Project Structure

```
nba-telegram-bot/
├── bot.py              # Main bot logic
├── config.py           # Configuration settings
├── requirements.txt    # Dependencies
└── .github/workflows/daily_run.yml  # GitHub Actions workflow
```

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables or update config.py with your API keys
4. Run the bot: `python bot.py`

## GitHub Actions

The bot runs daily at 09:00 UTC via GitHub Actions. To set up:

1. Add your API keys as GitHub Secrets:
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `NBA_API_KEY`
2. The workflow will automatically run daily

## Dependencies

- requests
- python-dateutil
- fuzzywuzzy
- python-Levenshtein

## Error Handling

The bot implements comprehensive error handling:
- Never crashes if any API fails
- Always sends a report even if no games are found
- Uses fallback 0.5/0.5 if Polymarket market is missing
- Handles team name variations with fuzzy matching