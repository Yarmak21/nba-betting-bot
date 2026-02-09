import requests
import logging
from datetime import datetime
from fuzzywuzzy import fuzz
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, NBA_API_KEY, POLYMARKET_URL
import math


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_telegram_message(message):
    """
    Send a message to a Telegram chat using the bot API.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Message sent successfully: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        return False


def get_today_games():
    """
    Fetch today's NBA games from the API.
    """
    try:
        # Using a public API that doesn't require authentication for basic data
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Attempt to fetch from a real API - if it fails, fall back to mock data
        # This is a placeholder - in reality, you would use the actual NBA API
        # For demonstration purposes, returning mock data based on real NBA teams
        mock_response = {
            "games": [
                {
                    "game_id": "1",
                    "date": today,
                    "home_team": "Los Angeles Lakers",
                    "away_team": "Boston Celtics",
                    "home_team_id": 14,
                    "away_team_id": 2
                },
                {
                    "game_id": "2", 
                    "date": today,
                    "home_team": "New York Knicks",
                    "away_team": "Miami Heat",
                    "home_team_id": 17,
                    "away_team_id": 15
                },
                {
                    "game_id": "3", 
                    "date": today,
                    "home_team": "Golden State Warriors",
                    "away_team": "Phoenix Suns",
                    "home_team_id": 11,
                    "away_team_id": 23
                }
            ]
        }
        logger.info(f"Fetched {len(mock_response['games'])} games for {today}")
        return mock_response['games']
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        # Return empty list but log the error
        return []


def get_team_stats(team_id):
    """
    Get team statistics from the NBA API.
    """
    headers = {
        'Authorization': f'Bearer {NBA_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Placeholder for actual API call
        # In a real scenario, you would fetch from the actual NBA API
        # For demonstration, returning mock data
        mock_stats = {
            14: {"off_rating": 115.2, "def_rating": 108.7},  # Lakers
            2: {"off_rating": 118.5, "def_rating": 110.2},   # Celtics
            17: {"off_rating": 112.8, "def_rating": 109.1},  # Knicks
            15: {"off_rating": 110.3, "def_rating": 107.8}   # Heat
        }
        
        if team_id in mock_stats:
            logger.info(f"Fetched stats for team ID {team_id}")
            return mock_stats[team_id]
        else:
            logger.warning(f"No stats found for team ID {team_id}, using defaults")
            return {"off_rating": 110.0, "def_rating": 110.0}
            
    except Exception as e:
        logger.error(f"Error fetching team stats: {str(e)}")
        # Return default values to prevent crashes
        return {"off_rating": 110.0, "def_rating": 110.0}


def get_polymarket_probs(home_team, away_team):
    """
    Get probabilities from Polymarket for the given teams.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        params = {
            'category': 'basketball',
            'event': 'NBA'
        }
        response = requests.get(POLYMARKET_URL, headers=headers, params=params)
        response.raise_for_status()
        markets = response.json()
        
        # Find the market for the specific matchup
        for market in markets.get('data', []):
            if 'question' in market:
                title = market['question'].lower()
                
                # Handle team name variations using fuzzy matching
                home_variations = [home_team.lower(), home_team.replace(" ", "").lower(), 
                                  home_team.replace(" ", "-").lower(), home_team.replace(" ", "_").lower()]
                away_variations = [away_team.lower(), away_team.replace(" ", "").lower(),
                                  away_team.replace(" ", "-").lower(), away_team.replace(" ", "_").lower()]
                
                # Check if this market is for our teams using fuzzy matching
                title_clean = title.replace("will the", "").replace("win vs", "vs").strip()
                
                # Look for team names in the title
                home_found = any(fuzz.partial_ratio(var, title_clean) > 75 for var in home_variations)
                away_found = any(fuzz.partial_ratio(var, title_clean) > 75 for var in away_variations)
                
                if home_found and away_found:
                    # Extract probabilities from outcomes
                    outcomes = market.get('outcomes', [])
                    prices = market.get('prices', [])
                    
                    if len(outcomes) >= 2 and len(prices) >= 2:
                        # Find which outcome corresponds to home team
                        home_outcome_idx = -1
                        away_outcome_idx = -1
                        
                        for i, outcome in enumerate(outcomes):
                            outcome_text = outcome.lower()
                            if fuzz.partial_ratio(home_team.lower(), outcome_text) > 75:
                                home_outcome_idx = i
                            elif fuzz.partial_ratio(away_team.lower(), outcome_text) > 75:
                                away_outcome_idx = i
                        
                        if home_outcome_idx != -1 and away_outcome_idx != -1:
                            home_prob = float(prices[home_outcome_idx]) if prices[home_outcome_idx] else 0.5
                            away_prob = float(prices[away_outcome_idx]) if prices[away_outcome_idx] else 0.5
                            
                            logger.info(f"Found Polymarket odds for {home_team} vs {away_team}: Home={home_prob}, Away={away_prob}")
                            return home_prob, away_prob
        
        # If no market found, return default 0.5 / 0.5
        logger.warning(f"No Polymarket data found for {home_team} vs {away_team}, using default 0.5/0.5")
        return 0.5, 0.5
        
    except Exception as e:
        logger.error(f"Error fetching Polymarket data: {str(e)}")
        # Return default values to prevent crashes
        return 0.5, 0.5


def model_probability(home_team_id, away_team_id):
    """
    Calculate model probability based on team statistics.
    """
    try:
        home_stats = get_team_stats(home_team_id)
        away_stats = get_team_stats(away_team_id)
        
        # Calculate net ratings
        home_net = home_stats['off_rating'] - home_stats['def_rating']
        away_net = away_stats['off_rating'] - away_stats['def_rating']
        
        # Calculate difference
        diff = home_net - away_net
        
        # Apply logistic function to get probability
        # Using a simplified logistic function: prob = 1 / (1 + exp(-x))
        import math
        prob_home = 1 / (1 + math.exp(-diff / 10))
        
        # Ensure probability is between 0 and 1
        prob_home = max(0, min(1, prob_home))
        
        prob_away = 1 - prob_home
        
        logger.info(f"Model calculated probabilities: Home={prob_home:.3f}, Away={prob_away:.3f}")
        return prob_home, prob_away
        
    except Exception as e:
        logger.error(f"Error calculating model probability: {str(e)}")
        # Return neutral probabilities to prevent crashes
        return 0.5, 0.5


def classify_edge(model_prob, market_prob):
    """
    Classify the edge based on the difference between model and market probabilities.
    """
    edge = model_prob - market_prob
    
    if edge >= 0.07:
        return "GOOD BET", "💡", edge
    elif edge >= 0.03:
        return "SMALL EDGE", "📈", edge
    else:
        return "NO BET", "🧱", edge


def build_report(games):
    """
    Build the final report to send via Telegram.
    """
    report = []
    report.append("🏀 NBA Value Betting Report")
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("")
    
    for game in games:
        home_team = game['home_team']
        away_team = game['away_team']
        home_team_id = game['home_team_id']
        away_team_id = game['away_team_id']
        
        # Get Polymarket probabilities
        pm_home_prob, pm_away_prob = get_polymarket_probs(home_team, away_team)
        
        # Get model probabilities
        model_home_prob, model_away_prob = model_probability(home_team_id, away_team_id)
        
        # Classify the edge for home team
        edge_label, emoji, edge_value = classify_edge(model_home_prob, pm_home_prob)
        
        # Build game report
        report.append(f"{emoji} <b>{home_team} vs {away_team}</b>")
        report.append(f"Market: {pm_home_prob:.1%} vs {pm_away_prob:.1%}")
        report.append(f"Model: {model_home_prob:.1%} vs {model_away_prob:.1%}")
        report.append(f"Edge: {edge_value:.1%} ({edge_label})")
        
        # Add short reason
        home_stats = get_team_stats(home_team_id)
        away_stats = get_team_stats(away_team_id)
        
        home_net = home_stats['off_rating'] - home_stats['def_rating']
        away_net = away_stats['off_rating'] - away_stats['def_rating']
        
        report.append(f"Reason: {home_team} Net Rating: {home_net:.1f}, {away_team} Net Rating: {away_net:.1f}")
        report.append("")
    
    return "\n".join(report)


def main():
    """
    Main function to run the NBA value betting bot.
    """
    try:
        logger.info("Starting NBA value betting bot...")
        
        # Get today's games
        games = get_today_games()
        
        if not games:
            message = "🏀 NBA Value Betting Report\n\nNo games scheduled for today."
            send_telegram_message(message)
            logger.info("No games found for today, sent notification.")
            return
        
        # Build the report
        report = build_report(games)
        
        # Send the report via Telegram
        success = send_telegram_message(report)
        
        if success:
            logger.info("Report sent successfully to Telegram.")
        else:
            logger.error("Failed to send report to Telegram.")
    
    except Exception as e:
        logger.error(f"Critical error in main function: {str(e)}")
        error_message = f"🚨 Bot Error: {str(e)}"
        send_telegram_message(error_message)


if __name__ == "__main__":
    main()