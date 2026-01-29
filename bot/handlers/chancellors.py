"""
Chancellors section handler - Sports, fixtures, results, leaderboard
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from django.utils import timezone
from asgiref.sync import sync_to_async


async def chancellors_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Chancellors section - sports hub."""
    query = update.callback_query
    await query.answer()
    
    text = """⚽ *CHANCELLORS*
_Sports & Entertainment Hub_

Choose what you'd like to see:"""
    
    keyboard = [
        [
            InlineKeyboardButton("📅 Fixtures", callback_data="chancellors_fixtures"),
            InlineKeyboardButton("🏆 Results", callback_data="chancellors_results"),
        ],
        [
            InlineKeyboardButton("📊 Fantasy Leaderboard", callback_data="chancellors_leaderboard"),
        ],
        [
            InlineKeyboardButton("📢 Announcements", callback_data="chancellors_announcements"),
        ],
        [
            InlineKeyboardButton("« Back to Menu", callback_data="main_menu"),
        ],
    ]
    
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


async def show_fixtures(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display upcoming fixtures."""
    from bot.models import Fixture
    
    query = update.callback_query
    await query.answer()
    
    @sync_to_async
    def get_fixtures():
        now = timezone.now()
        return list(Fixture.objects.filter(match_date__gte=now).order_by('match_date')[:10])
    
    fixtures = await get_fixtures()
    
    if not fixtures:
        text = "📅 *FIXTURES*\n\nNo upcoming fixtures at the moment."
    else:
        text = "📅 *UPCOMING FIXTURES*\n\n"
        
        for fixture in fixtures:
            text += f"⚽ *{fixture.home_team}* vs *{fixture.away_team}*\n"
            text += f"📆 {fixture.match_date.strftime('%b %d, %Y at %H:%M')}\n"
            if fixture.venue:
                text += f"📍 {fixture.venue}\n"
            if fixture.competition:
                text += f"🏆 {fixture.competition}\n"
            text += "\n"
    
    keyboard = [
        [InlineKeyboardButton("« Back to Chancellors", callback_data="section_chancellors")],
        [InlineKeyboardButton("« Main Menu", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display recent match results."""
    from bot.models import Result
    
    query = update.callback_query
    await query.answer()
    
    @sync_to_async
    def get_results():
        return list(Result.objects.select_related('fixture').order_by('-created_at')[:10])
    
    results = await get_results()
    
    if not results:
        text = "🏆 *RESULTS*\n\nNo results available yet."
    else:
        text = "🏆 *RECENT RESULTS*\n\n"
        
        for result in results:
            fixture = result.fixture
            text += f"⚽ *{fixture.home_team}* {result.home_score} - {result.away_score} *{fixture.away_team}*\n"
            text += f"📆 {fixture.match_date.strftime('%b %d, %Y')}\n"
            if result.summary:
                summary = result.summary[:100] + "..." if len(result.summary) > 100 else result.summary
                text += f"📝 {summary}\n"
            text += "\n"
    
    keyboard = [
        [InlineKeyboardButton("« Back to Chancellors", callback_data="section_chancellors")],
        [InlineKeyboardButton("« Main Menu", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display fantasy leaderboard."""
    from bot.models import FantasyLeaderboard
    
    query = update.callback_query
    await query.answer()
    
    @sync_to_async
    def get_leaders():
        return list(FantasyLeaderboard.objects.order_by('rank')[:20])
    
    leaders = await get_leaders()
    
    if not leaders:
        text = "📊 *FANTASY LEADERBOARD*\n\nNo leaderboard data available yet."
    else:
        text = "📊 *FANTASY LEADERBOARD*\n\n"
        
        for leader in leaders:
            # Medals for top 3
            if leader.rank == 1:
                medal = "🥇"
            elif leader.rank == 2:
                medal = "🥈"
            elif leader.rank == 3:
                medal = "🥉"
            else:
                medal = f"#{leader.rank}"
            
            text += f"{medal} *{leader.player_name}* - {leader.points} pts\n"
    
    keyboard = [
        [InlineKeyboardButton("« Back to Chancellors", callback_data="section_chancellors")],
        [InlineKeyboardButton("« Main Menu", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_announcements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display Chancellors announcements."""
    from bot.models import Announcement
    
    query = update.callback_query
    await query.answer()
    
    @sync_to_async
    def get_announcements():
        return list(Announcement.objects.all()[:10])
    
    announcements = await get_announcements()
    
    if not announcements:
        text = "📢 *ANNOUNCEMENTS*\n\nNo announcements at the moment."
    else:
        text = "📢 *ANNOUNCEMENTS*\n\n"
        
        for ann in announcements:
            pin = "📌 " if ann.is_pinned else ""
            content = ann.content[:200] + "..." if len(ann.content) > 200 else ann.content
            text += f"{pin}*{ann.title}*\n"
            text += f"{content}\n"
            text += f"_{ann.created_at.strftime('%b %d, %Y')}_\n\n"
    
    keyboard = [
        [InlineKeyboardButton("« Back to Chancellors", callback_data="section_chancellors")],
        [InlineKeyboardButton("« Main Menu", callback_data="main_menu")],
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def get_chancellors_handlers():
    """Return handlers for Chancellors section."""
    return [
        CallbackQueryHandler(chancellors_section, pattern="^section_chancellors$"),
        CallbackQueryHandler(show_fixtures, pattern="^chancellors_fixtures$"),
        CallbackQueryHandler(show_results, pattern="^chancellors_results$"),
        CallbackQueryHandler(show_leaderboard, pattern="^chancellors_leaderboard$"),
        CallbackQueryHandler(show_announcements, pattern="^chancellors_announcements$"),
    ]
