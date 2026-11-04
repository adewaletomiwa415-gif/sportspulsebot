import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sofascore_api import SofaScoreClient

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize SofaScore client (no key needed)
client = SofaScoreClient()

# ==================== Helper: Format Match Data ====================
def format_match(ev):
    home = ev.get("homeTeam", {}).get("name", "Unknown")
    away = ev.get("awayTeam", {}).get("name", "Unknown")
    hs = ev.get("homeScore", {}).get("current", "-")
    as_ = ev.get("awayScore", {}).get("current", "-")
    status = ev.get("status", {}).get("description", "Scheduled")
    # Extract league name
    tournament = ev.get("tournament", {}).get("name", "Unknown League")
    return f"🏆 {tournament}\n⚽ {home} {hs} - {as_} {away}\n📌 Status: {status}"

# ==================== Command Handlers ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ **Sports Bot Ready!**\n"
        "Commands:\n"
        "/live - Live football scores\n"
        "/fixtures - Today's upcoming matches\n"
        "/standings - League table (Premier League example)\n"
        "/stats - Match statistics (demo)\n"
        "/news - Sports news (placeholder)",
        parse_mode="Markdown"
    )

async def live_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Fetch live football matches
        live_events = client.get_live_events("football")
        if not live_events:
            await update.message.reply_text("No live football matches right now.")
            return
        
        # Show top 5 live matches to avoid message too long
        text = "🔴 **Live Matches**\n\n"
        for ev in live_events[:5]:
            text += format_match(ev) + "\n\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Live error: {e}")
        await update.message.reply_text("⚠️ Unable to fetch live scores. Data source may be busy.")

async def fixtures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Fetch today's matches
        events = client.get_events_today("football")
        if not events:
            await update.message.reply_text("No fixtures found for today.")
            return
        
        text = "📅 **Today's Fixtures**\n\n"
        # Filter for scheduled matches only (or just show first 5)
        for ev in events[:5]:
            text += format_match(ev) + "\n\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Fixtures error: {e}")
        await update.message.reply_text("⚠️ Unable to fetch fixtures.")

async def standings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Hardcoded example: Premier League ID is 17 in SofaScore
        # You can find other IDs by exploring, but this works for demo
        league_id = 17 
        
        # First get seasons to find current season ID (or use a known one)
        seasons = client.get_tournament_seasons(league_id)
        if not seasons:
            await update.message.reply_text("Could not load league data.")
            return
        
        current_season = seasons[0]["id"] # Usually the latest season
        
        # Get standings
        standings_data = client.get_tournament_standings(league_id, season_id=current_season)
        
        # Parse standings (structure varies, usually contains 'rows')
        if not standings_data or "rows" not in standings_data:
            await update.message.reply_text("Standings data format unavailable.")
            return
        
        text = "🏆 **Premier League Standings (Top 5)**\n\n"
        rows = standings_data["rows"][:5]
        for idx, row in enumerate(rows, 1):
            team = row.get("team", {}).get("name", "Unknown")
            points = row.get("points", 0)
            text += f"{idx}. {team} - {points} pts\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Standings error: {e}")
        await update.message.reply_text("⚠️ Unable to fetch standings. (Note: Free data sources may limit this)")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This is a demo. To get real stats, you need a specific event ID.
    # The flow: get live -> pick event id -> get_event_statistics(event_id)
    await update.message.reply_text(
        "📊 **Match Stats Feature**\n"
        "To get detailed stats, I need a specific match ID.\n"
        "In a full version, you would tap a button on a live match to see possession, shots, etc.\n"
        "This demo currently shows the placeholder because live event IDs change rapidly.",
        parse_mode="Markdown"
    )

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder because real news needs RSS/APIs
    await update.message.reply_text(
        "📰 **Sports News**\n"
        "This section requires an RSS feed or a news API key.\n"
        "You can add a feedparser later to pull from BBC Sport RSS for free.",
        parse_mode="Markdown"
    )

# ==================== Main App ====================
def main():
    # Get token from environment variable (Railway will set this)
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable is missing!")
        return

    app = Application.builder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", live_scores))
    app.add_handler(CommandHandler("fixtures", fixtures))
    app.add_handler(CommandHandler("standings", standings))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("news", news))

    logger.info("Bot starting with Long Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
