"""
Registration handler - Service provider registration flow
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, MessageHandler, 
    filters, ConversationHandler
)
from asgiref.sync import sync_to_async


# Conversation states
(
    WAITING_NAME,
    WAITING_DESCRIPTION,
    WAITING_KEYWORDS,
    WAITING_CATEGORY,
    WAITING_PHONE,
    WAITING_TELEGRAM,
    WAITING_INSTAGRAM,
    WAITING_HALL,
    WAITING_CATALOGUE,
    WAITING_PLAN,
    CONFIRM_REGISTRATION,
) = range(11)


PLAN_INFO = """
💰 *REGISTRATION PLANS*

*Basic* - ₦1,500
• Listed in search results

*Verified* - ₦3,000
• ✅ Verified badge (after review)
• Higher trust with customers

*Premium* - ₦5,000
• ⭐ Premium badge
• Top placement in search
• Hall of residence in your card
"""


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process."""
    query = update.callback_query
    await query.answer()
    
    # Clear previous registration data
    context.user_data['registration'] = {}
    context.user_data['expecting_search'] = False  # Disable search mode
    
    text = """📝 *PROVIDER REGISTRATION*

Welcome! Let's get you registered on Purple Board.

Please enter your *Business/Service Name*:

_Example: "Lash by Sarah", "TechDev Solutions"_"""
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")]]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return WAITING_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive business name."""
    name = update.message.text.strip()
    
    if len(name) < 3:
        await update.message.reply_text(
            "❌ Name too short. Please enter at least 3 characters.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
            ]])
        )
        return WAITING_NAME
    
    context.user_data['registration']['name'] = name
    
    await update.message.reply_text(
        f"✅ Great! Your business name is: *{name}*\n\n"
        "Now, enter a *short description* of your services:\n\n"
        "_Example: 'Professional lash technician with 3 years experience. "
        "Specializing in classic and volume lashes.'_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive business description."""
    description = update.message.text.strip()
    
    if len(description) < 10:
        await update.message.reply_text(
            "❌ Description too short. Please enter at least 10 characters.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
            ]])
        )
        return WAITING_DESCRIPTION
    
    context.user_data['registration']['description'] = description[:500]
    
    await update.message.reply_text(
        "✅ Description saved!\n\n"
        "Enter *keywords* for your service (comma-separated):\n\n"
        "_Example: lash, beauty, makeup, volume lash_\n\n"
        "These help customers find you in search!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_KEYWORDS


async def receive_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive keywords."""
    keywords_text = update.message.text.strip()
    keywords = [k.strip().lower() for k in keywords_text.split(',') if k.strip()]
    
    if not keywords:
        await update.message.reply_text(
            "❌ Please enter at least one keyword.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
            ]])
        )
        return WAITING_KEYWORDS
    
    context.user_data['registration']['keywords'] = keywords
    
    # Use first keyword as category name
    category_name = keywords[0].title()
    context.user_data['registration']['category_name'] = category_name
    
    await update.message.reply_text(
        f"✅ Keywords saved: {', '.join(keywords)}\n\n"
        f"Your category will be: *{category_name}*\n\n"
        "Now enter your *phone number*:\n\n"
        "_Example: 08012345678_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_phone"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive phone number."""
    phone = update.message.text.strip()
    context.user_data['registration']['phone'] = phone
    
    await update.message.reply_text(
        "✅ Phone saved!\n\n"
        "Enter your *Telegram username* (without @):\n\n"
        "_Example: yourname_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_telegram"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_TELEGRAM


async def skip_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip phone number."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['registration']['phone'] = ''
    
    await query.edit_message_text(
        "Enter your *Telegram username* (without @):\n\n"
        "_Example: yourname_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_telegram"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_TELEGRAM


async def receive_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive Telegram handle."""
    handle = update.message.text.strip().lstrip('@')
    context.user_data['registration']['telegram_handle'] = f"@{handle}"
    
    await update.message.reply_text(
        "✅ Telegram saved!\n\n"
        "Enter your *Instagram username* (without @):\n\n"
        "_Example: yourinstagram_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_instagram"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_INSTAGRAM


async def skip_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip Telegram handle."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['registration']['telegram_handle'] = ''
    
    await query.edit_message_text(
        "Enter your *Instagram username* (without @):\n\n"
        "_Example: yourinstagram_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_instagram"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_INSTAGRAM


async def receive_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive Instagram handle."""
    handle = update.message.text.strip().lstrip('@')
    context.user_data['registration']['instagram_handle'] = f"@{handle}"
    
    return await ask_for_catalogue(update, context)


async def skip_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip Instagram handle."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['registration']['instagram_handle'] = ''
    
    return await ask_for_catalogue_callback(update, context)


async def ask_for_catalogue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for catalogue upload."""
    await update.message.reply_text(
        "✅ Instagram saved!\n\n"
        "📄 *CATALOGUE/PORTFOLIO*\n\n"
        "Please upload a *PDF* with your work samples, pricing, or portfolio.\n\n"
        "_This helps customers learn more about your services!_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_catalogue"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_CATALOGUE


async def ask_for_catalogue_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for catalogue upload (from callback)."""
    query = update.callback_query
    
    await query.edit_message_text(
        "📄 *CATALOGUE/PORTFOLIO*\n\n"
        "Please upload a *PDF* with your work samples, pricing, or portfolio.\n\n"
        "_This helps customers learn more about your services!_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ Skip", callback_data="skip_catalogue"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
        ]])
    )
    
    return WAITING_CATALOGUE


async def receive_catalogue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive catalogue PDF."""
    document = update.message.document
    
    if not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ Please upload a PDF file only.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭ Skip", callback_data="skip_catalogue"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
            ]])
        )
        return WAITING_CATALOGUE
    
    # Store file_id for later download
    context.user_data['registration']['catalogue_file_id'] = document.file_id
    context.user_data['registration']['catalogue_name'] = document.file_name
    
    return await show_plan_selection(update, context)


async def skip_catalogue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip catalogue upload."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['registration']['catalogue_file_id'] = None
    
    return await show_plan_selection_callback(update, context)


async def show_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show plan selection."""
    await update.message.reply_text(
        PLAN_INFO + "\n\nSelect your plan:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Basic - ₦1,500", callback_data="plan_BASIC")],
            [InlineKeyboardButton("Verified - ₦3,000", callback_data="plan_VERIFIED")],
            [InlineKeyboardButton("Premium - ₦5,000", callback_data="plan_PREMIUM")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")],
        ])
    )
    
    return WAITING_PLAN


async def show_plan_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show plan selection (from callback)."""
    query = update.callback_query
    
    await query.edit_message_text(
        PLAN_INFO + "\n\nSelect your plan:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Basic - ₦1,500", callback_data="plan_BASIC")],
            [InlineKeyboardButton("Verified - ₦3,000", callback_data="plan_VERIFIED")],
            [InlineKeyboardButton("Premium - ₦5,000", callback_data="plan_PREMIUM")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")],
        ])
    )
    
    return WAITING_PLAN


async def receive_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive plan selection."""
    query = update.callback_query
    await query.answer()
    
    plan = query.data.replace("plan_", "")
    context.user_data['registration']['plan_type'] = plan
    
    # If premium, ask for hall of residence
    if plan == 'PREMIUM':
        await query.edit_message_text(
            "⭐ *PREMIUM PLAN SELECTED*\n\n"
            "Enter your *Hall of Residence*:\n\n"
            "_This will be shown on your contact card._",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭ Skip", callback_data="skip_hall"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
            ]])
        )
        return WAITING_HALL
    
    return await show_confirmation(update, context)


async def receive_hall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive hall of residence."""
    hall = update.message.text.strip()
    context.user_data['registration']['hall_of_residence'] = hall
    
    return await show_confirmation_message(update, context)


async def skip_hall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip hall of residence."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['registration']['hall_of_residence'] = ''
    
    return await show_confirmation(update, context)


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show registration confirmation."""
    query = update.callback_query
    reg = context.user_data.get('registration', {})
    
    plan_prices = {'BASIC': '₦1,500', 'VERIFIED': '₦3,000', 'PREMIUM': '₦5,000'}
    
    text = "📋 *REGISTRATION SUMMARY*\n\n"
    text += f"*Name:* {reg.get('name')}\n"
    desc = reg.get('description', '')[:100]
    text += f"*Description:* {desc}...\n"
    text += f"*Keywords:* {', '.join(reg.get('keywords', []))}\n"
    text += f"*Category:* {reg.get('category_name')}\n"
    text += f"*Phone:* {reg.get('phone') or 'Not provided'}\n"
    text += f"*Telegram:* {reg.get('telegram_handle') or 'Not provided'}\n"
    text += f"*Instagram:* {reg.get('instagram_handle') or 'Not provided'}\n"
    text += f"*Catalogue:* {'✅ Uploaded' if reg.get('catalogue_file_id') else '❌ Not uploaded'}\n"
    text += f"*Plan:* {reg.get('plan_type')} - {plan_prices.get(reg.get('plan_type'), '?')}\n"
    
    if reg.get('hall_of_residence'):
        text += f"*Hall:* {reg.get('hall_of_residence')}\n"
    
    text += "\n⚠️ *Please pay to complete registration:*\n"
    text += "_Payment details will be sent after confirmation._"
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm & Submit", callback_data="confirm_registration")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")],
        ])
    )
    
    return CONFIRM_REGISTRATION


async def show_confirmation_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show registration confirmation (from message)."""
    reg = context.user_data.get('registration', {})
    
    plan_prices = {'BASIC': '₦1,500', 'VERIFIED': '₦3,000', 'PREMIUM': '₦5,000'}
    
    text = "📋 *REGISTRATION SUMMARY*\n\n"
    text += f"*Name:* {reg.get('name')}\n"
    desc = reg.get('description', '')[:100]
    text += f"*Description:* {desc}...\n"
    text += f"*Keywords:* {', '.join(reg.get('keywords', []))}\n"
    text += f"*Category:* {reg.get('category_name')}\n"
    text += f"*Phone:* {reg.get('phone') or 'Not provided'}\n"
    text += f"*Telegram:* {reg.get('telegram_handle') or 'Not provided'}\n"
    text += f"*Instagram:* {reg.get('instagram_handle') or 'Not provided'}\n"
    text += f"*Catalogue:* {'✅ Uploaded' if reg.get('catalogue_file_id') else '❌ Not uploaded'}\n"
    text += f"*Plan:* {reg.get('plan_type')} - {plan_prices.get(reg.get('plan_type'), '?')}\n"
    
    if reg.get('hall_of_residence'):
        text += f"*Hall:* {reg.get('hall_of_residence')}\n"
    
    text += "\n⚠️ *Please pay to complete registration:*\n"
    text += "_Payment details will be sent after confirmation._"
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm & Submit", callback_data="confirm_registration")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")],
        ])
    )
    
    return CONFIRM_REGISTRATION


async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Complete the registration and save to database."""
    query = update.callback_query
    await query.answer("Saving your registration...")
    
    reg = context.user_data.get('registration', {})
    user_id = query.from_user.id
    
    from bot.models import ServiceProvider, Category
    from django.conf import settings
    import os
    
    @sync_to_async
    def check_existing(uid):
        return ServiceProvider.objects.filter(telegram_user_id=uid).exists()
    
    @sync_to_async
    def get_or_create_category(cat_name):
        category, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={'slug': cat_name.lower().replace(' ', '-')}
        )
        return category
    
    @sync_to_async
    def save_provider(provider):
        provider.save()
        return provider
    
    # Check if already registered
    if await check_existing(user_id):
        await query.edit_message_text(
            "❌ You are already registered!\n\n"
            "Contact an admin if you need to update your profile.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Main Menu", callback_data="main_menu")
            ]])
        )
        context.user_data['expecting_search'] = True  # Re-enable search mode
        return ConversationHandler.END
    
    # Get or create category
    category_name = reg.get('category_name', '').title()
    category = await get_or_create_category(category_name)
    
    # Create provider
    from bot.models import ServiceProvider
    provider = ServiceProvider(
        telegram_user_id=user_id,
        name=reg.get('name'),
        description=reg.get('description'),
        keywords=reg.get('keywords', []),
        category=category,
        plan_type=reg.get('plan_type', 'BASIC'),
        phone=reg.get('phone', ''),
        telegram_handle=reg.get('telegram_handle', ''),
        instagram_handle=reg.get('instagram_handle', ''),
        hall_of_residence=reg.get('hall_of_residence', ''),
        is_approved=False,  # Requires admin approval
    )
    
    # Download and save catalogue if provided
    if reg.get('catalogue_file_id'):
        try:
            file = await context.bot.get_file(reg['catalogue_file_id'])
            catalogue_dir = os.path.join(settings.MEDIA_ROOT, 'catalogues')
            os.makedirs(catalogue_dir, exist_ok=True)
            
            filename = f"{user_id}_{reg.get('catalogue_name', 'catalogue.pdf')}"
            filepath = os.path.join(catalogue_dir, filename)
            
            await file.download_to_drive(filepath)
            provider.catalogue = f"catalogues/{filename}"
        except Exception as e:
            print(f"Error saving catalogue: {e}")
    
    await save_provider(provider)
    
    plan_prices = {'BASIC': '₦1,500', 'VERIFIED': '₦3,000', 'PREMIUM': '₦5,000'}
    
    await query.edit_message_text(
        "✅ *REGISTRATION SUBMITTED!*\n\n"
        f"Your {reg.get('plan_type')} registration has been received.\n\n"
        f"💰 *Amount to pay:* {plan_prices.get(reg.get('plan_type'))}\n\n"
        "📱 *Payment Instructions:*\n"
        "Please contact the admin to complete payment and activation.\n\n"
        "_Your profile will be visible once approved._",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Main Menu", callback_data="main_menu")
        ]])
    )
    
    # Clear registration data and re-enable search
    context.user_data['registration'] = {}
    context.user_data['expecting_search'] = True
    
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['registration'] = {}
    context.user_data['expecting_search'] = True  # Re-enable search mode
    
    await query.edit_message_text(
        "❌ Registration cancelled.\n\n"
        "You can start again anytime!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("« Main Menu", callback_data="main_menu")
        ]])
    )
    
    return ConversationHandler.END


def get_registration_handler():
    """Return the registration conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_registration, pattern="^register_start$"),
        ],
        states={
            WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name),
            ],
            WAITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description),
            ],
            WAITING_KEYWORDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_keywords),
            ],
            WAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone),
                CallbackQueryHandler(skip_phone, pattern="^skip_phone$"),
            ],
            WAITING_TELEGRAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_telegram),
                CallbackQueryHandler(skip_telegram, pattern="^skip_telegram$"),
            ],
            WAITING_INSTAGRAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_instagram),
                CallbackQueryHandler(skip_instagram, pattern="^skip_instagram$"),
            ],
            WAITING_CATALOGUE: [
                MessageHandler(filters.Document.PDF, receive_catalogue),
                CallbackQueryHandler(skip_catalogue, pattern="^skip_catalogue$"),
            ],
            WAITING_PLAN: [
                CallbackQueryHandler(receive_plan, pattern="^plan_(BASIC|VERIFIED|PREMIUM)$"),
            ],
            WAITING_HALL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_hall),
                CallbackQueryHandler(skip_hall, pattern="^skip_hall$"),
            ],
            CONFIRM_REGISTRATION: [
                CallbackQueryHandler(complete_registration, pattern="^confirm_registration$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$"),
        ],
        allow_reentry=True,
        per_message=False,
    )
