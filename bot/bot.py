"""
Eagles View Telegram Bot - Main Application
"""
import os
import django

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EaglesViewTGBot.settings')
django.setup()

from telegram.ext import Application, Defaults
from telegram.request import HTTPXRequest
from django.conf import settings

from bot.handlers.start import get_start_handlers
from bot.handlers.home import get_home_handlers
from bot.handlers.news import get_news_handlers
from bot.handlers.purple_board import get_purple_board_handlers
from bot.handlers.chancellors import get_chancellors_handlers
from bot.handlers.registration import get_registration_handler


def create_application() -> Application:
    """Create and configure the bot application."""
    
    # Configure request with longer timeouts
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=30.0,
    )
    
    # Create the Application with custom request
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .request(request)
        .build()
    )
    
    # Add handlers
    # Registration conversation handler must be added first (before purple board's message handler)
    application.add_handler(get_registration_handler())
    
    # Add start handlers
    for handler in get_start_handlers():
        application.add_handler(handler)
    
    # Add section handlers
    for handler in get_home_handlers():
        application.add_handler(handler)
    
    for handler in get_news_handlers():
        application.add_handler(handler)
    
    # Purple board handlers (includes message handler for search)
    for handler in get_purple_board_handlers():
        application.add_handler(handler)
    
    for handler in get_chancellors_handlers():
        application.add_handler(handler)
    
    return application


def main():
    """Run the bot."""
    print("🦅 Starting Eagles View Bot...")
    print(f"Bot username: @{settings.TELEGRAM_BOT_USERNAME}")
    
    application = create_application()
    
    # Run the bot until Ctrl-C is pressed
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()

