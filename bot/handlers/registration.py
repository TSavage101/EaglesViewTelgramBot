"""
Registration handler - Service provider registration flow with Paystack payment
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, MessageHandler, 
    filters, ConversationHandler
)
from asgiref.sync import sync_to_async
from django.conf import settings as django_settings


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
    WAITING_EMAIL,
    WAITING_PAYMENT,
    CONFIRM_REGISTRATION,
) = range(13)


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
    
    # If premium, ask for hall of residence first
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
    
    # For Basic and Verified, skip to email collection
    return await ask_email(update, context, from_callback=True)


async def receive_hall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive hall of residence."""
    hall = update.message.text.strip()
    context.user_data['registration']['hall_of_residence'] = hall
    
    return await ask_email(update, context, from_callback=False)


async def skip_hall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip hall of residence."""
    query = update.callback_query
    await query.answer()
    
    context.user_data['registration']['hall_of_residence'] = ''
    
    return await ask_email(update, context, from_callback=True)


async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = True) -> int:
    """Ask the user for their email address (required by Paystack)."""
    text = (
        "📧 *EMAIL ADDRESS*\n\n"
        "Please enter your *email address*.\n"
        "This is needed for payment processing.\n\n"
        "_Example: yourname@gmail.com_"
    )
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
    ]])
    
    if from_callback:
        query = update.callback_query
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    return WAITING_EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive email and show confirmation summary before payment."""
    email = update.message.text.strip().lower()
    
    # Basic email validation
    if '@' not in email or '.' not in email.split('@')[-1]:
        await update.message.reply_text(
            "❌ That doesn't look like a valid email.\nPlease try again:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")
            ]])
        )
        return WAITING_EMAIL
    
    context.user_data['registration']['email'] = email
    
    # Show confirmation summary
    return await show_confirmation_message(update, context)


async def show_confirmation_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show registration confirmation summary before payment."""
    reg = context.user_data.get('registration', {})
    
    plan_prices = {'BASIC': '₦1,500', 'VERIFIED': '₦3,000', 'PREMIUM': '₦5,000'}
    
    def escape_md(text):
        """Escape Markdown special characters in user input."""
        if not text:
            return text
        for char in ['_', '*', '`', '[']:
            text = text.replace(char, f'\\{char}')
        return text
    
    name = escape_md(reg.get('name', ''))
    desc = escape_md(reg.get('description', '')[:100])
    keywords = escape_md(', '.join(reg.get('keywords', [])))
    category = escape_md(reg.get('category_name', ''))
    phone = escape_md(reg.get('phone')) or 'Not provided'
    tg_handle = escape_md(reg.get('telegram_handle')) or 'Not provided'
    ig_handle = escape_md(reg.get('instagram_handle')) or 'Not provided'
    email = escape_md(reg.get('email', ''))
    hall = escape_md(reg.get('hall_of_residence', ''))
    
    text = "📋 *REGISTRATION SUMMARY*\n\n"
    text += f"Name: {name}\n"
    text += f"Description: {desc}\n"
    text += f"Keywords: {keywords}\n"
    text += f"Category: {category}\n"
    text += f"Phone: {phone}\n"
    text += f"Telegram: {tg_handle}\n"
    text += f"Instagram: {ig_handle}\n"
    text += f"Email: {email}\n"
    text += f"Catalogue: {'✅ Uploaded' if reg.get('catalogue_file_id') else '❌ Not uploaded'}\n"
    text += f"Plan: {reg.get('plan_type')} - {plan_prices.get(reg.get('plan_type'), '?')}\n"
    
    if hall:
        text += f"Hall: {hall}\n"
    
    text += f"\n💰 *Total: {plan_prices.get(reg.get('plan_type'), '?')}*\n"
    text += "\nClick Confirm to proceed to payment."
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm & Pay", callback_data="confirm_registration")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")],
        ])
    )
    
    return CONFIRM_REGISTRATION


async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the provider to DB and generate Paystack payment link."""
    query = update.callback_query
    await query.answer("Processing...")
    
    reg = context.user_data.get('registration', {})
    user_id = query.from_user.id
    
    from bot.models import ServiceProvider, Category, Payment
    from bot.services.paystack import initialize_payment, generate_reference
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
    
    @sync_to_async
    def create_payment(provider, reference, amount, plan, auth_url):
        payment = Payment.objects.create(
            provider=provider,
            reference=reference,
            amount=amount,
            plan_type=plan,
            authorization_url=auth_url,
        )
        return payment
    
    @sync_to_async
    def init_payment(email, amount, ref, metadata):
        return initialize_payment(email, amount, ref, metadata)
    
    @sync_to_async
    def gen_ref():
        return generate_reference()
    
    # Check if already registered
    if await check_existing(user_id):
        await query.edit_message_text(
            "❌ You are already registered!\n\n"
            "Contact an admin if you need to update your profile.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Main Menu", callback_data="main_menu")
            ]])
        )
        context.user_data['expecting_search'] = True
        return ConversationHandler.END
    
    # Get or create category
    category_name = reg.get('category_name', '').title()
    category = await get_or_create_category(category_name)
    
    # Create provider (not approved yet)
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
        is_approved=False,
    )
    
    # Download and save catalogue if provided
    if reg.get('catalogue_file_id'):
        try:
            file = await context.bot.get_file(reg['catalogue_file_id'])
            catalogue_dir = os.path.join(django_settings.MEDIA_ROOT, 'catalogues')
            os.makedirs(catalogue_dir, exist_ok=True)
            
            filename = f"{user_id}_{reg.get('catalogue_name', 'catalogue.pdf')}"
            filepath = os.path.join(catalogue_dir, filename)
            
            await file.download_to_drive(filepath)
            provider.catalogue = f"catalogues/{filename}"
        except Exception as e:
            print(f"Error saving catalogue: {e}")
    
    await save_provider(provider)
    
    # --- PAYSTACK PAYMENT ---
    plan = reg.get('plan_type', 'BASIC')
    amount_kobo = django_settings.PLAN_PRICES.get(plan, 150000)
    reference = await gen_ref()
    email = reg.get('email', f'{user_id}@eaglesview.bot')
    
    # Initialize Paystack transaction
    result = await init_payment(
        email=email,
        amount=amount_kobo,
        ref=reference,
        metadata={
            "provider_id": provider.id,
            "provider_name": provider.name,
            "plan_type": plan,
            "telegram_user_id": user_id,
        }
    )
    
    if result.get('success'):
        auth_url = result['authorization_url']
        
        # Save payment record
        await create_payment(provider, reference, amount_kobo, plan, auth_url)
        
        # Store reference for verification
        context.user_data['payment_reference'] = reference
        
        plan_prices = {'BASIC': '₦1,500', 'VERIFIED': '₦3,000', 'PREMIUM': '₦5,000'}
        
        await query.edit_message_text(
            f"✅ *REGISTRATION SAVED!*\n\n"
            f"💰 *Plan:* {plan} - {plan_prices.get(plan)}\n"
            f"📧 *Ref:* `{reference}`\n\n"
            f"👉 *Click the button below to pay:*\n\n"
            f"After payment, click *'✅ I've Paid'* to verify.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Pay Now", url=auth_url)],
                [InlineKeyboardButton("✅ I've Paid - Verify", callback_data=f"verify_payment_{reference}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_registration")],
            ])
        )
        
        # Clear registration data, re-enable search
        context.user_data['registration'] = {}
        context.user_data['expecting_search'] = True
        
        return ConversationHandler.END
    
    else:
        # Payment initialization failed — save provider anyway
        error_msg = result.get('error', 'Unknown error')
        print(f"Paystack error: {error_msg}")
        
        await query.edit_message_text(
            "⚠️ *REGISTRATION SAVED* but payment link could not be generated.\n\n"
            f"Error: _{error_msg}_\n\n"
            "Please contact the admin to arrange payment manually.\n"
            "Your profile will be activated once payment is confirmed.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Main Menu", callback_data="main_menu")
            ]])
        )
        
        context.user_data['registration'] = {}
        context.user_data['expecting_search'] = True
        
        return ConversationHandler.END


async def verify_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify payment via Paystack API when user clicks 'I've Paid'."""
    query = update.callback_query
    await query.answer("Verifying payment...")
    
    reference = query.data.replace("verify_payment_", "")
    
    from bot.models import Payment
    from bot.services.paystack import verify_payment
    from django.utils import timezone
    
    @sync_to_async
    def do_verify(ref):
        return verify_payment(ref)
    
    @sync_to_async
    def get_payment(ref):
        try:
            return Payment.objects.select_related('provider').get(reference=ref)
        except Payment.DoesNotExist:
            return None
    
    @sync_to_async
    def update_payment_success(payment, paystack_data):
        payment.status = 'SUCCESS'
        payment.paystack_response = paystack_data
        payment.verified_at = timezone.now()
        payment.save()
        # Also mark provider as paid (but still needs admin approval)
        provider = payment.provider
        provider.save()
    
    @sync_to_async
    def update_payment_failed(payment, paystack_data):
        payment.status = 'FAILED'
        payment.paystack_response = paystack_data
        payment.save()
    
    # Get payment record
    payment = await get_payment(reference)
    
    if not payment:
        await query.edit_message_text(
            "❌ Payment record not found.\nPlease contact admin.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Main Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Already verified?
    if payment.status == 'SUCCESS':
        await query.edit_message_text(
            "✅ *Payment already verified!*\n\n"
            "Your profile is pending admin approval.\n"
            "You'll be visible in search once approved! 🎉",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Main Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Verify with Paystack
    result = await do_verify(reference)
    
    if result.get('success') and result.get('status') == 'success':
        # Payment confirmed!
        await update_payment_success(payment, result.get('data'))
        
        await query.edit_message_text(
            "✅ *PAYMENT VERIFIED!* 🎉\n\n"
            f"💰 Amount: ₦{payment.amount_naira:,.0f}\n"
            f"📧 Ref: `{reference}`\n\n"
            "Your profile is now *pending admin approval*.\n"
            "Once approved, you'll appear in Purple Board search!\n\n"
            "_Thank you for choosing Eagles View!_ 🦅",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Main Menu", callback_data="main_menu")
            ]])
        )
    
    elif result.get('success') and result.get('status') in ('abandoned', 'failed'):
        await update_payment_failed(payment, result.get('data'))
        
        # Regenerate payment link
        auth_url = payment.authorization_url
        
        await query.edit_message_text(
            "❌ *Payment not completed yet.*\n\n"
            "It seems the payment was not successful or was abandoned.\n"
            "Please try again:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Try Again", url=auth_url)],
                [InlineKeyboardButton("✅ I've Paid - Verify", callback_data=f"verify_payment_{reference}")],
                [InlineKeyboardButton("« Main Menu", callback_data="main_menu")],
            ])
        )
    
    else:
        # Payment still pending or error
        auth_url = payment.authorization_url
        
        await query.edit_message_text(
            "⏳ *Payment still pending...*\n\n"
            "We couldn't confirm your payment yet.\n"
            "If you haven't paid, click 'Pay Now'.\n"
            "If you just paid, wait a moment and try verifying again.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Pay Now", url=auth_url)],
                [InlineKeyboardButton("✅ Verify Again", callback_data=f"verify_payment_{reference}")],
                [InlineKeyboardButton("« Main Menu", callback_data="main_menu")],
            ])
        )


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
            WAITING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email),
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


def get_payment_verification_handler():
    """Return the handler for verifying payments (outside conversation)."""
    return CallbackQueryHandler(verify_payment_handler, pattern=r"^verify_payment_")
