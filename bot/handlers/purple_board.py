"""
Purple Board handler - Service Concierge (Core Feature)
Search and discover service providers
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from django.db.models import Q, Case, When, Value, IntegerField
from django.conf import settings
from asgiref.sync import sync_to_async
import os


RESULTS_PER_PAGE = 5


def escape_md(text):
    """Escape Markdown special characters in user input."""
    if not text:
        return text
    text = str(text)
    for char in ['_', '*', '`', '[']:
        text = text.replace(char, f'\\{char}')
    return text


async def purple_board_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Purple Board section."""
    query = update.callback_query
    await query.answer()
    
    # Set state to expect search query
    context.user_data['expecting_search'] = True
    context.user_data['search_results'] = []
    context.user_data['search_page'] = 0
    
    text = """💜 *PURPLE BOARD*
_Service Concierge_

🔍 *Search for services*
Type a keyword to find providers:

Examples:
• `lash` - Find lash technicians
• `frontend` - Find developers
• `photography` - Find photographers
• `design` - Find graphic designers

_Or browse by category:_"""
    
    # Get categories with active providers
    from bot.models import Category
    
    @sync_to_async
    def get_categories():
        return list(Category.objects.filter(
            providers__is_approved=True,
            providers__is_active=True
        ).distinct()[:10])
    
    categories = await get_categories()
    
    keyboard = []
    
    # Category buttons (2 per row)
    cat_row = []
    for cat in categories:
        cat_row.append(InlineKeyboardButton(f"📁 {cat.name}", callback_data=f"cat_{cat.id}"))
        if len(cat_row) == 2:
            keyboard.append(cat_row)
            cat_row = []
    if cat_row:
        keyboard.append(cat_row)
    
    keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="main_menu")])
    
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


async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search queries from users."""
    if not context.user_data.get('expecting_search'):
        return
    
    query_text = update.message.text.strip().lower()
    
    if len(query_text) < 2:
        await update.message.reply_text(
            "🔍 Please enter at least 2 characters to search.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to Purple Board", callback_data="section_purple")
            ]])
        )
        return
    
    from bot.models import ServiceProvider
    
    @sync_to_async
    def search_providers(q):
        providers = ServiceProvider.objects.filter(
            is_approved=True,
            is_active=True
        ).filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(keywords__icontains=q) |
            Q(category__name__icontains=q)
        ).annotate(
            plan_priority=Case(
                When(plan_type='PREMIUM', then=Value(3)),
                When(plan_type='VERIFIED', then=Value(2)),
                When(plan_type='BASIC', then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-plan_priority', '-created_at')
        return list(providers.values_list('id', flat=True))
    
    result_ids = await search_providers(query_text)
    
    if not result_ids:
        await update.message.reply_text(
            f"🔍 No providers found for *{query_text}*\n\nTry a different keyword!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 Search Again", callback_data="section_purple"),
                InlineKeyboardButton("« Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Store results
    context.user_data['search_results'] = result_ids
    context.user_data['search_page'] = 0
    context.user_data['search_query'] = query_text
    
    await show_search_results(update, context, from_message=True)


async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False) -> None:
    """Display search results with pagination."""
    from bot.models import ServiceProvider
    
    result_ids = context.user_data.get('search_results', [])
    page = context.user_data.get('search_page', 0)
    query_text = context.user_data.get('search_query', '')
    
    offset = page * RESULTS_PER_PAGE
    page_ids = result_ids[offset:offset + RESULTS_PER_PAGE]
    
    @sync_to_async
    def get_providers(ids):
        providers = list(ServiceProvider.objects.filter(id__in=ids))
        # Preserve order
        return sorted(providers, key=lambda p: ids.index(p.id))
    
    providers = await get_providers(page_ids)
    
    total_count = len(result_ids)
    total_pages = (total_count + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    
    text = f"🔍 Results for '{escape_md(query_text)}'\n"
    text += f"{total_count} provider(s) found\n\n"
    
    keyboard = []
    
    for provider in providers:
        badge = provider.get_display_badge()
        badge_str = f" {badge}" if badge else ""
        
        name = escape_md(provider.name)
        desc = escape_md(provider.description[:80])
        text += f"{name}{badge_str}\n"
        text += f"📝 {desc}\n\n"
        
        name_short = provider.name[:20] + "..." if len(provider.name) > 20 else provider.name
        keyboard.append([
            InlineKeyboardButton(
                f"👤 View {name_short}", 
                callback_data=f"provider_{provider.id}"
            )
        ])
    
    # Pagination
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data="search_prev"))
    
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="search_info"))
    
    if offset + RESULTS_PER_PAGE < total_count:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data="search_next"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([
        InlineKeyboardButton("🔍 New Search", callback_data="section_purple"),
        InlineKeyboardButton("« Menu", callback_data="main_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if from_message:
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        query = update.callback_query
        try:
            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except:
            await query.message.delete()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )


async def search_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search results pagination."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    page = context.user_data.get('search_page', 0)
    
    if action == "search_next":
        context.user_data['search_page'] = page + 1
    elif action == "search_prev":
        context.user_data['search_page'] = max(0, page - 1)
    
    await show_search_results(update, context)


async def view_provider(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display provider profile with contact card."""
    from bot.models import ServiceProvider
    
    query = update.callback_query
    await query.answer()
    
    provider_id = int(query.data.replace("provider_", ""))
    
    @sync_to_async
    def get_provider(pid):
        try:
            return ServiceProvider.objects.select_related('category').get(id=pid)
        except ServiceProvider.DoesNotExist:
            return None
    
    provider = await get_provider(provider_id)
    
    if not provider:
        await query.edit_message_text(
            "❌ Provider not found.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back", callback_data="section_purple")
            ]])
        )
        return
    
    # Build contact card (escape special markdown chars)
    name = escape_md(provider.name)
    badge = provider.get_display_badge()
    desc = escape_md(provider.description)
    
    lines = [f"📋 {name}"]
    if badge:
        lines[0] += f" {badge}"
    lines.append(f"\n📝 {desc}")
    
    if provider.phone:
        lines.append(f"📞 {escape_md(provider.phone)}")
    if provider.telegram_handle:
        lines.append(f"💬 {escape_md(provider.telegram_handle)}")
    if provider.instagram_handle:
        lines.append(f"📸 {escape_md(provider.instagram_handle)}")
    if provider.plan_type == 'PREMIUM' and provider.hall_of_residence:
        lines.append(f"🏠 {escape_md(provider.hall_of_residence)}")
    
    text = "\n".join(lines)
    
    # Add keywords
    if provider.keywords:
        keywords = provider.keywords if isinstance(provider.keywords, list) else [provider.keywords]
        text += f"\n\n🏷️ Keywords: {escape_md(', '.join(str(k) for k in keywords))}"
    
    # Add category
    if provider.category:
        text += f"\n📁 Category: {escape_md(provider.category.name)}"
    
    keyboard = []
    
    # Contact buttons
    contact_row = []
    if provider.telegram_handle:
        handle = provider.telegram_handle.lstrip('@')
        contact_row.append(InlineKeyboardButton("💬 Telegram", url=f"https://t.me/{handle}"))
    
    if provider.instagram_handle:
        handle = provider.instagram_handle.lstrip('@')
        contact_row.append(InlineKeyboardButton("📸 Instagram", url=f"https://instagram.com/{handle}"))
    
    if contact_row:
        keyboard.append(contact_row)
    
    # Catalogue button
    if provider.catalogue:
        keyboard.append([InlineKeyboardButton("📄 View Catalogue", callback_data=f"catalogue_{provider.id}")])
    
    keyboard.append([
        InlineKeyboardButton("« Back to Results", callback_data="search_back"),
        InlineKeyboardButton("« Menu", callback_data="main_menu")
    ])
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def view_catalogue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send provider's PDF catalogue."""
    from bot.models import ServiceProvider
    
    query = update.callback_query
    await query.answer("Sending catalogue...")
    
    provider_id = int(query.data.replace("catalogue_", ""))
    
    @sync_to_async
    def get_provider(pid):
        try:
            return ServiceProvider.objects.get(id=pid)
        except ServiceProvider.DoesNotExist:
            return None
    
    provider = await get_provider(provider_id)
    
    if not provider:
        return
    
    if provider.catalogue:
        catalogue_path = os.path.join(settings.MEDIA_ROOT, str(provider.catalogue))
        if os.path.exists(catalogue_path):
            with open(catalogue_path, 'rb') as doc:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=doc,
                    filename=f"{provider.name}_catalogue.pdf",
                    caption=f"📄 Catalogue for *{provider.name}*",
                    parse_mode='Markdown'
                )


async def browse_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Browse providers in a specific category."""
    from bot.models import ServiceProvider, Category
    
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.replace("cat_", ""))
    
    @sync_to_async
    def get_category_providers(cat_id):
        try:
            category = Category.objects.get(id=cat_id)
        except Category.DoesNotExist:
            return None, []
        
        providers = ServiceProvider.objects.filter(
            category=category,
            is_approved=True,
            is_active=True
        ).annotate(
            plan_priority=Case(
                When(plan_type='PREMIUM', then=Value(3)),
                When(plan_type='VERIFIED', then=Value(2)),
                When(plan_type='BASIC', then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-plan_priority', '-created_at')
        
        return category, list(providers.values_list('id', flat=True))
    
    category, result_ids = await get_category_providers(category_id)
    
    if not category:
        return
    
    context.user_data['search_results'] = result_ids
    context.user_data['search_page'] = 0
    context.user_data['search_query'] = category.name
    
    await show_search_results(update, context)


async def search_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Go back to search results."""
    query = update.callback_query
    await query.answer()
    await show_search_results(update, context)


def get_purple_board_handlers():
    """Return handlers for Purple Board section."""
    return [
        CallbackQueryHandler(purple_board_section, pattern="^section_purple$"),
        CallbackQueryHandler(view_provider, pattern=r"^provider_\d+$"),
        CallbackQueryHandler(view_catalogue, pattern=r"^catalogue_\d+$"),
        CallbackQueryHandler(browse_category, pattern=r"^cat_\d+$"),
        CallbackQueryHandler(search_pagination, pattern="^search_(prev|next|info)$"),
        CallbackQueryHandler(search_back, pattern="^search_back$"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query),
    ]
