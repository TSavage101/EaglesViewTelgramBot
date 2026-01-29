"""
Home/Ads Hub handler - Display advertisements
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import sync_to_async
import os


async def home_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Home/Ads section."""
    query = update.callback_query
    await query.answer()
    
    # Import here to avoid circular imports
    from bot.models import Advertisement
    
    # Get active ads using sync_to_async
    @sync_to_async
    def get_ads():
        now = timezone.now()
        ads = Advertisement.objects.filter(
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).order_by('slot_position')
        return list(ads.values('id', 'title', 'ad_type', 'media_file', 'caption', 'external_link'))
    
    ads = await get_ads()
    
    if not ads:
        keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            "🏠 *HOME*\n\nNo advertisements available at the moment.\nCheck back later!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Store ads in context for navigation
    context.user_data['ads'] = ads
    context.user_data['current_ad_index'] = 0
    
    await show_ad(update, context, edit=True)


async def show_ad(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False) -> None:
    """Display the current ad."""
    ads = context.user_data.get('ads', [])
    index = context.user_data.get('current_ad_index', 0)
    
    if not ads or index >= len(ads):
        return
    
    ad = ads[index]
    
    # Build navigation keyboard
    keyboard = []
    nav_row = []
    
    if index > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data="ad_prev"))
    
    nav_row.append(InlineKeyboardButton(f"{index + 1}/{len(ads)}", callback_data="ad_count"))
    
    if index < len(ads) - 1:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data="ad_next"))
    
    keyboard.append(nav_row)
    
    if ad.get('external_link'):
        keyboard.append([InlineKeyboardButton("🔗 Learn More", url=ad['external_link'])])
    
    keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = f"📢 *{ad['title']}*"
    if ad.get('caption'):
        caption += f"\n\n{ad['caption']}"
    
    # Get the media file path
    media_path = os.path.join(settings.MEDIA_ROOT, str(ad['media_file']))
    
    query = update.callback_query
    chat_id = query.message.chat_id
    
    # Delete previous message and send new one with media
    try:
        await query.message.delete()
    except:
        pass
    
    if ad['ad_type'] == 'VIDEO':
        if os.path.exists(media_path):
            with open(media_path, 'rb') as video:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=video,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption + "\n\n_(Video not available)_",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    else:  # PICTURE
        if os.path.exists(media_path):
            with open(media_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption + "\n\n_(Image not available)_",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )


async def ad_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ad navigation."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    ads = context.user_data.get('ads', [])
    index = context.user_data.get('current_ad_index', 0)
    
    if action == "ad_next" and index < len(ads) - 1:
        context.user_data['current_ad_index'] = index + 1
    elif action == "ad_prev" and index > 0:
        context.user_data['current_ad_index'] = index - 1
    
    await show_ad(update, context)


def get_home_handlers():
    """Return handlers for home section."""
    return [
        CallbackQueryHandler(home_section, pattern="^section_home$"),
        CallbackQueryHandler(ad_navigation, pattern="^ad_(prev|next|count)$"),
    ]
