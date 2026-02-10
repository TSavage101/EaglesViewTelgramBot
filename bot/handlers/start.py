"""
Start command handler - Main menu for Eagles View Bot
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler


MAIN_MENU_TEXT = """
🦅 *EAGLES VIEW* 🦅

Welcome to your campus discovery hub!

Choose a section to explore:
"""


def get_main_menu_keyboard():
    """Return the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🏠 Home", callback_data="section_home"),
            InlineKeyboardButton("📰 News", callback_data="section_news"),
        ],
        [
            InlineKeyboardButton("💜 Purple Board", callback_data="section_purple"),
            InlineKeyboardButton("⚽ Chancellors", callback_data="section_chancellors"),
        ],
        [
            InlineKeyboardButton("📝 Register as Provider", callback_data="register_start"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - show main menu."""
    await update.message.reply_text(
        MAIN_MENU_TEXT,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback to return to main menu."""
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_text(
            MAIN_MENU_TEXT,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    except Exception:
        # Can't edit media messages (photos/videos) — delete and send new
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=MAIN_MENU_TEXT,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )


def get_start_handlers():
    """Return handlers for start command."""
    return [
        CommandHandler("start", start_command),
        CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
    ]
