"""
News section handler - Display news updates
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from django.conf import settings
from asgiref.sync import sync_to_async
import os


NEWS_PER_PAGE = 5


async def news_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle News section - show list of news."""
    query = update.callback_query
    await query.answer()
    
    # Reset page
    context.user_data['news_page'] = 0
    await show_news_list(update, context)


async def show_news_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display paginated news list."""
    from bot.models import News
    
    page = context.user_data.get('news_page', 0)
    offset = page * NEWS_PER_PAGE
    
    @sync_to_async
    def get_news_data():
        all_news = News.objects.filter(is_published=True)
        total_count = all_news.count()
        news_items = list(all_news[offset:offset + NEWS_PER_PAGE])
        return news_items, total_count
    
    news_items, total_count = await get_news_data()
    
    if not news_items:
        keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="main_menu")]]
        text = "📰 *NEWS*\n\nNo news available at the moment.\nCheck back later!"
        
        query = update.callback_query
        if query:
            try:
                await query.edit_message_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except:
                await query.message.delete()
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        return
    
    # Build news list
    text = "📰 *LATEST NEWS*\n\n"
    keyboard = []
    
    for news in news_items:
        # Category emoji
        cat_emoji = {
            'GENERAL': '📌',
            'CAMPUS': '🏫',
            'TECH': '💻',
            'SPORTS': '⚽',
            'ANNOUNCEMENT': '📢',
        }.get(news.category, '📌')
        
        text += f"{cat_emoji} *{news.title}*\n"
        text += f"_{news.created_at.strftime('%b %d, %Y')}_\n\n"
        
        title_short = news.title[:30] + "..." if len(news.title) > 30 else news.title
        keyboard.append([
            InlineKeyboardButton(f"📖 {title_short}", callback_data=f"news_view_{news.id}")
        ])
    
    # Pagination
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data="news_page_prev"))
    
    total_pages = (total_count + NEWS_PER_PAGE - 1) // NEWS_PER_PAGE
    nav_row.append(InlineKeyboardButton(f"Page {page + 1}/{total_pages}", callback_data="news_page_info"))
    
    if offset + NEWS_PER_PAGE < total_count:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data="news_page_next"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="main_menu")])
    
    query = update.callback_query
    try:
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        # If message has media, delete and send new
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def view_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a single news item."""
    from bot.models import News
    
    query = update.callback_query
    await query.answer()
    
    # Extract news ID from callback data
    news_id = int(query.data.replace("news_view_", ""))
    
    @sync_to_async
    def get_news(nid):
        try:
            return News.objects.get(id=nid)
        except News.DoesNotExist:
            return None
    
    news = await get_news(news_id)
    
    if not news:
        await query.edit_message_text(
            "❌ News item not found.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to News", callback_data="section_news")
            ]])
        )
        return
    
    # Category emoji
    cat_emoji = {
        'GENERAL': '📌',
        'CAMPUS': '🏫',
        'TECH': '💻',
        'SPORTS': '⚽',
        'ANNOUNCEMENT': '📢',
    }.get(news.category, '📌')
    
    text = f"{cat_emoji} *{news.title}*\n"
    text += f"_{news.category} • {news.created_at.strftime('%B %d, %Y at %H:%M')}_\n\n"
    text += news.content
    
    keyboard = [
        [InlineKeyboardButton("« Back to News", callback_data="section_news")],
        [InlineKeyboardButton("« Main Menu", callback_data="main_menu")],
    ]
    
    # Check if news has an image
    if news.image:
        image_path = os.path.join(settings.MEDIA_ROOT, str(news.image))
        if os.path.exists(image_path):
            try:
                await query.message.delete()
            except:
                pass
            
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return
    
    # No image, just text
    try:
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def news_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle news pagination."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    page = context.user_data.get('news_page', 0)
    
    if action == "news_page_next":
        context.user_data['news_page'] = page + 1
    elif action == "news_page_prev":
        context.user_data['news_page'] = max(0, page - 1)
    
    await show_news_list(update, context)


def get_news_handlers():
    """Return handlers for news section."""
    return [
        CallbackQueryHandler(news_section, pattern="^section_news$"),
        CallbackQueryHandler(view_news, pattern=r"^news_view_\d+$"),
        CallbackQueryHandler(news_pagination, pattern="^news_page_(prev|next|info)$"),
    ]
